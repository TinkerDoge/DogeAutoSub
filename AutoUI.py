"""
DogeAutoSub — Automatic Subtitle Generation Application
========================================================
Clean, modern desktop app using PySide6 + faster-whisper.

Pipeline:  Select Video → Extract Audio → Transcribe → Translate → Save SRT
"""

import os
import sys

# ── Ensure updatable modules load from disk, not PYZ archive ────
# PyInstaller compiles modules into a PYZ archive. To allow the
# auto-updater to replace .py files on disk and have them take
# effect, we must ensure _internal/ is searched FIRST.
if getattr(sys, 'frozen', False):
    _internal = os.path.join(os.path.dirname(sys.executable), '_internal')
    if os.path.isdir(_internal) and _internal not in sys.path:
        sys.path.insert(0, _internal)
    # Invalidate any cached module finders so Python re-scans
    import importlib
    importlib.invalidate_caches()

import re
import subprocess
import time

from PySide6.QtWidgets import (
    QApplication, QFileDialog, QMainWindow, QMessageBox,
)
from PySide6.QtGui import QMovie, QPixmap, QDesktopServices, QIcon
from PySide6.QtCore import QThread, QUrl, Qt, Signal

from modules import ui_DogeAutoSub
from modules.constants import MODEL_INFO, LANGUAGE_CODES_AI, MODEL_TYPES, TRANSLATION_ENGINES, TRANSLATION_ENGINES_SUBTITLE_ONLY
from modules.subtitle_args import SubtitleArgs
from modules.mlaas_client import (
    MLAASConfig, fetch_mlaas_model_list, translate_segments_mlaas,
    summarize_text_mlaas, get_masked_key, get_api_key,
    load_cached_mlaas_model_list_from_disk, save_bearer_token,
)
from modules.updater import APP_VERSION, check_for_update, download_and_apply_update, restart_app

from modules.subtitle_thread import SubtitleThread, ThroughputTracker, _lang_code
from modules.meeting_notes_thread import MeetingNotesThread
from modules.translate_thread import TranslateFileThread

# ── CUDA Setup ──────────────────────────────────────────────────
cuda_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules', 'CUDA')
if os.path.isdir(cuda_path):
    os.environ['CUDA_PATH'] = cuda_path
    os.environ['PATH'] = os.path.join(cuda_path, 'bin') + os.pathsep + os.environ['PATH']
    os.environ['CUDA_HOME'] = cuda_path

# ── Paths ───────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = os.path.join(SCRIPT_DIR, "modules", "ffmpeg", "bin", "ffmpeg.exe")
TEMP_DIR = os.path.join(SCRIPT_DIR, "modules", "temp")

# ── Try importing optional translation engines ──────────────────
try:
    from deep_translator import GoogleTranslator
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False
    print("Google Translate not available (install deep-translator)")



try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# MAIN WINDOW CLASS
# ═══════════════════════════════════════════════════════════════





