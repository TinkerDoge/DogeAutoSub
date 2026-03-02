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

import ui_DogeAutoSub
from modules.constants import MODEL_INFO, LANGUAGE_CODES_AI, MODEL_TYPES
from modules.subtitle_args import SubtitleArgs
from modules.mlaas_client import MLAASConfig, translate_segments_mlaas, summarize_text_mlaas, get_masked_key
from modules.updater import APP_VERSION, check_for_update, download_and_apply_update, restart_app

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
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _lang_code(name: str, default: str = "auto") -> str:
    """Convert a display name like 'English' to a language code like 'en'."""
    if not name:
        return default
    for code, disp in LANGUAGE_CODES_AI:
        if disp.lower() == name.lower():
            return code
    return name.lower()



def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def save_as_srt(segments: list, output_path: str):
    """Save transcription segments as an SRT file."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = seg.get("text", "").strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    print(f"Subtitles saved to {output_path}")


def translate_segments_google(segments: list, src_lang: str, dst_lang: str) -> list:
    """Translate segments using Google Translate."""
    if not GOOGLE_TRANSLATE_AVAILABLE:
        print("Google Translate not available, returning original segments")
        return segments

    source = None if src_lang == 'auto' else src_lang
    # Handle Chinese variants
    source_options = ['zh-CN', 'zh-TW'] if src_lang == 'zh' else [source]

    try:
        translator = GoogleTranslator(source=source_options[0], target=dst_lang)
        # Test with first option
        if segments:
            try:
                translator.translate(segments[0].get("text", "test")[:50])
            except Exception:
                for alt in source_options[1:]:
                    try:
                        translator = GoogleTranslator(source=alt, target=dst_lang)
                        translator.translate(segments[0].get("text", "test")[:50])
                        break
                    except Exception:
                        continue
    except Exception as e:
        print(f"Error initializing translator: {e}")
        return segments

    translated = []
    for seg in segments:
        try:
            text = seg.get("text", "").strip()
            translated_text = translator.translate(text) if text else ""
            translated.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": translated_text,
            })
        except Exception:
            translated.append(seg)
    return translated


# ═══════════════════════════════════════════════════════════════
# THROUGHPUT TRACKER (replaces heuristic-based ETA)
# ═══════════════════════════════════════════════════════════════

class ThroughputTracker:
    """Track real-time processing speed for accurate ETA calculation."""
    
    def __init__(self):
        self.start_time = time.time()
        self._stage_start = time.time()
        self._audio_processed = 0.0
        self._total_audio = 0.0
    
    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time
    
    def set_total_audio(self, duration: float):
        self._total_audio = duration
    
    def update(self, audio_seconds_done: float):
        """Update with amount of audio processed so far."""
        self._audio_processed = audio_seconds_done
    
    def eta_string(self) -> str:
        """Get formatted ETA string."""
        elapsed = time.time() - self._stage_start
        if self._audio_processed <= 0 or elapsed < 2:
            return "Calculating..."
        throughput = self._audio_processed / elapsed  # audio seconds per wall second
        remaining_audio = max(0, self._total_audio - self._audio_processed)
        if throughput > 0:
            eta_seconds = remaining_audio / throughput
            return time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
        return "Calculating..."
    
    def elapsed_string(self) -> str:
        return time.strftime("%H:%M:%S", time.gmtime(self.elapsed))
    
    def start_stage(self):
        self._stage_start = time.time()
        self._audio_processed = 0.0


# ═══════════════════════════════════════════════════════════════
# SUBTITLE THREAD — Clean 5-step pipeline
# ═══════════════════════════════════════════════════════════════

class SubtitleThread(QThread):
    """Worker thread for subtitle generation pipeline."""
    
    task_complete = Signal()
    task_start = Signal()
    progress_update = Signal(int)
    status_update = Signal(str)
    duration_update = Signal(str)
    
    def __init__(self, args: SubtitleArgs):
        super().__init__()
        self.args = args
        self.tracker = ThroughputTracker()
    
    def run(self):
        try:
            self.task_start.emit()
            self.tracker = ThroughputTracker()
            
            src_code = _lang_code(self.args.src_language or "Auto", "auto")
            dst_code = _lang_code(self.args.dst_language or "English", "en")
            os.makedirs(TEMP_DIR, exist_ok=True)
            
            # ── Step 1: Load faster-whisper + Process ───────────
            self.status_update.emit("Loading faster-whisper model…")
            self.progress_update.emit(5)
            
            from modules.faster_whisper_engine import FasterWhisperRecognizer
            from modules.chunk_processor import ChunkProcessor
            
            processor = ChunkProcessor(
                chunk_duration=30.0,
                volume_boost=str(self.args.volume),
                ffmpeg_path=FFMPEG_PATH,
            )
            
            recognizer = FasterWhisperRecognizer(
                model_size=self.args.model_size,
                language=None if src_code == "auto" else src_code,
            )
            
            self.progress_update.emit(15)
            
            # ── Step 2: Extract audio + Transcribe ──────────────
            self.status_update.emit("Processing audio…")
            self.tracker.start_stage()
            
            transcribe_start = time.time()
            
            def chunk_progress_cb(completed, total, stage, eta_seconds):
                if total > 0:
                    # Map to 15-85% range
                    progress = 15 + int((completed / total) * 70)
                    self.progress_update.emit(min(progress, 85))
                self.status_update.emit(stage)
                if processor.total_duration > 0:
                    audio_done = (completed / max(total, 1)) * processor.total_duration
                    self.tracker.update(audio_done)
                eta = self.tracker.eta_string()
                elapsed = self.tracker.elapsed_string()
                self.duration_update.emit(f"Elapsed: {elapsed} | ETA: {eta}")
            
            segs, detected = processor.process_parallel(
                self.args.source_path,
                recognizer,
                progress_callback=chunk_progress_cb,
            )
            
            transcribe_time = time.time() - transcribe_start
            video_duration = processor.total_duration
            self.tracker.set_total_audio(video_duration)
            
            segments_count = len(segs or [])
            base = os.path.splitext(os.path.basename(self.args.source_path))[0]
            out_dir = self.args.output_folder or os.path.dirname(self.args.source_path)
            os.makedirs(out_dir, exist_ok=True)
            
            # Resolve auto-detected language
            actual_src = detected if (src_code == "auto" and detected) else src_code
            
            # ── Step 3: Save original transcription ─────────────
            self.status_update.emit("Saving transcription…")
            self.progress_update.emit(86)
            orig_srt = os.path.join(out_dir, f"{base}.srt")
            if segs:
                save_as_srt(segs, orig_srt)
            
            # ── Step 4: Translate if needed ──────────────────────
            translate_time = 0
            if actual_src != dst_code:
                self.status_update.emit(f"Translating {actual_src} → {dst_code}…")
                translate_start = time.time()
                
                engine = (self.args.translate_engine or "google").lower()
                translated_segments = None
                
                try:
                    if engine == "mlaas":
                        self.status_update.emit(f"Translating via MLAAS API ({actual_src} → {dst_code})…")
                        mlaas_config = MLAASConfig.from_env()
                        translated_segments = translate_segments_mlaas(
                            segs, dst_code, mlaas_config,
                            progress_callback=lambda p: self.progress_update.emit(86 + int(p * 0.13)),
                        )
                    elif engine == "marian" and MARIAN_AVAILABLE:
                        translator = MarianTranslator(actual_src, dst_code)
                        if translator.load_model():
                            texts = [s.get("text", "") for s in segs]
                            preds = translator.translate_batch(
                                texts,
                                batch_size=8 if (TORCH_AVAILABLE and torch.cuda.is_available()) else 4,
                                progress_cb=lambda f: self.progress_update.emit(86 + int((f or 0) * 13)),
                            )
                            translated_segments = [
                                {"start": s["start"], "end": s["end"], "text": preds[i] if i < len(preds) else s.get("text", "")}
                                for i, s in enumerate(segs)
                            ]
                    elif engine == "whisper" and hasattr(recognizer, 'translate'):
                        # Use the audio already extracted by ChunkProcessor
                        audio_path = os.path.join(TEMP_DIR, "chunks", "full_audio.wav")
                        if os.path.exists(audio_path):
                            translated_segments = recognizer.translate(audio_path, dst_code) or []
                        else:
                            print("Warning: No extracted audio found for whisper translate")
                            translated_segments = None
                    else:
                        # Default: Google Translate
                        translated_segments = translate_segments_google(segs, actual_src, dst_code)
                except Exception as e:
                    print(f"Translation error ({engine}): {e}")
                    translated_segments = None
                
                translate_time = time.time() - translate_start
                
                if translated_segments:
                    tgt_srt = os.path.join(out_dir, f"{base}_{dst_code}.srt")
                    save_as_srt(translated_segments, tgt_srt)
            
            # ── Step 5: Done ────────────────────────────────────
            self.progress_update.emit(100)
            
            total_time = time.time() - self.tracker.start_time
            print(f"\n{'='*50}")
            print(f"TASK COMPLETED")
            print(f"{'='*50}")
            print(f"Video Length:     {time.strftime('%H:%M:%S', time.gmtime(video_duration))} ({video_duration:.1f}s)")
            print(f"Transcribe Time:  {time.strftime('%H:%M:%S', time.gmtime(transcribe_time))} ({transcribe_time:.1f}s)")
            if translate_time > 0:
                print(f"Translate Time:   {time.strftime('%H:%M:%S', time.gmtime(translate_time))} ({translate_time:.1f}s)")
            print(f"Total Time:       {time.strftime('%H:%M:%S', time.gmtime(total_time))} ({total_time:.1f}s)")
            print(f"Segments:         {segments_count}")
            print(f"{'='*50}\n")
            
            elapsed = self.tracker.elapsed_string()
            self.duration_update.emit(f"Completed in {elapsed}")
            self.status_update.emit("Completed ✓")
            self.task_complete.emit()
            
        except Exception as e:
            print(f"SubtitleThread error: {e}")
            import traceback
            traceback.print_exc()
            self.status_update.emit(f"Error: {str(e)[:80]}")
            self.task_complete.emit()


# ═══════════════════════════════════════════════════════════════
# MEETING NOTES THREAD
# ═══════════════════════════════════════════════════════════════

class MeetingNotesThread(QThread):
    """Worker thread for meeting notes generation via MLAAS."""
    
    finished = Signal(str)   # result text
    error = Signal(str)      # error message
    status_update = Signal(str)
    
    def __init__(self, docx_path: str, api_key: str):
        super().__init__()
        self.docx_path = docx_path
        self.api_key = api_key
    
    def run(self):
        try:
            from modules.meeting_notes import (
                parse_meeting_docx, format_transcript_for_llm,
            )
            
            self.status_update.emit("Parsing transcript…")
            blocks = parse_meeting_docx(self.docx_path)
            
            if not blocks:
                self.error.emit("No speaker blocks found in the document. Check the format.")
                return
            
            self.status_update.emit(f"Found {len(blocks)} speaker blocks. Formatting…")
            transcript = format_transcript_for_llm(blocks)
            
            self.status_update.emit("Sending to MLAAS for summarization…")
            config = MLAASConfig(api_key=self.api_key)
            result = summarize_text_mlaas(
                transcript, config,
                progress_callback=lambda msg: self.status_update.emit(msg),
            )
            
            self.finished.emit(result)
            
        except ImportError as e:
            self.error.emit(f"Missing dependency: {e}\nInstall with: pip install python-docx")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# FILE TRANSLATION THREAD
# ═══════════════════════════════════════════════════════════════

def _read_file_content(filepath: str) -> str:
    """Read content from SRT, DOCX, or TXT file."""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == ".docx":
        try:
            import docx
            doc = docx.Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise ImportError("python-docx is required. Install with: pip install python-docx")
    else:
        # SRT, TXT, and other plain text
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Cannot decode file: {filepath}")


def _translate_srt_content(
    srt_text: str, src_lang: str, dst_lang: str, engine: str,
    api_key: str, progress_cb=None,
) -> str:
    """Translate SRT content preserving timestamps and structure."""
    import re as _re
    blocks = _re.split(r"\n\n+", srt_text.strip())
    translated_blocks = []
    total = len(blocks)
    
    for i, block in enumerate(blocks):
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            # lines[0] = index, lines[1] = timestamp, lines[2:] = text
            text_lines = "\n".join(lines[2:])
            translated = _translate_single(text_lines, src_lang, dst_lang, engine, api_key)
            translated_blocks.append(f"{lines[0]}\n{lines[1]}\n{translated}")
        else:
            translated_blocks.append(block)
        
        if progress_cb and total > 0:
            progress_cb(int(((i + 1) / total) * 100))
    
    return "\n\n".join(translated_blocks)


def _translate_plain_content(
    text: str, src_lang: str, dst_lang: str, engine: str,
    api_key: str, progress_cb=None,
) -> str:
    """Translate plain text content line by line."""
    lines = [l for l in text.split("\n") if l.strip()]
    translated_lines = []
    total = len(lines)
    
    for i, line in enumerate(lines):
        translated = _translate_single(line.strip(), src_lang, dst_lang, engine, api_key)
        translated_lines.append(translated)
        
        if progress_cb and total > 0:
            progress_cb(int(((i + 1) / total) * 100))
    
    return "\n".join(translated_lines)


def _translate_single(text: str, src: str, dst: str, engine: str, api_key: str) -> str:
    """Translate a single text string using the selected engine."""
    if not text.strip():
        return text
    
    if engine == "mlaas":
        from modules.mlaas_client import translate_text_mlaas, MLAASConfig
        config = MLAASConfig(api_key=api_key)
        return translate_text_mlaas(text, dst, config)
    elif engine == "marian" and MARIAN_AVAILABLE:
        translator = MarianTranslator(src, dst)
        if translator.load_model():
            results = translator.translate_batch([text], batch_size=1)
            return results[0] if results else text
        return text
    else:
        # Google Translate
        if GOOGLE_TRANSLATE_AVAILABLE:
            return GoogleTranslator(source=src if src != "auto" else "auto", target=dst).translate(text) or text
        return text


class TranslateFileThread(QThread):
    """Worker thread for file translation."""
    
    finished = Signal(str)
    error = Signal(str)
    status_update = Signal(str)
    progress_update = Signal(int)
    
    def __init__(self, filepath: str, src_lang: str, dst_lang: str,
                 engine: str, api_key: str):
        super().__init__()
        self.filepath = filepath
        self.src_lang = src_lang
        self.dst_lang = dst_lang
        self.engine = engine
        self.api_key = api_key
    
    def run(self):
        try:
            self.status_update.emit("Reading file…")
            content = _read_file_content(self.filepath)
            
            if not content.strip():
                self.error.emit("File is empty or could not be read.")
                return
            
            ext = os.path.splitext(self.filepath)[1].lower()
            line_count = content.count("\n") + 1
            self.status_update.emit(f"Translating {line_count} lines via {self.engine}…")
            
            def on_progress(pct):
                self.progress_update.emit(pct)
                self.status_update.emit(f"Translating… {pct}%")
            
            if ext == ".srt":
                result = _translate_srt_content(
                    content, self.src_lang, self.dst_lang,
                    self.engine, self.api_key, on_progress,
                )
            else:
                result = _translate_plain_content(
                    content, self.src_lang, self.dst_lang,
                    self.engine, self.api_key, on_progress,
                )
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(f"Translation error: {str(e)}")



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
            self.mlaasStatusLabel.setText(f"✅ {masked}")
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
        
        self.notes_thread = MeetingNotesThread(self.docx_path, self.mlaas_config.api_key)
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
            self.trans_file_path, src, dst, engine, self.mlaas_config.api_key,
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
