"""
MLAAS API Client for DogeAutoSub.
Integrates with the internal Virtuos MLAAS platform for:
  - Text Translation: POST /task/text/translation
  - Text Summarization: POST /task/text/summary

Auth: Bearer token (two modes — builtin API key or user-provided temporary token).
"""

import json
import os
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Callable, List, Optional


# ── API Configuration ───────────────────────────────────────────

MLAAS_BASE_URL = "https://mlaas.virtuosgames.com"
MLAAS_DEFAULT_MODEL = "gpt4o"
MLAAS_APP_NAME = "DogeAutoSub"


@dataclass
class MLAASConfig:
    """Configuration for MLAAS API connection.
    
    Two auth modes:
      1. builtin_api_key: Long-term key stored in backend (when available)
      2. bearer_token: Temporary user-provided token (expires ~2h)
    
    The active token is resolved as: builtin_api_key if set, else bearer_token.
    """
    builtin_api_key: str = ""
    bearer_token: str = ""
    model_name: str = MLAAS_DEFAULT_MODEL
    base_url: str = MLAAS_BASE_URL

    @property
    def active_token(self) -> str:
        """Return the token to use — prefer builtin, fall back to bearer."""
        return self.builtin_api_key.strip() or self.bearer_token.strip()

    def is_configured(self) -> bool:
        return bool(self.active_token)

    def save_to_file(self, filepath: str):
        """Save config (excludes temporary bearer_token for security)."""
        data = {
            "builtin_api_key": self.builtin_api_key,
            "model_name": self.model_name,
            "base_url": self.base_url,
            # bearer_token is intentionally NOT saved — it's temporary
        }
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "MLAASConfig":
        if not os.path.exists(filepath):
            return cls()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        except Exception as e:
            print(f"Error loading MLAAS config: {e}")
            return cls()


# ── API Calls ───────────────────────────────────────────────────

def _extract_content(text: str) -> str:
    """Extract text from <content>...</content> tags if present."""
    match = re.search(r"<content>\s*(.*?)\s*</content>", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _mlaas_request(endpoint: str, payload: dict, config: MLAASConfig, timeout: int = 120) -> dict:
    """Make a POST request to MLAAS API."""
    if not config.is_configured():
        raise ValueError("MLAAS API not configured. Please provide an API key or Bearer token.")

    url = f"{config.base_url.rstrip('/')}{endpoint}"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {config.active_token}",
        "x-application-name": MLAAS_APP_NAME,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        if e.code == 401:
            raise RuntimeError(
                "Authentication failed (401). Your Bearer token may have expired.\n"
                "Please get a new token and re-enter it."
            )
        elif e.code == 429:
            raise RuntimeError("Rate limit exceeded (429). Please wait and try again.")
        else:
            detail = ""
            try:
                detail = json.loads(body).get("detail", body)
            except Exception:
                detail = body
            raise RuntimeError(f"MLAAS API error (HTTP {e.code}): {detail}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot connect to MLAAS API: {e.reason}")


# ── Translation ─────────────────────────────────────────────────

# Language name mapping for the MLAAS API
MLAAS_LANGUAGE_MAP = {
    "en": "english", "vi": "vietnamese", "zh": "chinese",
    "ja": "japanese", "ko": "korean", "fr": "french",
    "de": "german", "es": "spanish", "it": "italian",
    "pt": "portuguese", "ru": "russian", "ar": "arabic",
    "th": "thai", "id": "indonesian", "ms": "malay",
    "nl": "dutch", "pl": "polish", "sv": "swedish",
    "tr": "turkish", "hi": "hindi", "uk": "ukrainian",
}


def translate_text_mlaas(
    text: str,
    target_language: str,
    config: MLAASConfig,
) -> str:
    """
    Translate text using Claude via MLAAS Anthropic proxy.
    Includes instructions to fix transcription errors before translating.
    
    Args:
        text: Text to translate (may contain transcription errors)
        target_language: Language code (e.g. 'vi', 'en') or full name ('vietnamese')
        config: MLAAS API configuration
        
    Returns:
        Translated text string
    """
    target_lang_name = MLAAS_LANGUAGE_MAP.get(target_language.lower(), target_language.lower())

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Translate the following text to {target_lang_name}. "
                    "This text comes from automatic speech transcription and may contain errors "
                    "such as mishearings, incomplete words, or wrong punctuation. "
                    "First try to understand the intended meaning, correct any obvious transcription "
                    "mistakes, then translate naturally. "
                    "Return ONLY the translated text, nothing else.\n\n"
                    f"{text}"
                ),
            },
        ],
    }

    result = _mlaas_request("/proxy/anthropic/v1/messages", payload, config, timeout=30)

    # Parse Anthropic response
    content = result.get("content", [])
    if isinstance(content, list) and len(content) > 0:
        return content[0].get("text", "").strip()
    return result.get("text", text)