class DogeAutoSub(ui_DogeAutoSub.Ui_MainWindow, QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.input_file_path = None
        self.output_folder_path = None
        self.docx_path = None
        self.trans_file_path = None
        self.subtitle_thread = None
        self.notes_thread = None
        self.translate_thread = None
        self.current_theme = "Dark"

        # ── Set window icon ─────────────────────────────────────
        icon_path = os.path.join(SCRIPT_DIR, "icons", "favicon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Also show icon in custom title bar
        if os.path.exists(icon_path) and hasattr(self, "titleBarIcon"):
            from PySide6.QtGui import QPixmap
            pm = QPixmap(icon_path).scaled(
                16, 16,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.titleBarIcon.setPixmap(pm)

        # ── Palette ─────────────────────────────────────────────────────
        from modules.theme_tokens import build_stylesheet, DEFAULT_PALETTE
        from PySide6.QtCore import QSettings
        _settings = QSettings("DogeAutoSub", "ui")
        # One-shot migration: drop old theme/dark key
        if _settings.contains("theme/dark"):
            _settings.remove("theme/dark")
        _palette_id = _settings.value("theme/palette", DEFAULT_PALETTE, type=str)
        QApplication.instance().setStyleSheet(build_stylesheet(_palette_id))
        self.paletteStripe.set_palette(_palette_id)
        self.paletteMenuButton.select(_palette_id)
        self.phaseStrip.set_accent_color(self._accent_for(_palette_id))
        self.paletteMenuButton.palette_selected.connect(self._on_palette_changed)

        # ── Frameless window controls ───────────────────────────────────
        self.closeBtn.clicked.connect(self.close)
        self.minBtn.clicked.connect(self.showMinimized)
        self.zoomBtn.clicked.connect(self._toggle_zoom)
        self._drag_origin = None
        self.fauxTitleBar.mousePressEvent = self._titlebar_press
        self.fauxTitleBar.mouseMoveEvent = self._titlebar_move
        self.fauxTitleBar.mouseReleaseEvent = self._titlebar_release

        # ── Logging ─────────────────────────────────────────────
        from modules.log_writer import LogWriter
        from modules.log_panel import LogPanel, PIPELINE_SUBTITLES, PIPELINE_NOTES, PIPELINE_TRANSLATE
        log_dir = os.path.join(SCRIPT_DIR, "logs")
        self._log_writer = LogWriter(log_dir, keep_days=7)
        self._log_writer.prune()
        self.logPanel = LogPanel(log_writer=self._log_writer)
        # Swap the logPanelHost placeholder out for the real LogPanel
        host_parent = self.logPanelHost.parentWidget()
        host_layout = host_parent.layout() if host_parent else None
        if host_layout is not None:
            idx = host_layout.indexOf(self.logPanelHost)
            host_layout.removeWidget(self.logPanelHost)
            self.logPanelHost.deleteLater()
            host_layout.insertWidget(idx, self.logPanel)
        self.logPanel.set_pipeline(PIPELINE_SUBTITLES)
        self._PIPELINES = {
            "subtitles": PIPELINE_SUBTITLES,
            "notes": PIPELINE_NOTES,
            "translate": PIPELINE_TRANSLATE,
        }

        # ── Sidebar workflow switching ──────────────────────────────────
        self._sidebar_items = {
            "subtitles": self.sidebarSubtitlesItem,
            "notes":     self.sidebarNotesItem,
            "translate": self.sidebarTranslateItem,
        }
        for name, btn in self._sidebar_items.items():
            btn.clicked.connect(lambda _checked=False, n=name: self._activate_workflow(n))
        self._activate_workflow("subtitles")

        # ── Mascot widget ───────────────────────────────────────────────
        from modules.mascot import MascotWidget
        _icons_root = os.path.join(SCRIPT_DIR, "icons")
        self.mascot = MascotWidget(self.mascotHost, icons_root=_icons_root)
        self.mascotHost.layout().insertWidget(1, self.mascot)
        self.mascot.set_idle("subtitles")

        # ── Status bar ──────────────────────────────────────────────────
        self.statusBarVersion.setText(f"v{APP_VERSION}")
        try:
            if TORCH_AVAILABLE and torch.cuda.is_available():
                self.statusBarGpu.setText(f"GPU: {torch.cuda.get_device_name(0)}")
            else:
                self.statusBarGpu.setText("GPU: CPU only")
        except Exception:
            self.statusBarGpu.setText("GPU: —")
        self.statusBarReady.setText("● Ready")

        # ── Card hover lift ───────────────────────────────────────
        from modules.animations import lift_on_hover
        for _card_name in ("fileCard", "settingsCard", "actionCard", "mascotCard",
                           "notesFileCard", "notesOutputCard",
                           "transFileCard", "transSettingsCard", "transOutputCard"):
            _w = getattr(self, _card_name, None)
            if _w:
                lift_on_hover(_w, dy=2, duration_ms=120)

        # ── Legacy animation refs (kept for backward compat) ─────
        self.loading_movie = None
        self.standby_movie = None
        self.done_pixmap = None
        loading_gif = os.path.join(SCRIPT_DIR, "icons", "loading.gif")
        start_gif = os.path.join(SCRIPT_DIR, "icons", "start.gif")
        done_img = os.path.join(SCRIPT_DIR, "icons", "done.jpg")
        
        # ── Load MLAAS API key from .env ─────────────────────
        self.mlaas_config = MLAASConfig.from_env()

        # ── Populate dropdowns ──────────────────────────────────
        self._setup_model_dropdown()
        self._setup_language_dropdowns()
        # Load cached model list from disk (instant). Background refresh runs after window shows.
        load_cached_mlaas_model_list_from_disk()
        self._setup_translation_engines()
        
        # ── Connect signals ─────────────────────────────────────
        self.selectFileBtn.clicked.connect(self._select_input_file)
        self.selectOutputBtn.clicked.connect(self._select_output_folder)
        self.startButton.clicked.connect(self._start_subtitles)
        self.model_size_dropdown.currentTextChanged.connect(self._on_model_changed)
        self.themeBtn.clicked.connect(self._toggle_theme)
        self.openFolderBtn.clicked.connect(self._open_output_folder)
        
        # Meeting notes signals
        if hasattr(self, "selectDocxBtn"):
            self.selectDocxBtn.clicked.connect(self._select_docx)
        self.generateNotesBtn.clicked.connect(self._generate_meeting_notes)
        self.saveNotesBtn.clicked.connect(self._save_meeting_notes)

        # Translation tab signals
        if hasattr(self, "selectTransFileBtn"):
            self.selectTransFileBtn.clicked.connect(self._select_trans_file)
        self.translateFileBtn.clicked.connect(self._start_file_translation)
        if hasattr(self, "saveTransBtn"):
            self.saveTransBtn.clicked.connect(self._save_translation)

        # Bearer token UI signals
        self.getTokenBtn.clicked.connect(self._open_token_page)
        self.bearerTokenEdit.textChanged.connect(self._on_bearer_token_changed)

        # Restore persisted bearer token into the text field
        if self.mlaas_config.bearer_token:
            self.bearerTokenEdit.setText(self.mlaas_config.bearer_token)

        self._update_mlaas_status_label()
        
        # ── Set window title with version ───────────────────
        self.setWindowTitle(f"DogeAutoSub v{APP_VERSION}")
        if hasattr(self, "versionLabel"):
            self.versionLabel.setText(f"v{APP_VERSION}")
        
        # ── View menu ─────────────────────────────────────────────
        self._setup_view_menu()
        from PySide6.QtCore import QSettings as _QS
        _tips = _QS("DogeAutoSub", "ui").value("doge/tips_enabled", True, type=bool)
        try:
            self.logPanel._narrator.enabled = _tips
        except Exception:
            pass

        # ── Check for updates + refresh model list (non-blocking) ─
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, self._check_for_updates)
        QTimer.singleShot(500, self._refresh_models_async)

        print(f"DogeAutoSub v{APP_VERSION} initialized successfully")
    
    # ── Dropdown Setup ──────────────────────────────────────────
    
    def _setup_model_dropdown(self):
        self.model_size_dropdown.clear()
        for model in MODEL_TYPES:
            self.model_size_dropdown.addItem(model)
        self.model_size_dropdown.setCurrentText("turbo")
        self._on_model_changed("turbo")
    
    def _setup_language_dropdowns(self):
        self.source_language_dropdown.clear()
        self.target_language_dropdown.clear()
        self.source_language_dropdown.addItem("Auto")
        for code, name in LANGUAGE_CODES_AI:
            if code != "auto":
                self.source_language_dropdown.addItem(name)
                self.target_language_dropdown.addItem(name)
        self.source_language_dropdown.setCurrentText("Auto")
        self.target_language_dropdown.setCurrentText("English")
    
    def _setup_translation_engines(self):
        """Populate engine dropdowns with a small curated MLAAS model list."""
        from modules.mlaas_client import get_cached_mlaas_model_list
        # Build engine key → display name mapping
        self._engine_key_map = {}  # display_name → engine_key

        dynamic_engines = []
        seen_engine_keys = set()
        preferred_model_order = ["claude-sonnet-latest", "claude-opus-latest"]
        preferred_model_labels = {
            "claude-sonnet-latest": "Sonnet Latest (MLAAS)",
            "claude-opus-latest": "Opus Latest (MLAAS)",
        }
        cached_models = get_cached_mlaas_model_list()

        for model_id in preferred_model_order:
            if any((item.get("id") or "").strip() == model_id for item in cached_models):
                dynamic_engines.append((model_id, preferred_model_labels[model_id]))
                seen_engine_keys.add(model_id)

        for model in cached_models:
            model_id = (model.get("id") or "").strip()
            if not model_id or model_id in seen_engine_keys:
                continue
            if not model_id.startswith("gpt-"):
                continue

            gpt_parts = model_id.split("-")
            gpt_label = " ".join(
                [gpt_parts[0].upper()] + [part.capitalize() if part.isalpha() else part for part in gpt_parts[1:]]
            )
            label = f"{gpt_label} (MLAAS)"
            dynamic_engines.append((model_id, label))
            seen_engine_keys.add(model_id)

        # Subtitles tab engine (includes whisper)
        self.target_engine.clear()
        all_subtitle_engines = list(dynamic_engines)
        for key, display in TRANSLATION_ENGINES:
            if key not in seen_engine_keys:
                all_subtitle_engines.append((key, display))
        all_subtitle_engines.extend(TRANSLATION_ENGINES_SUBTITLE_ONLY)
        for key, display in all_subtitle_engines:
            self.target_engine.addItem(display)
            self._engine_key_map[display] = key
        self.target_engine.setCurrentIndex(0)

        # Translation tab dropdowns — reuse same languages
        if hasattr(self, "trans_src_lang") and hasattr(self, "trans_tgt_lang"):
            self.trans_src_lang.clear()
            self.trans_tgt_lang.clear()
            self.trans_src_lang.addItem("Auto")
            for code, name in LANGUAGE_CODES_AI:
                if code != "auto":
                    self.trans_src_lang.addItem(name)
                    self.trans_tgt_lang.addItem(name)
            self.trans_src_lang.setCurrentText("Auto")
            self.trans_tgt_lang.setCurrentText("Vietnamese")

        # Translation tab engine (no whisper)
        if hasattr(self, "trans_engine"):
            self.trans_engine.clear()
            engines = list(dynamic_engines)
            for key, display in TRANSLATION_ENGINES:
                if key not in seen_engine_keys:
                    engines.append((key, display))
            for key, display in engines:
                self.trans_engine.addItem(display)
                self._engine_key_map[display] = key
            self.trans_engine.setCurrentIndex(0)
    
    def _get_engine_key(self, display_name: str) -> str:
        """Convert engine display name back to engine key."""
        return self._engine_key_map.get(display_name, display_name)
    
    # ── File Selection ──────────────────────────────────────────
    
    def _select_input_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Media Files (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv *.m4a *.mp3 *.wav *.flac)"
        )
        if path:
            self.input_file_path = path
            self.selectFileBtn.setText(f"🎬  {os.path.basename(path)}")
            self.filePathLabel.setText(os.path.dirname(path))
            if not self.output_folder_path:
                self.output_folder_path = os.path.dirname(path)
            self._push_recent("subtitles", path)
    
    def _select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder_path = folder
            self.selectOutputBtn.setText(f"📁  {os.path.basename(folder)}")
    
    def _open_output_folder(self):
        folder = self.output_folder_path
        if not folder and self.input_file_path:
            folder = os.path.dirname(self.input_file_path)
        if folder and os.path.exists(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
    
    # ── Model Info ──────────────────────────────────────────────
    
    def _on_model_changed(self, model_size: str):
        info = MODEL_INFO.get(model_size, {})
        self.VRamUsage.setText(info.get("vram", "—"))
        self.rSpeed.setText(info.get("speed", "—"))
    
    # ── Subtitle Processing ─────────────────────────────────────
    
    def _start_subtitles(self):
        if not self.input_file_path:
            QMessageBox.warning(self, "No File", "Please select a video file first.")
            return
        
        if self.subtitle_thread and self.subtitle_thread.isRunning():
            return
        
        args = SubtitleArgs(
            source_path=self.input_file_path,
            output_folder=self.output_folder_path or os.path.dirname(self.input_file_path),
            src_language=self.source_language_dropdown.currentText(),
            dst_language=self.target_language_dropdown.currentText(),
            model_size=self.model_size_dropdown.currentText(),
            translate_engine=self._get_engine_key(self.target_engine.currentText()),
            volume=self.boostSlider.value(),
        )

        if args.translate_engine not in ("google", "whisper") and not self.mlaas_config.is_configured():
            QMessageBox.warning(self, "No API Key", "MLAAS API key not found. Add MLAAS_API to your .env file.")
            return
        
        self.subtitle_thread = SubtitleThread(args)
        self.subtitle_thread.task_start.connect(self._on_task_start)
        self.subtitle_thread.task_complete.connect(self._on_task_complete)
        self.subtitle_thread.status_update.connect(self.statusLabel.setText)
        self.logPanel.set_pipeline(self._PIPELINES["subtitles"])
        self.logPanel.clear()
        self.subtitle_thread.log_event.connect(self._on_log_event)

        # ── EtaTracker + PhaseStrip ─────────────────────────────────────
        from modules.eta_tracker import EtaTracker
        self._eta = EtaTracker(workflow="subtitles")
        SUBTITLE_PHASES = ["Preparing", "Reading video", "Transcribing", "Translating", "Saving"]
        self.phaseStrip.set_phases(SUBTITLE_PHASES)
        self._eng_to_phase = {
            "Load model":    "Preparing",
            "Extract audio": "Reading video",
            "Transcribe":    "Transcribing",
            "Translate":     "Translating",
            "Save SRT":      "Saving",
        }
        self.subtitle_thread.log_event.connect(self._on_log_event_for_eta)
        self.subtitle_thread.log_event.connect(self._forward_to_log_panel)
        self.subtitle_thread.progress_update.connect(self._on_progress_update_for_eta)
        self.subtitle_thread.duration_update.connect(lambda _msg: None)

        self.subtitle_thread.start()
    
    def _on_task_start(self):
        self.startButton.setEnabled(False)
        self.startButton.setText("⏳  Processing…")
        self.statusLabel.setText("Starting…")
        self.progressBar.setValue(0)
        if self.loading_movie:
            self.statusImage.setMovie(self.loading_movie)
            self.loading_movie.start()
        try:
            from modules.animations import shimmer
            self._shimmer_anim = shimmer(self.progressBar)
        except Exception:
            self._shimmer_anim = None
    
    def _on_task_complete(self):
        self.startButton.setEnabled(True)
        self.startButton.setText("▶  START PROCESSING")
        self.progressBar.setValue(100)
        if self.loading_movie:
            self.loading_movie.stop()
        if self.done_pixmap:
            self.statusImage.setPixmap(self.done_pixmap)
        try:
            if getattr(self, "_shimmer_anim", None):
                self._shimmer_anim.stop()
                self.progressBar.setStyleSheet("")
                self._shimmer_anim = None
        except Exception:
            pass
        self.logPanel.notify_completion()
        try:
            self.statusImage.set_state("celebrate")
        except Exception:
            pass
        try:
            from modules.animations import confetti_burst
            confetti_burst(self.actionCard)
            original = self.actionCard.styleSheet()
            self.actionCard.setStyleSheet(
                original + " QFrame { border: 2px solid #7ed957; background: #f4fff0; }"
            )
            from PySide6.QtCore import QTimer as _QT
            _QT.singleShot(400, lambda: self.actionCard.setStyleSheet(original))
        except Exception:
            pass
        try:
            from modules.toast import success_with_doge
            _base = os.path.basename(self.input_file_path or "")
            _toast = success_with_doge(self, "Done", filename=_base)
            _toast.show_toast()
        except Exception:
            pass

    def _on_log_event(self, evt: dict):
        kind = evt.get("kind")
        if kind == "step_start":
            self.logPanel.step_start(evt["step"])
        elif kind == "step_done":
            self.logPanel.step_done(evt["step"], evt.get("detail", ""))
        elif kind == "step_error":
            self.logPanel.step_error(evt["step"], evt.get("detail", ""))
        elif kind == "log":
            self.logPanel.log(evt.get("level", "info"), evt.get("text", ""))
        # Forward to mascot
        try:
            self.statusImage.handle_log_event(evt)
        except Exception:
            pass
        # Doge says things from log events
        if kind == "log" and evt.get("level") == "doge":
            try:
                self.statusImage.say(evt.get("text", ""))
            except Exception:
                pass
        # Error feedback: shake window + toast
        is_error = (kind == "step_error") or (kind == "log" and evt.get("level") == "error")
        if is_error:
            try:
                from modules.animations import shake
                from modules.toast import Toast
                shake(self, amplitude=8, cycles=3, duration_ms=220)
                msg = evt.get("text") or evt.get("detail") or "An error occurred"
                Toast(self, msg, kind="error", duration_ms=4000).show_toast()
            except Exception:
                pass

    def _forward_to_log_panel(self, evt: dict):
        kind = evt.get("kind")
        if kind == "log":
            self.logPanel.log(evt.get("level", "info"), evt.get("text", ""))
        elif kind == "step_start":
            self.logPanel.step_start(evt.get("step", ""))
        elif kind == "step_done":
            self.logPanel.step_done(evt.get("step", ""), evt.get("detail", ""))
        elif kind == "step_error":
            self.logPanel.step_error(evt.get("step", ""), evt.get("detail", ""))

    # ── Palette ──────────────────────────────────────────────────

    def _toggle_theme(self):
        """Legacy no-op: theme toggle replaced by palette menu."""
        pass

    @staticmethod
    def _accent_for(palette_id: str) -> str:
        from modules.theme_tokens import PALETTES
        return PALETTES[palette_id]["accent"]

    def _on_palette_changed(self, palette_id: str):
        from modules.theme_tokens import build_stylesheet
        from PySide6.QtCore import QSettings
        QApplication.instance().setStyleSheet(build_stylesheet(palette_id))
        self.paletteStripe.set_palette(palette_id)
        self.phaseStrip.set_accent_color(self._accent_for(palette_id))
        # Sync button label/icon without re-emitting the signal
        self.paletteMenuButton.blockSignals(True)
        self.paletteMenuButton.select(palette_id)
        self.paletteMenuButton.blockSignals(False)
        QSettings("DogeAutoSub", "ui").setValue("theme/palette", palette_id)

    # ── Frameless window helpers ─────────────────────────────────

    def _toggle_zoom(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _titlebar_press(self, ev):
        from PySide6.QtCore import Qt
        if ev.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            ev.accept()

    def _titlebar_move(self, ev):
        from PySide6.QtCore import Qt
        if self._drag_origin is not None and ev.buttons() & Qt.MouseButton.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag_origin)
            ev.accept()

    def _titlebar_release(self, ev):
        self._drag_origin = None

    # ── Sidebar ──────────────────────────────────────────────────

    def _activate_workflow(self, name: str):
        index = {"subtitles": 0, "notes": 1, "translate": 2}.get(name, 0)
        self.workflowStack.setCurrentIndex(index)
        for n, btn in self._sidebar_items.items():
            btn.setProperty("active", "true" if n == name else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        if hasattr(self, "mascot") and self.mascot is not None:
            self.mascot.set_idle(name)
        self._render_recents(name)

    _RECENTS_MAX = 5

    def _push_recent(self, workflow: str, path: str):
        from PySide6.QtCore import QSettings
        if not path:
            return
        s = QSettings("DogeAutoSub", "ui")
        key = f"recents/{workflow}"
        existing = s.value(key, [], type=list) or []
        items = [p for p in existing if p != path]
        items.insert(0, path)
        s.setValue(key, items[:self._RECENTS_MAX])
        self._render_recents(workflow)

    def _render_recents(self, workflow: str):
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import QPushButton
        s = QSettings("DogeAutoSub", "ui")
        items = s.value(f"recents/{workflow}", [], type=list) or []
        while self.recentListLayout.count():
            item = self.recentListLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for path in items:
            btn = QPushButton(os.path.basename(path))
            btn.setObjectName("sidebarItem")
            btn.setToolTip(path)
            btn.clicked.connect(
                lambda _checked=False, p=path, w=workflow: self._reload_recent(w, p)
            )
            self.recentListLayout.addWidget(btn)

    def _reload_recent(self, workflow: str, path: str):
        if workflow == "subtitles":
            self.input_file_path = path
            self.filePathLabel.setText(path)
        elif workflow == "notes":
            self.docx_path = path
            if hasattr(self, "docxPathLabel"):
                self.docxPathLabel.setText(path)
        elif workflow == "translate":
            self.trans_file_path = path
            if hasattr(self, "transFilePathLabel"):
                self.transFilePathLabel.setText(path)
        self._activate_workflow(workflow)

    # ── EtaTracker helpers ───────────────────────────────────────

    def _on_log_event_for_eta(self, evt: dict):
        kind = evt.get("kind")
        eng_step = evt.get("step")
        phase = self._eng_to_phase.get(eng_step) if eng_step else None
        if kind == "step_start" and phase:
            self._eta.start_phase(phase)
            self.phaseStrip.set_active(phase)
            if hasattr(self, "mascot") and self.mascot is not None:
                self.mascot.set_phase(phase)
            self._refresh_status_line()
        elif kind == "step_done" and phase:
            self._eta.complete_phase(phase)
            self.phaseStrip.mark_done(phase)
            self._refresh_status_line()
        elif kind == "step_error" and phase:
            self.phaseStrip.mark_error(phase)
            self.statusLabel.setText(f"{phase} · failed")
            self.statusLabel.setStyleSheet("color:#ff6b6b;")
            try:
                if hasattr(self, "logPanel"):
                    self.logPanel.set_filter("events")
                    if not self.logPanel._console_visible:
                        self.logPanel.toggle_console()
            except Exception:
                pass

    def _on_progress_update_for_eta(self, value: int):
        try:
            self._eta.update_position(float(value), 100.0)
        except Exception:
            pass
        self._refresh_status_line()
        try:
            self.progressBar.setValue(int(self._eta.overall_fraction() * 100))
        except Exception:
            self.progressBar.setValue(value)

    def _refresh_status_line(self):
        active = self.phaseStrip.active_phase()
        if active:
            self.statusLabel.setText(active)
            self.statusLabel.setStyleSheet("")
        self.etaLabel.setText(self._eta.current_eta_string())

    # ── Meeting Notes ───────────────────────────────────────────
    
    def _select_docx(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Meeting Transcript", "",
            "Transcript Files (*.docx *.txt *.srt *.sub *.vtt);;Word Documents (*.docx);;Text Files (*.txt);;Subtitle Files (*.srt *.sub *.vtt);;All Files (*.*)"
        )
        if path:
            self.docx_path = path
            self.selectDocxBtn.setText(f"📎  {os.path.basename(path)}")
            self.docxPathLabel.setText(path)
            self._push_recent("notes", path)
    
    def _generate_meeting_notes(self):
        if not self.docx_path:
            QMessageBox.warning(self, "No File", "Please select a transcript file first.")
            return
        
        if self.notes_thread and self.notes_thread.isRunning():
            return
        
        if not self.mlaas_config.is_configured():
            QMessageBox.warning(self, "No API Key", "MLAAS API key not found. Add MLAAS_API to your .env file.")
            return
        
        self.generateNotesBtn.setEnabled(False)
        self.generateNotesBtn.setText("⏳  Generating…")
        self.notesOutput.clear()
        
        self.notes_thread = MeetingNotesThread(self.docx_path)
        self.notes_thread.finished.connect(self._on_notes_finished)
        self.notes_thread.error.connect(self._on_notes_error)
        self.notes_thread.status_update.connect(self.notesStatusLabel.setText)
        self.logPanel.set_pipeline(self._PIPELINES["notes"])
        self.logPanel.clear()
        self.notes_thread.log_event.connect(self._on_log_event)
        self.notes_thread.start()
    
    def _on_notes_finished(self, result: str):
        self.notesOutput.setPlainText(result)
        self.notesStatusLabel.setText("Notes generated successfully ✓")
        self.generateNotesBtn.setEnabled(True)
        self.generateNotesBtn.setText("✨  Generate Meeting Notes")
    
    def _on_notes_error(self, error: str):
        self.notesOutput.setPlainText(f"Error:\n{error}")
        self.notesStatusLabel.setText("Error generating notes")
        self.generateNotesBtn.setEnabled(True)
        self.generateNotesBtn.setText("✨  Generate Meeting Notes")
        try:
            from modules.animations import shake
            from modules.toast import Toast
            shake(self, amplitude=8, cycles=3, duration_ms=220)
            Toast(self, error[:120], kind="error", duration_ms=4000).show_toast()
        except Exception:
            pass
    
    def _save_meeting_notes(self):
        text = self.notesOutput.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Empty", "No notes to save.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Meeting Notes", "",
            "Text Files (*.txt);;Markdown (*.md);;All Files (*.*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.notesStatusLabel.setText(f"Saved to {os.path.basename(path)}")
    
    # ── File Translation ────────────────────────────────────────
    
    def _select_trans_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Translate", "",
            "Supported Files (*.srt *.docx *.txt *.sub *.vtt);;All Files (*.*)"
        )
        if path:
            self.trans_file_path = path
            self.selectTransFileBtn.setText(f"📎  {os.path.basename(path)}")
            self.transFilePathLabel.setText(path)
            self._push_recent("translate", path)
    
    def _get_lang_code(self, display_name: str) -> str:
        """Convert display name back to language code."""
        if display_name == "Auto":
            return "auto"
        for code, name in LANGUAGE_CODES_AI:
            if name == display_name:
                return code
        return display_name.lower()[:2]
    
    def _start_file_translation(self):
        if not self.trans_file_path:
            QMessageBox.warning(self, "No File", "Please select a file to translate.")
            return
        
        if self.translate_thread and self.translate_thread.isRunning():
            return
        
        src = self._get_lang_code(self.trans_src_lang.currentText())
        dst = self._get_lang_code(self.trans_tgt_lang.currentText())
        engine = self._get_engine_key(self.trans_engine.currentText())
        
        if engine != "google" and not self.mlaas_config.is_configured():
            QMessageBox.warning(self, "No API Key", "MLAAS API key not found. Add MLAAS_API to your .env file.")
            return
        
        self.translateFileBtn.setEnabled(False)
        self.translateFileBtn.setText("⏳  Translating…")
        self.transOutput.clear()
        self.transStatusLabel.setText("Starting…")
        
        self.translate_thread = TranslateFileThread(
            self.trans_file_path, src, dst, engine,
        )
        self.translate_thread.finished.connect(self._on_trans_finished)
        self.translate_thread.error.connect(self._on_trans_error)
        self.translate_thread.status_update.connect(self.transStatusLabel.setText)
        self.logPanel.set_pipeline(self._PIPELINES["translate"])
        self.logPanel.clear()
        self.translate_thread.log_event.connect(self._on_log_event)
        self.translate_thread.start()
    
    def _on_trans_finished(self, result: str):
        self.transOutput.setPlainText(result)
        self.transStatusLabel.setText("Translation complete ✓")
        self.translateFileBtn.setEnabled(True)
        self.translateFileBtn.setText("🌐  Translate File")
    
    def _on_trans_error(self, error: str):
        self.transOutput.setPlainText(f"Error:\n{error}")
        self.transStatusLabel.setText("Translation failed")
        self.translateFileBtn.setEnabled(True)
        self.translateFileBtn.setText("🌐  Translate File")
        try:
            from modules.animations import shake
            from modules.toast import Toast
            shake(self, amplitude=8, cycles=3, duration_ms=220)
            Toast(self, error[:120], kind="error", duration_ms=4000).show_toast()
        except Exception:
            pass
    
    def _save_translation(self):
        text = self.transOutput.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Empty", "No translated content to save.")
            return
        
        # Default to same extension as source
        default_ext = ""
        if self.trans_file_path:
            base, ext = os.path.splitext(self.trans_file_path)
            dst_code = self._get_lang_code(self.trans_tgt_lang.currentText())
            default_ext = f"{base}_{dst_code}{ext}"
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Translation", default_ext,
            "SRT Files (*.srt);;Text Files (*.txt);;All Files (*.*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.transStatusLabel.setText(f"Saved to {os.path.basename(path)}")
    

    
    # ── Bearer Token ─────────────────────────────────────────────

    def _open_token_page(self):
        QDesktopServices.openUrl(QUrl("https://mlaas.virtuosgames.com/auth/token"))

    def _on_bearer_token_changed(self, text: str):
        self.mlaas_config.bearer_token = text.strip()
        save_bearer_token(text.strip())
        self._update_mlaas_status_label()

    def _update_mlaas_status_label(self):
        if self.mlaas_config.bearer_token.strip():
            self.mlaasStatusLabel.setText("✅ Bearer token active")
            self.mlaasStatusLabel.setStyleSheet("color: #4CAF50;")
        elif self.mlaas_config.api_key.strip():
            self.mlaasStatusLabel.setText("✅ DOGE AUTO SUB API PRO MAX")
            self.mlaasStatusLabel.setStyleSheet("color: #4CAF50;")
        else:
            self.mlaasStatusLabel.setText("❌ No API key — add MLAAS_API to .env")
            self.mlaasStatusLabel.setStyleSheet("color: #f44336;")

    # ── Background MLAAS Model Refresh ──────────────────────────

    def _refresh_models_async(self):
        """Fetch the latest MLAAS model list off the UI thread; refresh dropdowns when done."""
        config = self.mlaas_config

        class ModelFetchThread(QThread):
            finished_ok = Signal()

            def run(self):
                try:
                    fetch_mlaas_model_list(config)
                    self.finished_ok.emit()
                except Exception as e:
                    print(f"MLAAS model refresh failed: {e}")

        self._model_fetch_thread = ModelFetchThread()
        self._model_fetch_thread.finished_ok.connect(self._on_models_refreshed)
        self._model_fetch_thread.start()

    def _on_models_refreshed(self):
        """Re-populate engine dropdowns with the freshly-fetched model list."""
        # Preserve current selections so the user doesn't lose their choice
        current_target = self.target_engine.currentText() if self.target_engine.count() else ""
        current_trans = self.trans_engine.currentText() if self.trans_engine.count() else ""
        self._setup_translation_engines()
        if current_target:
            idx = self.target_engine.findText(current_target)
            if idx >= 0:
                self.target_engine.setCurrentIndex(idx)
        if current_trans:
            idx = self.trans_engine.findText(current_trans)
            if idx >= 0:
                self.trans_engine.setCurrentIndex(idx)

    # ── View Menu ───────────────────────────────────────────────

    def _setup_view_menu(self):
        from PySide6.QtWidgets import QMenu
        from PySide6.QtCore import QSettings
        view_label = self.menuItems.get("View")
        if not view_label:
            return
        view_label.setCursor(Qt.CursorShape.PointingHandCursor)
        settings = QSettings("DogeAutoSub", "ui")

        def _show_menu(event):
            menu = QMenu(self)
            s = QSettings("DogeAutoSub", "ui")

            act_motion = menu.addAction("Reduce Motion")
            act_motion.setCheckable(True)
            act_motion.setChecked(s.value("motion/reduce", False, type=bool))

            act_sounds = menu.addAction("Sounds Enabled")
            act_sounds.setCheckable(True)
            act_sounds.setChecked(s.value("sounds/enabled", False, type=bool))

            act_tips = menu.addAction("Show Doge Tips")
            act_tips.setCheckable(True)
            act_tips.setChecked(s.value("doge/tips_enabled", True, type=bool))

            def _apply(action):
                s2 = QSettings("DogeAutoSub", "ui")
                s2.setValue("motion/reduce", act_motion.isChecked())
                s2.setValue("sounds/enabled", act_sounds.isChecked())
                tips = act_tips.isChecked()
                s2.setValue("doge/tips_enabled", tips)
                try:
                    self.logPanel._narrator.enabled = tips
                except Exception:
                    pass

            menu.triggered.connect(_apply)
            menu.exec(view_label.mapToGlobal(view_label.rect().bottomLeft()))

        view_label.mousePressEvent = _show_menu

    # ── Auto-Update ─────────────────────────────────────────────

    def _check_for_updates(self):
        """Check for updates in a background thread (non-blocking)."""
        class UpdateCheckThread(QThread):
            update_found = Signal(object)
            
            def run(self):
                update = check_for_update()
                if update and update.is_newer:
                    self.update_found.emit(update)
        
        self._update_thread = UpdateCheckThread()
        self._update_thread.update_found.connect(self._on_update_available)
        self._update_thread.start()
    
    def _on_update_available(self, update):
        """Show update dialog when a new version is found."""
        notes = f"\n\nRelease notes:\n{update.notes}" if update.notes else ""
        
        reply = QMessageBox.question(
            self,
            "Update Available",
            f"A new version of DogeAutoSub is available!\n\n"
            f"Current: v{APP_VERSION}\n"
            f"New: v{update.version}"
            f"{notes}\n\n"
            f"Would you like to update now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._apply_update(update)
    
    def _apply_update(self, update):
        """Download and apply the update, then restart."""
        self.statusLabel.setText(f"Downloading update v{update.version}…")
        
        success = download_and_apply_update(
            update,
            progress_callback=lambda msg: self.statusLabel.setText(msg),
        )
        
        if success:
            reply = QMessageBox.information(
                self,
                "Update Complete",
                f"DogeAutoSub has been updated to v{update.version}.\n"
                f"The app will restart now.",
                QMessageBox.StandardButton.Ok,
            )
            restart_app()
        else:
            QMessageBox.warning(
                self,
                "Update Failed",
                "Failed to apply the update. Please try again later\n"
                "or download the latest version manually.",
            )


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    try:
        print("Starting DogeAutoSub…")
        app = QApplication(sys.argv)
        app.setApplicationName("DogeAutoSub")
        app.setApplicationVersion("2.0")

        _no_splash = "--no-splash" in sys.argv
        _splash = None
        if not _no_splash:
            try:
                from modules.splash import BootSplash
                _splash = BootSplash()
                _splash.show()
                _splash.set_progress(10, "Initialising…")
            except Exception as _e:
                print(f"Splash skipped: {_e}")
                _splash = None

        if _splash:
            _splash.set_progress(40, "Loading UI…")

        window = DogeAutoSub()

        if _splash:
            _splash.set_progress(90, "Ready!")
            _splash.fade_close()

        window.show()

        exit_code = app.exec()
        sys.exit(exit_code)

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("DogeAutoSub Error")
            msg.setText(f"Failed to start: {str(e)}")
            msg.exec()
        except Exception:
            pass
        sys.exit(1)
