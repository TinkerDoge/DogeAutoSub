"""
Meeting Notes module for DogeAutoSub.
Provides DOCX transcript parsing and LLM-based summarization framework.

The LLM API integration is a framework/stub — the actual internal API
endpoint will be configured later by the user.
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class SpeakerBlock:
    """A single block of speech from a meeting transcript."""
    speaker: str
    text: str
    timestamp: str = ""


@dataclass
class LLMConfig:
    """Configuration for the LLM API connection."""
    api_url: str = ""
    api_key: str = ""
    model_name: str = ""
    system_prompt: str = (
        "You are a professional meeting note-taker. Given the following meeting transcript "
        "with speaker names and their dialogue, create a well-structured summary that includes:\n"
        "1. **Meeting Overview** - Brief summary of what the meeting was about\n"
        "2. **Key Discussion Points** - Main topics discussed\n"
        "3. **Action Items** - Tasks assigned with responsible persons\n"
        "4. **Decisions Made** - Any decisions reached during the meeting\n"
        "5. **Follow-ups** - Items that need follow-up\n\n"
        "Keep the summary concise but comprehensive."
    )
    max_tokens: int = 2048
    temperature: float = 0.3

    def is_configured(self) -> bool:
        """Check if the LLM API is properly configured."""
        return bool(self.api_url and self.api_key and self.model_name)

    def save_to_file(self, filepath: str):
        """Save config to a JSON file."""
        data = {
            "api_url": self.api_url,
            "api_key": self.api_key,
            "model_name": self.model_name,
            "system_prompt": self.system_prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "LLMConfig":
        """Load config from a JSON file."""
        if not os.path.exists(filepath):
            return cls()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception as e:
            print(f"Error loading LLM config: {e}")
            return cls()


def parse_meeting_docx(file_path: str) -> List[SpeakerBlock]:
    """
    Parse a DOCX meeting transcript file into speaker blocks.
    
    Supports common formats from Teams and Zoom:
    - "Speaker Name  HH:MM:SS" followed by text
    - "Speaker Name:" followed by text
    - Timestamped blocks with speaker labels
    
    Args:
        file_path: Path to the .docx file
        
    Returns:
        List of SpeakerBlock objects
    """
    try:
        from docx import Document
    except ImportError:
        raise ImportError(
            "python-docx is required for DOCX parsing. "
            "Install it with: pip install python-docx"
        )
    
    doc = Document(file_path)
    blocks: List[SpeakerBlock] = []
    
    # Patterns for speaker detection
    # Teams format: "Speaker Name   0:15:30"
    teams_pattern = re.compile(r'^(.+?)\s{2,}(\d{1,2}:\d{2}(?::\d{2})?)\s*$')
    # Zoom format: "Speaker Name:" or "Speaker Name (HH:MM:SS):"
    zoom_pattern = re.compile(r'^(.+?)(?:\s*\((\d{1,2}:\d{2}(?::\d{2})?)\))?\s*:\s*$')
    # Generic: "Speaker Name:"  with text on same line
    generic_pattern = re.compile(r'^([A-Z][a-zA-Z\s\.]+?):\s+(.+)$')
    
    current_speaker = ""
    current_timestamp = ""
    current_text_lines: List[str] = []
    
    def flush_block():
        nonlocal current_speaker, current_timestamp, current_text_lines
        if current_speaker and current_text_lines:
            text = " ".join(line.strip() for line in current_text_lines if line.strip())
            if text:
                blocks.append(SpeakerBlock(
                    speaker=current_speaker.strip(),
                    text=text,
                    timestamp=current_timestamp,
                ))
        current_text_lines = []
    
    for para in doc.paragraphs:
        line = para.text.strip()
        if not line:
            continue
        
        # Try Teams format
        teams_match = teams_pattern.match(line)
        if teams_match:
            flush_block()
            current_speaker = teams_match.group(1).strip()
            current_timestamp = teams_match.group(2).strip()
            continue
        
        # Try Zoom format
        zoom_match = zoom_pattern.match(line)
        if zoom_match:
            flush_block()
            current_speaker = zoom_match.group(1).strip()
            current_timestamp = zoom_match.group(2) or ""
            continue
        
        # Try generic "Speaker: text" format
        generic_match = generic_pattern.match(line)
        if generic_match and not current_speaker:
            flush_block()
            current_speaker = generic_match.group(1).strip()
            current_text_lines.append(generic_match.group(2))
            continue
        
        # Regular text line — append to current speaker's block
        if current_speaker:
            current_text_lines.append(line)
        else:
            # No speaker yet, treat as first speaker "Unknown"
            current_speaker = "Unknown"
            current_text_lines.append(line)
    
    # Flush the last block
    flush_block()
    
    return blocks


def format_transcript_for_llm(blocks: List[SpeakerBlock]) -> str:
    """
    Format parsed transcript blocks into a text suitable for LLM input.
    
    Args:
        blocks: List of SpeakerBlock objects
        
    Returns:
        Formatted transcript string
    """
    lines = []
    for block in blocks:
        timestamp_str = f" [{block.timestamp}]" if block.timestamp else ""
        lines.append(f"**{block.speaker}**{timestamp_str}: {block.text}")
    return "\n\n".join(lines)


def summarize_with_llm(
    transcript: str,
    config: LLMConfig,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Send transcript to an LLM API for summarization.
    
    Uses OpenAI-compatible API format (works with OpenAI, Ollama, LM Studio, 
    and most internal APIs).
    
    Args:
        transcript: Formatted transcript text
        config: LLM API configuration
        progress_callback: Optional callback for status updates
        
    Returns:
        Generated summary text
    """
    if not config.is_configured():
        raise ValueError(
            "LLM API is not configured. Please set the API URL, API key, and model name."
        )
    
    if progress_callback:
        progress_callback("Connecting to LLM API...")
    
    try:
        import urllib.request
        import urllib.error
        
        # Build the request in OpenAI-compatible format
        payload = {
            "model": config.model_name,
            "messages": [
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": f"Here is the meeting transcript:\n\n{transcript}"},
            ],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        }
        
        # Ensure URL ends with /chat/completions
        api_url = config.api_url.rstrip("/")
        if not api_url.endswith("/chat/completions"):
            if not api_url.endswith("/v1"):
                api_url += "/v1"
            api_url += "/chat/completions"
        
        if progress_callback:
            progress_callback("Sending transcript to LLM...")
        
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
        
        if progress_callback:
            progress_callback("Processing response...")
        
        # Extract the response text
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return f"Unexpected API response format: {json.dumps(result, indent=2)}"
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        raise RuntimeError(f"LLM API error (HTTP {e.code}): {error_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot connect to LLM API: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"LLM API call failed: {e}")
