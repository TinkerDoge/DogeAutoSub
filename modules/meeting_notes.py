"""
Meeting Notes module for DogeAutoSub.
Parses meeting transcripts (DOCX/TXT/SRT/VTT) into speaker blocks. Summarization
is handled by `summarize_text_mlaas` in modules.mlaas_client.
"""

import os
import re
from dataclasses import dataclass
from typing import List


@dataclass
class SpeakerBlock:
    """A single block of speech from a meeting transcript."""
    speaker: str
    text: str
    timestamp: str = ""


def parse_meeting_transcript(file_path: str) -> List[SpeakerBlock]:
    """
    Parse a meeting transcript file into speaker blocks.
    Dispatches to the correct parser based on file extension.

    Supported formats: .docx, .txt, .srt, .sub, .vtt

    Args:
        file_path: Path to the transcript file

    Returns:
        List of SpeakerBlock objects
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".docx":
        return _parse_docx(file_path)
    elif ext == ".txt":
        return _parse_text(file_path)
    elif ext in (".srt", ".sub", ".vtt"):
        return _parse_subtitle(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# keep old name as alias for backwards compatibility
parse_meeting_docx = parse_meeting_transcript


def _parse_text(file_path: str) -> List[SpeakerBlock]:
    """Parse a plain-text transcript into speaker blocks."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Reuse the same speaker-detection patterns as the DOCX parser
    teams_pattern = re.compile(r'^(.+?)\s{2,}(\d{1,2}:\d{2}(?::\d{2})?)\s*$')
    zoom_pattern = re.compile(r'^(.+?)(?:\s*\((\d{1,2}:\d{2}(?::\d{2})?)\))?\s*:\s*$')
    generic_pattern = re.compile(r'^([A-Z][a-zA-Z\s\.]+?):\s+(.+)$')

    blocks: List[SpeakerBlock] = []
    current_speaker = ""
    current_timestamp = ""
    current_text_lines: List[str] = []

    def flush_block():
        nonlocal current_speaker, current_timestamp, current_text_lines
        if current_speaker and current_text_lines:
            text = " ".join(l.strip() for l in current_text_lines if l.strip())
            if text:
                blocks.append(SpeakerBlock(
                    speaker=current_speaker.strip(),
                    text=text,
                    timestamp=current_timestamp,
                ))
        current_text_lines = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        teams_match = teams_pattern.match(line)
        if teams_match:
            flush_block()
            current_speaker = teams_match.group(1).strip()
            current_timestamp = teams_match.group(2).strip()
            continue

        zoom_match = zoom_pattern.match(line)
        if zoom_match:
            flush_block()
            current_speaker = zoom_match.group(1).strip()
            current_timestamp = zoom_match.group(2) or ""
            continue

        generic_match = generic_pattern.match(line)
        if generic_match and not current_speaker:
            flush_block()
            current_speaker = generic_match.group(1).strip()
            current_text_lines.append(generic_match.group(2))
            continue

        if current_speaker:
            current_text_lines.append(line)
        else:
            current_speaker = "Unknown"
            current_text_lines.append(line)

    flush_block()
    return blocks


def _parse_subtitle(file_path: str) -> List[SpeakerBlock]:
    """Parse SRT / SUB / VTT subtitle files into speaker blocks."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Strip VTT header if present
    content = re.sub(r'^WEBVTT[^\n]*\n', '', content, flags=re.MULTILINE)

    # Match subtitle cue blocks:
    #   optional index line, timestamp line, then text lines
    cue_re = re.compile(
        r'(?:^\d+\s*\n)?'
        r'(\d{1,2}[:\.]\d{2}[:\.]\d{2}[,\.]\d{2,3})\s*-->\s*'
        r'(\d{1,2}[:\.]\d{2}[:\.]\d{2}[,\.]\d{2,3})\s*\n'
        r'((?:(?!\n\n|\n\d+\s*\n|\n\d{1,2}[:\.]\d{2}).+\n?)+)',
        re.MULTILINE,
    )

    blocks: List[SpeakerBlock] = []
    speaker_tag_re = re.compile(r'^<v\s+([^>]+)>(.*)$')  # VTT voice tag
    speaker_colon_re = re.compile(r'^([A-Z][a-zA-Z\s\.]+?):\s+(.+)$')

    for m in cue_re.finditer(content):
        timestamp = m.group(1).replace('.', ':')
        text_block = m.group(3).strip()
        # Remove HTML-style tags except voice tags handled above
        clean_lines = []
        speaker = "Speaker"
        for line in text_block.splitlines():
            line = line.strip()
            vtag = speaker_tag_re.match(line)
            if vtag:
                speaker = vtag.group(1).strip()
                line = vtag.group(2).strip()
            else:
                sc = speaker_colon_re.match(line)
                if sc:
                    speaker = sc.group(1).strip()
                    line = sc.group(2).strip()
            # strip remaining HTML tags
            line = re.sub(r'<[^>]+>', '', line).strip()
            if line:
                clean_lines.append(line)

        text = " ".join(clean_lines)
        if text:
            blocks.append(SpeakerBlock(speaker=speaker, text=text, timestamp=timestamp))

    return blocks


def _parse_docx(file_path: str) -> List[SpeakerBlock]:
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


