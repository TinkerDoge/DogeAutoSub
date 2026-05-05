from PySide6.QtCore import QThread, Signal
from modules.mlaas_client import MLAASConfig, summarize_text_mlaas


class MeetingNotesThread(QThread):
    """Worker thread for meeting notes generation via MLAAS."""

    finished = Signal(str)
    error = Signal(str)
    status_update = Signal(str)
    log_event = Signal(dict)

    def __init__(self, docx_path: str):
        super().__init__()
        self.docx_path = docx_path

    def _emit(self, kind: str, **fields):
        evt = {"kind": kind}
        evt.update(fields)
        self.log_event.emit(evt)

    def run(self):
        try:
            from modules.meeting_notes import (
                parse_meeting_transcript, format_transcript_for_llm,
            )

            self._emit("step_start", step="Read transcript")
            self.status_update.emit("Parsing transcript…")
            blocks = parse_meeting_transcript(self.docx_path)

            if not blocks:
                self.error.emit("No speaker blocks found in the document. Check the format.")
                return

            self._emit("step_done", step="Read transcript")
            self._emit("step_start", step="Summarize")
            self.status_update.emit(f"Found {len(blocks)} speaker blocks. Formatting…")
            transcript = format_transcript_for_llm(blocks)

            self.status_update.emit("Sending to MLAAS for summarization…")
            config = MLAASConfig.from_env()
            result = summarize_text_mlaas(
                transcript, config,
                progress_callback=lambda msg: self.status_update.emit(msg),
            )

            self._emit("step_done", step="Summarize")
            self._emit("step_start", step="Format")
            self._emit("step_done", step="Format")
            self.finished.emit(result)

        except ImportError as e:
            self._emit("log", level="error", text=str(e))
            self.error.emit(f"Missing dependency: {e}")
        except Exception as e:
            self._emit("log", level="error", text=str(e))
            self.error.emit(f"Error: {str(e)}")
