from PySide6.QtCore import QThread, Signal
from modules.mlaas_client import MLAASConfig, summarize_text_mlaas

class MeetingNotesThread(QThread):
    """Worker thread for meeting notes generation via MLAAS."""
    
    finished = Signal(str)   # result text
    error = Signal(str)      # error message
    status_update = Signal(str)
    
    def __init__(self, docx_path: str):
        super().__init__()
        self.docx_path = docx_path
    
    def run(self):
        try:
            from modules.meeting_notes import (
                parse_meeting_transcript, format_transcript_for_llm,
            )
            
            self.status_update.emit("Parsing transcript…")
            blocks = parse_meeting_transcript(self.docx_path)
            
            if not blocks:
                self.error.emit("No speaker blocks found in the document. Check the format.")
                return
            
            self.status_update.emit(f"Found {len(blocks)} speaker blocks. Formatting…")
            transcript = format_transcript_for_llm(blocks)
            
            self.status_update.emit("Sending to MLAAS for summarization…")
            config = MLAASConfig.from_env()
            result = summarize_text_mlaas(
                transcript, config,
                progress_callback=lambda msg: self.status_update.emit(msg),
            )
            
            self.finished.emit(result)
            
        except ImportError as e:
            self.error.emit(f"Missing dependency: {e}")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")
