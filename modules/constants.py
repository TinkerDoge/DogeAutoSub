
LANGUAGE_CODES = {
    'en-US': 'English (US)',
    'en-GB': 'English (UK)',
    'es-ES': 'Spanish (Spain)',
    'fr-FR': 'French',
    'de-DE': 'German',
    'it-IT': 'Italian',
    'cmn-Hans-CN': 'Chinese (Mandarin)',
    'zh-CN': 'Chinese (Simplified)',
    'ja-JP': 'Japanese',
    'ko-KR': 'Korean',
    'vi-VN': 'Vietnamese',
}

MODEL_INFO = {
    "tiny": {"vram": "1 GB", "speed": "10x"},
    "base": {"vram": "1 GB", "speed": "7x"},
    "small": {"vram": "2 GB", "speed": "4x"},
    "medium": {"vram": "5 GB", "speed": "2x"},
    "large": {"vram": "10 GB", "speed": "1x"},
    "turbo": {"vram": "6 GB", "speed": "8x"}
}

TIMEEST = {
    "tiny": 0.37,
    "base": 0.44,
    "small": 0.88,
    "medium": 2.31,
    "turbo": 2.13,
    "large": 4.62
}

    # Base weights for the model (excluding translate)
BASE_WEIGHTS = {
        "tiny": 0.25,
        "base": 0.35,
        "small": 0.70,
        "medium": 2.00,
        "turbo": 1.80,
        "large": 4.62
    }
    
    # Additional weights for the translate task
TRANSLATE_WEIGHTS = {
        "tiny": 0.12,
        "base": 0.09,
        "small": 0.18,
        "medium": 0.30,
        "turbo": 0.25,
        "large": 4.62
    }

LANGUAGETRANS = {
    'English': 'en',
    'Thai': 'th',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'it-IT': 'it',
    'Chinese': 'zh',  # Simplified Chinese
    'Japanese': 'ja',        # Japanese
    'Korean': 'ko',        # Korean
    'Vietnamese': 'vi',    # Vietnamese
    'Russian': 'ru',

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

MODEL_TYPES = ["tiny", "base", "small", "medium", "large"]

TASK_TYPES = ["transcribe", "translate"]