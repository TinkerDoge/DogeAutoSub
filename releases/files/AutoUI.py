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
from modules.constants import MODEL_INFO, LANGUAGE_CODES_AI, MODEL_TYPES
from modules.subtitle_args import SubtitleArgs
from modules.mlaas_client import MLAASConfig, translate_segments_mlaas, summarize_text_mlaas, get_masked_key, get_api_key
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
    from modules.marian_translator import MarianTranslator, MARIAN_AVAILABLE
except ImportError:
    MARIAN_AVAILABLE = False

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
        
        # ── Load dark theme ─────────────────────────────────────
        self._load_theme("Dark")
        
        # ── Setup animations ────────────────────────────────────
        self.loading_movie = None
        self.standby_movie = None
        self.done_pixmap = None
        
        loading_gif = os.path.join(SCRIPT_DIR, "icons", "loading.gif")
        start_gif = os.path.join(SCRIPT_DIR, "icons", "start.gif")
        done_img = os.path.join(SCRIPT_DIR, "icons", "done.jpg")
        
        if os.path.exists(loading_gif):
            self.loading_movie = QMovie(loading_gif)
        if os.path.exists(start_gif):
            self.standby_movie = QMovie(start_gif)
            self.statusImage.setMovie(self.standby_movie)
            self.standby_movie.start()
        if os.path.exists(done_img):
            self.done_pixmap = QPixmap(done_img).scaled(
                130, 130, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        
        # ── Populate dropdowns ──────────────────────────────────
        self._setup_model_dropdown()
        self._setup_language_dropdowns()
        self._setup_translation_engines()
        
        # ── Connect signals ─────────────────────────────────────
        self.selectFileBtn.clicked.connect(self._select_input_file)
        self.selectOutputBtn.clicked.connect(self._select_output_folder)
        self.startButton.clicked.connect(self._start_subtitles)
        self.model_size_dropdown.currentTextChanged.connect(self._on_model_changed)
        self.themeBtn.clicked.connect(self._toggle_theme)
        self.openFolderBtn.clicked.connect(self._open_output_folder)
        
        # Meeting notes signals
        self.selectDocxBtn.clicked.connect(self._select_docx)
        self.generateNotesBtn.clicked.connect(self._generate_meeting_notes)
        self.saveNotesBtn.clicked.connect(self._save_meeting_notes)
        
        # Translation tab signals
        self.selectTransFileBtn.clicked.connect(self._select_trans_file)
        self.translateFileBtn.clicked.connect(self._start_file_translation)
        self.saveTransBtn.clicked.connect(self._save_translation)
        
        # ── Load MLAAS API key from .env ─────────────────────
        self.mlaas_config = MLAASConfig.from_env()
        masked = get_masked_key(self.mlaas_config.api_key)
        if self.mlaas_config.is_configured():
            self.mlaasStatusLabel.setText(f"✅ DOGE AUTO SUB API PRO MAX")
            self.mlaasStatusLabel.setStyleSheet("color: #4CAF50;")
        else:
            self.mlaasStatusLabel.setText("❌ No API key — add MLAAS_API to .env")
            self.mlaasStatusLabel.setStyleSheet("color: #f44336;")
        
        # ── Set window title with version ───────────────────
        self.setWindowTitle(f"DogeAutoSub v{APP_VERSION}")
        self.versionLabel.setText(f"v{APP_VERSION}")
        
        # ── Check for updates (non-blocking) ────────────────
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, self._check_for_updates)
        
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
        # Subtitles tab engine
        self.target_engine.clear()
        self.target_engine.addItem("mlaas")
        self.target_engine.addItem("google")
        self.target_engine.addItem("whisper")
        if MARIAN_AVAILABLE:
            self.target_engine.addItem("marian")
        self.target_engine.setCurrentText("mlaas")
        
        # Translation tab dropdowns — reuse same languages
        self.trans_src_lang.clear()
        self.trans_tgt_lang.clear()
        self.trans_src_lang.addItem("Auto")
        for code, name in LANGUAGE_CODES_AI:
            if code != "auto":
                self.trans_src_lang.addItem(name)
                self.trans_tgt_lang.addItem(name)
        self.trans_src_lang.setCurrentText("Auto")
        self.trans_tgt_lang.setCurrentText("Vietnamese")
        
        # Translation tab engine
        self.trans_engine.clear()
        self.trans_engine.addItem("mlaas")
        self.trans_engine.addItem("google")
        if MARIAN_AVAILABLE:
            self.trans_engine.addItem("marian")
        self.trans_engine.setCurrentText("mlaas")
    
    # ── Theme ───────────────────────────────────────────────────
    
    def _load_theme(self, theme: str):
        filename = "styleSheetDark.css" if theme == "Dark" else "styleSheetLight.css"
        path = os.path.join(SCRIPT_DIR, "modules", filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                self.setStyleSheet(f.read())
        self.current_theme = theme
    
    def _toggle_theme(self):
        new_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self._load_theme(new_theme)
    
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
            translate_engine=self.target_engine.currentText(),
            volume=self.boostSlider.value(),
        )
        
        self.subtitle_thread = SubtitleThread(args)
        self.subtitle_thread.task_start.connect(self._on_task_start)
        self.subtitle_thread.task_complete.connect(self._on_task_complete)
        self.subtitle_thread.progress_update.connect(self.progressBar.setValue)
        self.subtitle_thread.status_update.connect(self.statusLabel.setText)
        self.subtitle_thread.duration_update.connect(self.etaLabel.setText)
        self.subtitle_thread.start()
    
    def _on_task_start(self):
        self.startButton.setEnabled(False)
        self.startButton.setText("⏳  Processing…")
        self.statusLabel.setText("Starting…")
        self.progressBar.setValue(0)
        if self.loading_movie:
            self.statusImage.setMovie(self.loading_movie)
            self.loading_movie.start()
    
    def _on_task_complete(self):
        self.startButton.setEnabled(True)
        self.startButton.setText("▶  START PROCESSING")
        self.progressBar.setValue(100)
        if self.loading_movie:
            self.loading_movie.stop()
        if self.done_pixmap:
            self.statusImage.setPixmap(self.done_pixmap)
    
    # ── Meeting Notes ───────────────────────────────────────────
    
    def _select_docx(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Meeting Transcript", "",
            "Word Documents (*.docx);;All Files (*.*)"
        )
        if path:
            self.docx_path = path
            self.selectDocxBtn.setText(f"📎  {os.path.basename(path)}")
            self.docxPathLabel.setText(path)
    
    def _generate_meeting_notes(self):
        if not self.docx_path:
            QMessageBox.warning(self, "No File", "Please upload a DOCX transcript first.")
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
        engine = self.trans_engine.currentText()
        
        if engine == "mlaas" and not self.mlaas_config.is_configured():
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
        
        window = DogeAutoSub()
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
