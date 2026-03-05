import os
import time
from PySide6.QtCore import QThread, Signal

# ── Paths ───────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG_PATH = os.path.join(SCRIPT_DIR, "modules", "ffmpeg", "bin", "ffmpeg.exe")
TEMP_DIR = os.path.join(SCRIPT_DIR, "modules", "temp")

from modules.subtitle_args import SubtitleArgs
from modules.mlaas_client import MLAASConfig, translate_segments_mlaas
from modules.constants import LANGUAGE_CODES_AI

# Try importing optional translation engines
try:
    from deep_translator import GoogleTranslator
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False

try:
    from modules.marian_translator import MarianTranslator, MARIAN_AVAILABLE
except ImportError:
    MARIAN_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


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
