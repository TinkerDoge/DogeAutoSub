MODEL_INFO = {
    "tiny": {"vram": "39 MB", "speed": "~150x"},      # faster-whisper benchmarks
    "base": {"vram": "74 MB", "speed": "~80x"},
    "small": {"vram": "244 MB", "speed": "~40x"},
    "medium": {"vram": "769 MB", "speed": "~20x"},
    "large": {"vram": "1550 MB", "speed": "~8x"},
    "large-v3": {"vram": "1550 MB", "speed": "~8x"},
    "turbo": {"vram": "809 MB", "speed": "~16x"},
    "distil-large-v3": {"vram": "756 MB", "speed": "~25x"},  # Distil model
}



LANGUAGE_CODES_AI = [
    ("auto", "Auto"),
    ("en", "English"),
    ("zh", "Chinese"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("de", "German"),
    ("es", "Spanish"),
    ("ru", "Russian"),
    ("fr", "French"),
    ("pt", "Portuguese"),
    ("tr", "Turkish"),
    ("pl", "Polish"),
    ("ca", "Catalan"),
    ("nl", "Dutch"),
    ("ar", "Arabic"),
    ("sv", "Swedish"),
    ("it", "Italian"),
    ("id", "Indonesian"),
    ("hi", "Hindi"),
    ("fi", "Finnish"),
    ("vi", "Vietnamese"),
    ("iw", "Hebrew"),
    ("uk", "Ukrainian"),
    ("el", "Greek"),
    ("ms", "Malay"),
    ("cs", "Czech"),
    ("ro", "Romanian"),
    ("da", "Danish"),
    ("hu", "Hungarian"),
    ("ta", "Tamil"),
    ("no", "Norwegian"),
    ("th", "Thai"),
    ("ur", "Urdu"),
    ("hr", "Croatian"),
    ("bg", "Bulgarian"),
    ("lt", "Lithuanian"),
    ("la", "Latin"),
    ("mi", "Maori"),
    ("ml", "Malayalam"),
    ("cy", "Welsh"),
    ("sk", "Slovak"),
    ("te", "Telugu"),
    ("fa", "Persian"),
    ("lv", "Latvian"),
    ("bn", "Bengali"),
    ("sr", "Serbian"),
    ("az", "Azerbaijani"),
    ("sl", "Slovenian"),
    ("kn", "Kannada"),
    ("et", "Estonian"),
    ("mk", "Macedonian"),
    ("br", "Breton"),
    ("eu", "Basque"),
    ("is", "Icelandic"),
    ("hy", "Armenian"),
    ("ne", "Nepali"),
    ("mn", "Mongolian"),
    ("bs", "Bosnian"),
    ("kk", "Kazakh"),
    ("sq", "Albanian"),
    ("sw", "Swahili"),
    ("gl", "Galician"),
    ("mr", "Marathi"),
    ("pa", "Punjabi"),
    ("si", "Sinhala"),
    ("km", "Khmer"),
    ("sn", "Shona"),
    ("yo", "Yoruba"),
    ("so", "Somali"),
    ("af", "Afrikaans"),
    ("oc", "Occitan"),
    ("ka", "Georgian"),
    ("be", "Belarusian"),
    ("tg", "Tajik"),
    ("sd", "Sindhi"),
    ("gu", "Gujarati"),
    ("am", "Amharic"),
    ("yi", "Yiddish"),
    ("lo", "Lao"),
    ("uz", "Uzbek"),
    ("fo", "Faroese"),
    ("ht", "Haitian Creole"),
    ("ps", "Pashto"),
    ("tk", "Turkmen"),
    ("nn", "Nynorsk"),
    ("mt", "Maltese"),
    ("sa", "Sanskrit"),
    ("lb", "Luxembourgish"),
    ("my", "Myanmar"),
    ("bo", "Tibetan"),
    ("tl", "Tagalog"),
    ("mg", "Malagasy"),
    ("as", "Assamese"),
    ("tt", "Tatar"),
    ("haw", "Hawaiian"),
    ("ln", "Lingala"),
    ("ha", "Hausa"),
    ("ba", "Bashkir"),
    ("jw", "Javanese"),
    ("su", "Sundanese"),
]

MODEL_TYPES = ["tiny", "base", "small", "medium", "large", "large-v3", "turbo", "distil-large-v3"]

# Translation engine definitions: (engine_key, display_name)
# engine_key is used internally by the backend; display_name is shown in the UI dropdown.
TRANSLATION_ENGINES = [
    ("claude-sonnet-4", "Claude Sonnet 4 (MLAAS)"),
    ("gpt-4o-mini", "GPT-4o Mini (OpenAI)"),
    ("google", "Google Translate"),
]

# Engines available only on the Subtitles tab (not Translate File tab)
TRANSLATION_ENGINES_SUBTITLE_ONLY = [
    ("whisper", "Whisper (English only)"),
]


# Display order for language dropdowns: priority languages first, then the
# rest alphabetical by display name. "auto" is excluded — it's added
# separately as the first item where appropriate.
_PRIORITY_LANGUAGES = ("English", "Vietnamese", "Chinese", "Japanese")


def language_codes_ordered():
    """Return LANGUAGE_CODES_AI without 'auto', priority-first then A→Z."""
    rest = [(code, name) for code, name in LANGUAGE_CODES_AI if code != "auto"]
    priority = []
    for prio_name in _PRIORITY_LANGUAGES:
        match = next((pair for pair in rest if pair[1] == prio_name), None)
        if match:
            priority.append(match)
            rest.remove(match)
    rest.sort(key=lambda pair: pair[1].lower())
    return priority + rest