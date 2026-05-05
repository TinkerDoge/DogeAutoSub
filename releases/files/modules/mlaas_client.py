# v2.1.2 - Hardcoded obfuscated API key, x-api-key auth header, batched translation
"""
MLAAS API Client for DogeAutoSub.
Integrates with the internal Virtuos MLAAS platform for:
  - Text Translation: POST /proxy/anthropic/v1/messages (Claude Sonnet — cost-efficient)
  - Text Summarization: POST /proxy/anthropic/v1/messages (Claude Sonnet — high quality)

Auth: Bearer JWT (preferred, user-supplied, ~2hr expiry) or x-api-key (embedded, long-lived).
"""

import base64
import json
import os
import re
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Callable, List, Optional



# ── Model List Cache ────────────────────────────────────────────
_MLAAS_MODEL_LIST = []
_MLAAS_MODEL_LIST_LAST_ERROR = None
_MODEL_LIST_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlaas_models_cache.json")
_MODEL_LIST_CACHE_TTL = 86400  # 24h


def _write_model_list_cache(models: list) -> None:
    try:
        with open(_MODEL_LIST_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"fetched_at": time.time(), "models": models}, f)
    except Exception as e:
        print(f"Warning: could not write model list cache: {e}")


def load_cached_mlaas_model_list_from_disk(max_age_seconds: int = _MODEL_LIST_CACHE_TTL) -> list:
    """Populate the in-memory model list from disk cache if fresh. Returns the list (may be empty)."""
    global _MLAAS_MODEL_LIST
    if not os.path.exists(_MODEL_LIST_CACHE_PATH):
        return []
    try:
        with open(_MODEL_LIST_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        fetched_at = data.get("fetched_at", 0)
        models = data.get("models", [])
        if not isinstance(models, list):
            return []
        if max_age_seconds > 0 and (time.time() - fetched_at) > max_age_seconds:
            # Stale, but still better than nothing while we refetch in background
            _MLAAS_MODEL_LIST = models
            return models
        _MLAAS_MODEL_LIST = models
        return models
    except Exception as e:
        print(f"Warning: could not read model list cache: {e}")
        return []


def _bearer_token_config_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlaas_config.json")


def save_bearer_token(token: str):
    """Persist bearer token to mlaas_config.json for reuse within the session."""
    path = _bearer_token_config_path()
    try:
        data = {}
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
        data["bearer_token"] = token.strip()
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to save bearer token: {e}")


def load_bearer_token() -> str:
    """Load persisted bearer token from mlaas_config.json."""
    path = _bearer_token_config_path()
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            return data.get("bearer_token", "").strip()
    except Exception:
        pass
    return ""


def _auth_headers(config: 'MLAASConfig') -> dict:
    """Return the correct auth header dict based on config."""
    token = config.bearer_token.strip() if config.bearer_token else ""
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {"x-api-key": config.api_key}


def fetch_mlaas_model_list(config: 'MLAASConfig' = None) -> list:
    """Fetch available models from MLAAS and cache them (in-memory + disk)."""
    global _MLAAS_MODEL_LIST, _MLAAS_MODEL_LIST_LAST_ERROR
    config = config or MLAASConfig.from_env()
    url = f"{config.base_url.rstrip('/')}/proxy/openai/v1/models"
    headers = {
        "Accept": "application/json",
        "x-application-name": MLAAS_APP_NAME,
        **_auth_headers(config),
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            _MLAAS_MODEL_LIST = data.get("data", [])
            _MLAAS_MODEL_LIST_LAST_ERROR = None
            if _MLAAS_MODEL_LIST:
                _write_model_list_cache(_MLAAS_MODEL_LIST)
    except Exception as e:
        _MLAAS_MODEL_LIST_LAST_ERROR = str(e)
        # Don't clobber an existing in-memory cache on transient failure
    return _MLAAS_MODEL_LIST

def get_cached_mlaas_model_list() -> list:
    """Return the last cached MLAAS model list."""
    return _MLAAS_MODEL_LIST

def get_mlaas_model_list_error() -> str:
    """Return the last error from model list fetch, if any."""
    return _MLAAS_MODEL_LIST_LAST_ERROR

MLAAS_BASE_URL = "https://mlaas.virtuosgames.com"
MLAAS_APP_NAME = "DogeAutoSub"


# Model tiers — use the cheapest model that does the job well
ANTHROPIC_MODEL_TRANSLATION = "claude-sonnet-4-20250514"   # Default fallback if model list fetch fails
ANTHROPIC_MODEL_SUMMARIZATION = "claude-sonnet-4-20250514"
OPENAI_MODEL_TRANSLATION = "gpt-4o-mini"

# Batching config
TRANSLATION_BATCH_SIZE = 20  # Max segments per API call (adaptive packing may use fewer)
TRANSLATION_CHUNK_SIZE = 200  # Segments per translation chunk (resets context for long transcripts)
TRANSLATION_BATCH_CHAR_BUDGET = 4500  # Soft cap to avoid oversized prompts/timeouts

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

    Auth priority: bearer_token (user JWT, ~2hr expiry) > api_key (embedded, long-lived).
    """
    api_key: str = ""
    base_url: str = MLAAS_BASE_URL
    bearer_token: str = ""

    def is_configured(self) -> bool:
        return bool(self.api_key.strip() or self.bearer_token.strip())

    @classmethod
    def from_env(cls) -> "MLAASConfig":
        """Create config from embedded API key plus any persisted bearer token."""
        return cls(
            api_key=get_api_key(),
            bearer_token=load_bearer_token(),
        )


# ── API Calls ───────────────────────────────────────────────────

def _mlaas_request(endpoint: str, payload: dict, config: MLAASConfig, timeout: int = 120) -> dict:
    """Make a POST request to MLAAS API, preferring Bearer JWT then falling back to x-api-key."""
    if not config.is_configured():
        raise ValueError(
            "MLAAS not configured. Provide an API key or paste a Bearer token."
        )

    url = f"{config.base_url.rstrip('/')}{endpoint}"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-application-name": MLAAS_APP_NAME,
        **_auth_headers(config),
    }

    body_bytes = json.dumps(payload).encode("utf-8")
    max_429_retries = 2

    for attempt in range(max_429_retries + 1):
        req = urllib.request.Request(
            url,
            data=body_bytes,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            if e.code == 429 and attempt < max_429_retries:
                retry_after = e.headers.get("Retry-After") if e.headers else None
                try:
                    delay = float(retry_after) if retry_after else 2.0 * (attempt + 1)
                except (TypeError, ValueError):
                    delay = 2.0 * (attempt + 1)
                delay = min(max(delay, 1.0), 30.0)
                print(f"MLAAS 429 rate-limit hit, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_429_retries})")
                time.sleep(delay)
                continue
            if e.code == 401:
                if config.bearer_token.strip():
                    raise RuntimeError(
                        "Bearer token rejected (401). It may have expired — get a fresh one from mlaas.virtuosgames.com/auth/token"
                    )
                raise RuntimeError(
                    "Authentication failed (401). The API key may be invalid or expired."
                )
            elif e.code == 429:
                raise RuntimeError("Rate limit exceeded (429). Try using a personal Bearer token.")
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
        "temperature": 0.2,
        "system": [
            {
                "type": "text",
                "text": (
                    f"Translate the user's text to {target_lang_name}. "
                    "Return ONLY the translation, nothing else."
                ),
                "cache_control": {"type": "ephemeral"},
            },
        ],
        "messages": [
            {"role": "user", "content": text},
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
        "temperature": 0.2,
        "system": [
            {
                "type": "text",
                "text": (
                    f"Translate each numbered subtitle line to {target_lang_name}. "
                    "Return ONLY the translations in the same [N] format, one per line. "
                    "Preserve numbering exactly."
                ),
                "cache_control": {"type": "ephemeral"},
            },
        ],
        "messages": [
            {"role": "user", "content": numbered},
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


def _translate_batch_resilient(
    texts: List[str],
    target_language: str,
    config: MLAASConfig,
    max_split_depth: int = 3,
) -> List[str]:
    """
    Translate with fallback splitting on transient failures.
    This keeps normal request count low, and only increases calls when a large batch fails.
    """
    if not texts:
        return []

    try:
        return _translate_batch_mlaas(texts, target_language, config)
    except Exception as e:
        # If this is already a single item (or split depth exhausted), bubble up.
        if len(texts) <= 1 or max_split_depth <= 0:
            raise RuntimeError(f"MLAAS translate failed for batch size {len(texts)}: {e}")

        mid = len(texts) // 2
        left = _translate_batch_resilient(texts[:mid], target_language, config, max_split_depth - 1)
        right = _translate_batch_resilient(texts[mid:], target_language, config, max_split_depth - 1)
        return left + right


def _pack_text_batches(texts: List[str], max_items: int, char_budget: int) -> List[List[str]]:
    """Pack subtitle lines into larger requests while respecting a soft character budget."""
    if not texts:
        return []

    max_items = max(1, int(max_items))
    char_budget = max(300, int(char_budget))

    batches: List[List[str]] = []
    current: List[str] = []
    current_chars = 0

    for text in texts:
        item_chars = len(text)
        would_exceed_items = len(current) >= max_items
        would_exceed_chars = current and (current_chars + item_chars > char_budget)

        if would_exceed_items or would_exceed_chars:
            batches.append(current)
            current = []
            current_chars = 0

        current.append(text)
        current_chars += item_chars

    if current:
        batches.append(current)

    return batches


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

    return [results.get(i, "") for i in range(expected_count)]


def translate_segments_mlaas(
    segments: list,
    target_language: str,
    config: MLAASConfig,
    progress_callback: Optional[Callable[[int], None]] = None,
    batch_size: int = TRANSLATION_BATCH_SIZE,
    chunk_size: int = TRANSLATION_CHUNK_SIZE,
    batch_char_budget: int = TRANSLATION_BATCH_CHAR_BUDGET,
) -> list:
    """Translate subtitle segments using chunked + batched MLAAS calls."""
    total = len(segments)
    if total == 0:
        return []

    batch_size = max(1, int(batch_size))
    chunk_size = max(1, int(chunk_size))
    batch_char_budget = max(300, int(batch_char_budget))

    translated = []
    chunk_count = (total + chunk_size - 1) // chunk_size

    print(
        f"Translating {total} segments in {chunk_count} chunks "
        f"(chunk_size={chunk_size}, batch_size={batch_size})"
    )

    for chunk_idx in range(chunk_count):
        chunk_start = chunk_idx * chunk_size
        chunk_end = min(chunk_start + chunk_size, total)
        chunk_segs = segments[chunk_start:chunk_end]
        chunk_total = len(chunk_segs)
        chunk_batch_count = (chunk_total + batch_size - 1) // batch_size

        print(
            f"MLAAS chunk {chunk_idx + 1}/{chunk_count}: "
            f"segments {chunk_start + 1}-{chunk_end} in {chunk_batch_count} API calls"
        )

        for batch_idx in range(chunk_batch_count):
            start = batch_idx * batch_size
            end = min(start + batch_size, chunk_total)
            batch_segs = chunk_segs[start:end]

            texts = []
            text_indices = []
            for i, seg in enumerate(batch_segs):
                text = seg.get("text", "").strip()
                if text:
                    texts.append(text)
                    text_indices.append(i)

            translations = []
            if texts:
                packed = _pack_text_batches(texts, max_items=batch_size, char_budget=batch_char_budget)
                for pack_idx, pack in enumerate(packed):
                    try:
                        part = _translate_batch_resilient(pack, target_language, config)
                        translations.extend(part)
                    except Exception as e:
                        print(
                            f"MLAAS batch translate error "
                            f"(chunk {chunk_idx + 1}, batch {batch_idx + 1}, part {pack_idx + 1}): {e}"
                        )
                        translations.extend(pack)

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
                global_done = chunk_start + end
                progress_callback(int((global_done / total) * 100))

    return translated


# ── OpenAI Translation (via MLAAS proxy) ────────────────────────

def _parse_openai_response(result: dict) -> str:
    """Extract text from OpenAI Chat Completion response."""
    choices = result.get("choices", [])
    if isinstance(choices, list) and len(choices) > 0:
        msg = choices[0].get("message", {})
        return msg.get("content", "").strip()
    return ""


def translate_text_openai(
    text: str,
    target_language: str,
    config: MLAASConfig,
    model: Optional[str] = None,
) -> str:
    """Translate a single text string using GPT via MLAAS OpenAI proxy."""
    target_lang_name = MLAAS_LANGUAGE_MAP.get(target_language.lower(), target_language.lower())
    selected_model = model or OPENAI_MODEL_TRANSLATION

    payload = {
        "model": selected_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"Translate the user's text to {target_lang_name}. "
                    "Return ONLY the translation, nothing else."
                ),
            },
            {"role": "user", "content": text},
        ],
        "max_tokens": 1024,
        "temperature": 0.2,
    }

    result = _mlaas_request("/proxy/openai/v1/chat/completions", payload, config, timeout=30)
    return _parse_openai_response(result)


def _translate_batch_openai(
    texts: List[str],
    target_language: str,
    config: MLAASConfig,
    model: Optional[str] = None,
) -> List[str]:
    """Translate a batch of numbered texts in a single OpenAI API call."""
    target_lang_name = MLAAS_LANGUAGE_MAP.get(target_language.lower(), target_language.lower())
    selected_model = model or OPENAI_MODEL_TRANSLATION

    numbered = "\n".join(f"[{i+1}] {t}" for i, t in enumerate(texts))

    payload = {
        "model": selected_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"Translate each numbered subtitle line to {target_lang_name}. "
                    "Return ONLY the translations in the same [N] format, one per line. "
                    "Preserve numbering exactly."
                ),
            },
            {"role": "user", "content": numbered},
        ],
        "max_tokens": 2048,
        "temperature": 0.2,
    }

    result = _mlaas_request("/proxy/openai/v1/chat/completions", payload, config, timeout=60)
    response_text = _parse_openai_response(result)

    translations = _parse_numbered_response(response_text, len(texts))

    if len(translations) != len(texts):
        print(f"Warning: Expected {len(texts)} translations, got {len(translations)}. Padding with originals.")
        while len(translations) < len(texts):
            translations.append(texts[len(translations)])

    return translations


def _translate_batch_openai_resilient(
    texts: List[str],
    target_language: str,
    config: MLAASConfig,
    max_split_depth: int = 3,
    model: Optional[str] = None,
) -> List[str]:
    """Translate with fallback splitting on transient failures (OpenAI variant)."""
    if not texts:
        return []

    try:
        return _translate_batch_openai(texts, target_language, config, model=model)
    except Exception as e:
        if len(texts) <= 1 or max_split_depth <= 0:
            raise RuntimeError(f"OpenAI translate failed for batch size {len(texts)}: {e}")

        mid = len(texts) // 2
        left = _translate_batch_openai_resilient(texts[:mid], target_language, config, max_split_depth - 1, model=model)
        right = _translate_batch_openai_resilient(texts[mid:], target_language, config, max_split_depth - 1, model=model)
        return left + right


def translate_segments_openai(
    segments: list,
    target_language: str,
    config: MLAASConfig,
    progress_callback: Optional[Callable[[int], None]] = None,
    batch_size: int = TRANSLATION_BATCH_SIZE,
    chunk_size: int = TRANSLATION_CHUNK_SIZE,
    batch_char_budget: int = TRANSLATION_BATCH_CHAR_BUDGET,
    model: Optional[str] = None,
) -> list:
    """Translate subtitle segments using chunked + batched OpenAI calls via MLAAS."""
    total = len(segments)
    if total == 0:
        return []

    batch_size = max(1, int(batch_size))
    chunk_size = max(1, int(chunk_size))
    batch_char_budget = max(300, int(batch_char_budget))

    translated = []
    chunk_count = (total + chunk_size - 1) // chunk_size

    print(
        f"OpenAI translating {total} segments in {chunk_count} chunks "
        f"(chunk_size={chunk_size}, batch_size={batch_size})"
    )

    for chunk_idx in range(chunk_count):
        chunk_start = chunk_idx * chunk_size
        chunk_end = min(chunk_start + chunk_size, total)
        chunk_segs = segments[chunk_start:chunk_end]
        chunk_total = len(chunk_segs)
        chunk_batch_count = (chunk_total + batch_size - 1) // batch_size

        print(
            f"OpenAI chunk {chunk_idx + 1}/{chunk_count}: "
            f"segments {chunk_start + 1}-{chunk_end} in {chunk_batch_count} API calls"
        )

        for batch_idx in range(chunk_batch_count):
            start = batch_idx * batch_size
            end = min(start + batch_size, chunk_total)
            batch_segs = chunk_segs[start:end]

            texts = []
            text_indices = []
            for i, seg in enumerate(batch_segs):
                text = seg.get("text", "").strip()
                if text:
                    texts.append(text)
                    text_indices.append(i)

            translations = []
            if texts:
                packed = _pack_text_batches(texts, max_items=batch_size, char_budget=batch_char_budget)
                for pack_idx, pack in enumerate(packed):
                    try:
                        part = _translate_batch_openai_resilient(pack, target_language, config, model=model)
                        translations.extend(part)
                    except Exception as e:
                        print(
                            f"OpenAI batch translate error "
                            f"(chunk {chunk_idx + 1}, batch {batch_idx + 1}, part {pack_idx + 1}): {e}"
                        )
                        translations.extend(pack)

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
                global_done = chunk_start + end
                progress_callback(int((global_done / total) * 100))

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

    system_text = MEETING_NOTES_SYSTEM_PROMPT
    if language:
        system_text = f"{system_text}\n\nWrite the summary in {language}."

    payload = {
        "model": ANTHROPIC_MODEL_SUMMARIZATION,
        "max_tokens": 4096,
        "system": [
            {
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral"},
            },
        ],
        "messages": [
            {
                "role": "user",
                "content": f"Here is the meeting transcript:\n\n{text}",
            },
        ],
    }

    result = _mlaas_request("/proxy/anthropic/v1/messages", payload, config, timeout=180)

    if progress_callback:
        progress_callback("Summary received from Claude ✓")

    return _parse_anthropic_response(result)
