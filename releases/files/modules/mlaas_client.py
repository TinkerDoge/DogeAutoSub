# v2.1.2 - Hardcoded obfuscated API key, x-api-key auth header, batched translation
"""
MLAAS API Client for DogeAutoSub.
Integrates with the internal Virtuos MLAAS platform for:
  - Text Translation: POST /proxy/anthropic/v1/messages (Claude Sonnet — cost-efficient)
  - Text Summarization: POST /proxy/anthropic/v1/messages (Claude Sonnet — high quality)

Auth: x-api-key header with embedded API key (obfuscated).
"""

import base64
import json
import os
import re
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Callable, List, Optional


# ── API Configuration ───────────────────────────────────────────

MLAAS_BASE_URL = "https://mlaas.virtuosgames.com"
MLAAS_APP_NAME = "DogeAutoSub"

# Model tiers — use the cheapest model that does the job well
ANTHROPIC_MODEL_TRANSLATION = "claude-sonnet-4-20250514"   # Fast, cheap, great at translation
ANTHROPIC_MODEL_SUMMARIZATION = "claude-sonnet-4-20250514"  # Quality summarization

# Batching config
TRANSLATION_BATCH_SIZE = 10  # Segments per API call

# ── Embedded API Key (obfuscated) ───────────────────────────────
# The key is base64-encoded to prevent casual reading in source code.
# It is decoded at runtime when needed.
_OBFUSCATED_KEY = "b2RfaWRaNjJsYTRsY1RjSDJWcTFDdUNUSWtHRnh6bFhzNExVVUFTQkJ1MA=="


def _decode_key() -> str:
    """Decode the embedded API key at runtime."""
    try:
        return base64.b64decode(_OBFUSCATED_KEY).decode("utf-8")
    except Exception:
        return ""


def get_api_key() -> str:
    """
    Get the MLAAS API key.
    
    Priority:
      1. .env file override (MLAAS_API) — for development/testing
      2. Embedded obfuscated key — for production use
    """
    # Check .env override first
    env_key = _load_env_key()
    if env_key:
        return env_key
    # Fall back to embedded key
    return _decode_key()


def _load_env_key() -> str:
    """Try to load API key from .env file (optional override)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root, ".env")
    
    if not os.path.exists(env_path):
        return ""
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("MLAAS_API") and "=" in line:
                    _, _, value = line.partition("=")
                    return value.strip().strip("'\"")
    except Exception:
        pass
    return ""


def get_masked_key(api_key: str) -> str:
    """Return a masked version of the API key for display (e.g. 'od_id...BBu0')."""
    if not api_key:
        return ""
    if len(api_key) <= 10:
        return "*" * len(api_key)
    return f"{api_key[:5]}...{api_key[-4:]}"


@dataclass
class MLAASConfig:
    """Configuration for MLAAS API connection.
    
    Auth: x-api-key header with embedded/obfuscated API key.
    """
    api_key: str = ""
    base_url: str = MLAAS_BASE_URL

    def is_configured(self) -> bool:
        return bool(self.api_key.strip())

    @classmethod
    def from_env(cls) -> "MLAASConfig":
        """Create config with the embedded API key (or .env override)."""
        return cls(api_key=get_api_key())


# ── API Calls ───────────────────────────────────────────────────

def _mlaas_request(endpoint: str, payload: dict, config: MLAASConfig, timeout: int = 120) -> dict:
    """Make a POST request to MLAAS API using x-api-key auth."""
    if not config.is_configured():
        raise ValueError(
            "MLAAS API key not available. Contact the app developer."
        )

    url = f"{config.base_url.rstrip('/')}{endpoint}"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": config.api_key,
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
                "Authentication failed (401). The API key may be invalid or expired."
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
    """Translate a single text string using Claude Sonnet via MLAAS."""
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
    """Translate a batch of numbered texts in a single API call."""
    target_lang_name = MLAAS_LANGUAGE_MAP.get(target_language.lower(), target_language.lower())

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

    translations = _parse_numbered_response(response_text, len(texts))

    if len(translations) != len(texts):
        print(f"Warning: Expected {len(texts)} translations, got {len(translations)}. Padding with originals.")
        while len(translations) < len(texts):
            translations.append(texts[len(translations)])

    return translations


def _parse_numbered_response(response: str, expected_count: int) -> List[str]:
    """Parse [N] numbered response back into a list."""
    results = {}

    pattern = re.compile(r"\[(\d+)\]\s*(.+?)(?=\n\[\d+\]|\Z)", re.DOTALL)
    matches = pattern.findall(response)

    if matches:
        for num_str, text in matches:
            idx = int(num_str) - 1
            if 0 <= idx < expected_count:
                results[idx] = text.strip()

    if len(results) < expected_count:
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        for i, line in enumerate(lines):
            if i >= expected_count:
                break
            cleaned = re.sub(r"^\[\d+\]\s*", "", line).strip()
            if cleaned and i not in results:
                results[i] = cleaned

    return [results.get(i, "") for i in range(max(len(results), 0))]


def translate_segments_mlaas(
    segments: list,
    target_language: str,
    config: MLAASConfig,
    progress_callback: Optional[Callable[[int], None]] = None,
    batch_size: int = TRANSLATION_BATCH_SIZE,
) -> list:
    """Translate subtitle segments using batched MLAAS calls."""
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

        texts = []
        text_indices = []

        for i, seg in enumerate(batch_segs):
            text = seg.get("text", "").strip()
            if text:
                texts.append(text)
                text_indices.append(i)

        translations = []
        if texts:
            try:
                translations = _translate_batch_mlaas(texts, target_language, config)
            except Exception as e:
                print(f"MLAAS batch translate error (batch {batch_idx + 1}): {e}")
                translations = texts

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

        if progress_callback and total > 0:
            progress_callback(int((end / total) * 100))

    return translated


# ── Summarization ───────────────────────────────────────────────

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
    """Summarize text using Claude Sonnet via MLAAS Anthropic proxy."""
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
