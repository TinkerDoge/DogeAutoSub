# v2.1.1 - Batched translation, Sonnet for translation / Opus for summarization
"""
MLAAS API Client for DogeAutoSub.
Integrates with the internal Virtuos MLAAS platform for:
  - Text Translation: POST /proxy/anthropic/v1/messages (Claude Sonnet — cost-efficient)
  - Text Summarization: POST /proxy/anthropic/v1/messages (Claude Opus — high quality)

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
MLAAS_APP_NAME = "DogeAutoSub"

# Model tiers — use the cheapest model that does the job well
ANTHROPIC_MODEL_TRANSLATION = "claude-sonnet-4-20250514"   # Fast, cheap, great at translation
ANTHROPIC_MODEL_SUMMARIZATION = "claude-sonnet-4-20250514"  # Quality summarization

# Batching config
TRANSLATION_BATCH_SIZE = 10  # Segments per API call


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
    model_name: str = ""  # Kept for config compat, not used directly
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


def _parse_anthropic_response(result: dict) -> str:
    """Extract text from Anthropic API response."""
    content = result.get("content", [])
    if isinstance(content, list) and len(content) > 0:
        return content[0].get("text", "").strip()
    return result.get("text", "").strip()


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
    Translate a single text string using Claude Sonnet via MLAAS.
    Used by the file translation tab for individual lines.
    """
    target_lang_name = MLAAS_LANGUAGE_MAP.get(target_language.lower(), target_language.lower())

    payload = {
        "model": ANTHROPIC_MODEL_TRANSLATION,
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Translate to {target_lang_name}. "
                    "Fix any obvious speech-to-text errors before translating. "
                    "Return ONLY the translation, nothing else.\n\n"
                    f"{text}"
                ),
            },
        ],
    }

    result = _mlaas_request("/proxy/anthropic/v1/messages", payload, config, timeout=30)
    return _parse_anthropic_response(result)


def _translate_batch_mlaas(
    texts: List[str],
    target_language: str,
    config: MLAASConfig,
) -> List[str]:
    """
    Translate a batch of numbered texts in a single API call.
    
    Sends texts as a numbered list, asks Claude to return translations
    in the same numbered format, then parses them back out.
    
    Args:
        texts: List of text strings to translate (max ~10 recommended)
        target_language: Target language code or name
        config: MLAAS API config
        
    Returns:
        List of translated strings (same length as input)
    """
    target_lang_name = MLAAS_LANGUAGE_MAP.get(target_language.lower(), target_language.lower())
    
    # Build numbered input
    numbered = "\n".join(f"[{i+1}] {t}" for i, t in enumerate(texts))
    
    payload = {
        "model": ANTHROPIC_MODEL_TRANSLATION,
        "max_tokens": 2048,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Translate each numbered line to {target_lang_name}. "
                    "These are subtitle lines from speech-to-text — fix obvious transcription errors. "
                    "Return ONLY the translations in the same [N] format, one per line.\n\n"
                    f"{numbered}"
                ),
            },
        ],
    }

    result = _mlaas_request("/proxy/anthropic/v1/messages", payload, config, timeout=60)
    response_text = _parse_anthropic_response(result)
    
    # Parse numbered response back into list
    translations = _parse_numbered_response(response_text, len(texts))
    
    # If parsing failed or count mismatch, fall back to returning what we got
    if len(translations) != len(texts):
        print(f"Warning: Expected {len(texts)} translations, got {len(translations)}. Padding with originals.")
        while len(translations) < len(texts):
            translations.append(texts[len(translations)])
    
    return translations


def _parse_numbered_response(response: str, expected_count: int) -> List[str]:
    """
    Parse a numbered response like:
      [1] translated text one
      [2] translated text two
    
    Returns list of translated texts.
    """
    results = {}
    
    # Try to match [N] patterns
    pattern = re.compile(r"\[(\d+)\]\s*(.+?)(?=\n\[\d+\]|\Z)", re.DOTALL)
    matches = pattern.findall(response)
    
    if matches:
        for num_str, text in matches:
            idx = int(num_str) - 1  # Convert to 0-based
            if 0 <= idx < expected_count:
                results[idx] = text.strip()
    
    # If regex didn't work well, try line-by-line splitting
    if len(results) < expected_count:
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        for i, line in enumerate(lines):
            if i >= expected_count:
                break
            # Strip leading [N] if present
            cleaned = re.sub(r"^\[\d+\]\s*", "", line).strip()
            if cleaned and i not in results:
                results[i] = cleaned
    
    # Build ordered list
    return [results.get(i, "") for i in range(max(len(results), 0))]


def translate_segments_mlaas(
    segments: list,
    target_language: str,
    config: MLAASConfig,
    progress_callback: Optional[Callable[[int], None]] = None,
    batch_size: int = TRANSLATION_BATCH_SIZE,
) -> list:
    """
    Translate subtitle segments using batched MLAAS calls.
    
    Batches segments (default 10 per call) to reduce API costs and latency.
    For a 174-segment video, this makes ~18 calls instead of 174.
    
    Args:
        segments: List of dicts with 'start', 'end', 'text' keys
        target_language: Target language code
        config: MLAAS API configuration
        progress_callback: Optional callback with progress percentage (0-100)
        batch_size: Number of segments per API call (default: 10)
        
    Returns:
        List of translated segment dicts
    """
    total = len(segments)
    if total == 0:
        return []
    
    translated = []
    batch_count = (total + batch_size - 1) // batch_size
    
    print(f"Translating {total} segments in {batch_count} batched API calls (batch_size={batch_size})")
    
    for batch_idx in range(batch_count):
        start = batch_idx * batch_size
        end = min(start + batch_size, total)
        batch_segs = segments[start:end]
        
        # Collect non-empty texts for translation
        texts = []
        text_indices = []  # Track which segments have text
        
        for i, seg in enumerate(batch_segs):
            text = seg.get("text", "").strip()
            if text:
                texts.append(text)
                text_indices.append(i)
        
        # Translate the batch
        translations = []
        if texts:
            try:
                translations = _translate_batch_mlaas(texts, target_language, config)
            except Exception as e:
                print(f"MLAAS batch translate error (batch {batch_idx + 1}): {e}")
                translations = texts  # Fall back to originals
        
        # Rebuild segments with translations
        trans_idx = 0
        for i, seg in enumerate(batch_segs):
            if i in text_indices and trans_idx < len(translations):
                translated.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": translations[trans_idx],
                })
                trans_idx += 1
            else:
                translated.append(seg)
        
        # Report progress
        if progress_callback and total > 0:
            progress_callback(int((end / total) * 100))
    
    return translated


# ── Summarization (via Anthropic-compatible proxy) ──────────────

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
    Summarize text using Claude via MLAAS Anthropic proxy.
    
    Uses Sonnet for cost efficiency — still produces high-quality meeting notes.
    
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
        "model": ANTHROPIC_MODEL_SUMMARIZATION,
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

    return _parse_anthropic_response(result)
