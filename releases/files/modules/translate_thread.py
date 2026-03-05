import os
from PySide6.QtCore import QThread, Signal

try:
    from deep_translator import GoogleTranslator
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False

try:
    from modules.marian_translator import MarianTranslator, MARIAN_AVAILABLE
except ImportError:
    MARIAN_AVAILABLE = False


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


def _translate_single(text: str, src: str, dst: str, engine: str, api_key: str = "") -> str:
    """Translate a single text string using the selected engine."""
    if not text.strip():
        return text
    
    if engine == "mlaas":
        from modules.mlaas_client import translate_text_mlaas, MLAASConfig
        config = MLAASConfig.from_env()
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
                    content, self.src_lang, self.dst_lang,
                    self.engine, "", on_progress,
                )
            else:
                result = _translate_plain_content(
                    content, self.src_lang, self.dst_lang,
                    self.engine, "", on_progress,
                )
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(f"Translation error: {str(e)}")