def translate_segments_mlaas(
    segments: list,
    target_language: str,
    config: MLAASConfig,
    progress_callback: Optional[Callable[[int], None]] = None,
    batch_size: int = 5,
) -> list:
    """
    Translate subtitle segments using MLAAS translation API.
    Sends segments individually for accurate per-segment translation.
    
    Args:
        segments: List of dicts with 'start', 'end', 'text' keys
        target_language: Target language code
        config: MLAAS API configuration
        progress_callback: Optional callback with progress percentage (0-100)
        batch_size: Not used for API calls, kept for interface compatibility
        
    Returns:
        List of translated segment dicts
    """
    translated = []
    total = len(segments)

    for i, seg in enumerate(segments):
        text = seg.get("text", "").strip()
        if not text:
            translated.append(seg)
        else:
            try:
                result = translate_text_mlaas(text, target_language, config)
                translated.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": result,
                })
            except Exception as e:
                print(f"MLAAS translate error for segment {i}: {e}")
                translated.append(seg)  # Keep original on error

        if progress_callback and total > 0:
            progress_callback(int(((i + 1) / total) * 100))

    return translated


# ── Summarization (via Anthropic-compatible proxy) ──────────────

ANTHROPIC_MODEL = "claude-opus-4-6"
MEETING_NOTES_SYSTEM_PROMPT = (
    "You are a professional meeting note-taker. Given a meeting transcript with speaker names "
    "and dialogue, produce structured call notes in the following exact format:\n\n"
    "1. Start with a one-line intro: 'Here is the call note style summary for the [date] [meeting type], "
    "including key discussion points and action items for follow-up:'\n"
    "2. '## Call Notes — [Date]' heading\n"
    "3. '### Attendees:' — bullet list of all speakers\n"
    "4. '### Key Discussion Points & Action Items:' — numbered bold topic titles, each with bullet sub-points "
    "summarizing what was discussed, decisions made, and any action items inline\n"
    "5. '### Follow-Up / Next Steps:' — bullet list of concrete action items with responsible persons\n"
    "Use markdown formatting with **bold** for topic titles. Keep each bullet concise but informative. "
    "Use horizontal rules (---) to separate major sections."
)


def summarize_text_mlaas(
    text: str,
    config: MLAASConfig,
    language: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Summarize text using the MLAAS Anthropic-compatible proxy (Claude).
    
    Endpoint: POST /proxy/anthropic/v1/messages
    
    Args:
        text: Text to summarize (meeting transcript)
        config: MLAAS API configuration (uses same Bearer token)
        language: Optional output language hint
        progress_callback: Optional status callback
        
    Returns:
        Summary text from Claude
    """
    if progress_callback:
        progress_callback("Sending to Claude for summarization…")

    lang_hint = f"\n\nPlease write the summary in {language}." if language else ""

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"{MEETING_NOTES_SYSTEM_PROMPT}{lang_hint}\n\n"
                    f"Here is the meeting transcript:\n\n{text}"
                ),
            },
        ],
    }

    result = _mlaas_request("/proxy/anthropic/v1/messages", payload, config, timeout=180)

    if progress_callback:
        progress_callback("Summary received from Claude ✓")

    # Parse Anthropic response format: { content: [{ text: "...", type: "text" }] }
    content = result.get("content", [])
    if isinstance(content, list) and len(content) > 0:
        return content[0].get("text", "")
    
    # Fallback: try plain text field
    return result.get("text", str(result))

