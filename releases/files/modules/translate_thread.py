import os
import re
from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import QThread, Signal

try:
    from deep_translator import GoogleTranslator
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False


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
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Cannot decode file: {filepath}")


# ── SRT parsing helpers ─────────────────────────────────────────

# An SRT cue: optional index line, timestamp line "HH:MM:SS,mmm --> HH:MM:SS,mmm", text lines.
_SRT_BLOCK_SPLIT = re.compile(r"\n\s*\n")
_SRT_TIMESTAMP_RE = re.compile(
    r"^(\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3})"
)


def _parse_srt_cues(srt_text: str) -> List[dict]:
    """
    Parse SRT text into a list of cue dicts.

    Each cue is either:
      {"kind": "cue", "index": str, "timestamp_line": str, "text": str}
    or for blocks we couldn't parse:
      {"kind": "raw", "raw": str}  (passed through untranslated)
    """
    cues: List[dict] = []
    for raw_block in _SRT_BLOCK_SPLIT.split(srt_text.strip()):
        block = raw_block.strip("\n")
        if not block.strip():
            continue
        lines = block.split("\n")
        # Find the timestamp line (usually line 0 or 1)
        ts_idx = -1
        for i, line in enumerate(lines[:2]):
            if _SRT_TIMESTAMP_RE.match(line.strip()):
                ts_idx = i
                break
        if ts_idx == -1:
            cues.append({"kind": "raw", "raw": block})
            continue
        index_line = lines[0].strip() if ts_idx == 1 else ""
        timestamp_line = lines[ts_idx].strip()
        text = "\n".join(lines[ts_idx + 1:]).strip()
        cues.append({
            "kind": "cue",
            "index": index_line,
            "timestamp_line": timestamp_line,
            "text": text,
        })
    return cues


def _cues_to_srt(cues: List[dict]) -> str:
    """Reassemble cues into SRT text. Re-numbers indices when missing."""
    out_blocks: List[str] = []
    auto_idx = 1
    for cue in cues:
        if cue.get("kind") == "raw":
            out_blocks.append(cue["raw"])
            continue
        idx = cue.get("index") or str(auto_idx)
        auto_idx += 1
        block = f"{idx}\n{cue['timestamp_line']}\n{cue['text']}"
        out_blocks.append(block)
    return "\n\n".join(out_blocks) + "\n"


# ── Translation dispatch ────────────────────────────────────────

def _translate_texts_batched(
    texts: List[str],
    src_lang: str,
    dst_lang: str,
    engine: str,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> List[str]:
    """
    Translate a list of plain strings using the selected engine.
    Reuses the chunked + batched primitives from mlaas_client for non-Google engines.
    Returns a list of translations the same length as `texts`.
    """
    if not texts:
        return []

    if engine == "google":
        return _translate_texts_google(texts, src_lang, dst_lang, progress_cb)

    # MLAAS-routed engines: wrap as segments to reuse the batch translators.
    from modules.mlaas_client import (
        MLAASConfig, translate_segments_mlaas, translate_segments_openai,
    )
    config = MLAASConfig.from_env()
    segments = [{"start": 0.0, "end": 0.0, "text": t} for t in texts]

    # claude-* models go through the Anthropic proxy; everything else through OpenAI proxy.
    if engine.startswith("claude"):
        translated_segments = translate_segments_mlaas(
            segments, dst_lang, config, progress_callback=progress_cb,
        )
    else:
        translated_segments = translate_segments_openai(
            segments, dst_lang, config, progress_callback=progress_cb, model=engine,
        )

    out = [seg.get("text", "") for seg in translated_segments]
    # Pad/truncate defensively in case of mismatched batch responses.
    if len(out) < len(texts):
        out.extend(texts[len(out):])
    return out[:len(texts)]


def _translate_texts_google(
    texts: List[str],
    src_lang: str,
    dst_lang: str,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> List[str]:
    """Per-line Google Translate (no batching available in deep_translator)."""
    if not GOOGLE_TRANSLATE_AVAILABLE:
        print("Google Translate not available, returning originals")
        return list(texts)

    source = "auto" if src_lang == "auto" else src_lang
    try:
        translator = GoogleTranslator(source=source, target=dst_lang)
    except Exception as e:
        print(f"Google translator init failed: {e}")
        return list(texts)

    out: List[str] = []
    total = len(texts)
    for i, text in enumerate(texts):
        try:
            out.append(translator.translate(text) if text.strip() else text)
        except Exception:
            out.append(text)
        if progress_cb and total:
            progress_cb(int(((i + 1) / total) * 100))
    return out


# ── High-level file translators ─────────────────────────────────

def _translate_srt_content(
    srt_text: str, src_lang: str, dst_lang: str, engine: str,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> str:
    """Translate SRT content preserving timestamps and structure."""
    cues = _parse_srt_cues(srt_text)
    cue_indices = [i for i, c in enumerate(cues) if c.get("kind") == "cue"]
    texts = [cues[i]["text"] for i in cue_indices]

    translations = _translate_texts_batched(texts, src_lang, dst_lang, engine, progress_cb)

    for i, t in zip(cue_indices, translations):
        cues[i]["text"] = t

    return _cues_to_srt(cues)


def _translate_plain_content(
    text: str, src_lang: str, dst_lang: str, engine: str,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> str:
    """Translate plain text content line by line, preserving order and blank lines."""
    raw_lines = text.split("\n")
    # Track which lines we'll translate (non-empty), preserve everything else.
    translatable_indices = [i for i, line in enumerate(raw_lines) if line.strip()]
    translatable_texts = [raw_lines[i] for i in translatable_indices]

    translations = _translate_texts_batched(
        translatable_texts, src_lang, dst_lang, engine, progress_cb,
    )

    out_lines = list(raw_lines)
    for i, t in zip(translatable_indices, translations):
        out_lines[i] = t
    return "\n".join(out_lines)


class TranslateFileThread(QThread):
    """Worker thread for file translation."""

    finished = Signal(str)
    error = Signal(str)
    status_update = Signal(str)
    progress_update = Signal(int)

    def __init__(self, filepath: str, src_lang: str, dst_lang: str,
                 engine: str):
        super().__init__()
        self.filepath = filepath
        self.src_lang = src_lang
        self.dst_lang = dst_lang
        self.engine = engine

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
                    content, self.src_lang, self.dst_lang, self.engine, on_progress,
                )
            else:
                result = _translate_plain_content(
                    content, self.src_lang, self.dst_lang, self.engine, on_progress,
                )

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(f"Translation error: {str(e)}")
