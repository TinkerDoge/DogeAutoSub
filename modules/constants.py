
MODEL_INFO = {
    "tiny": {"vram": "1 GB", "speed": "10x"},
    "base": {"vram": "1 GB", "speed": "7x"},
    "small": {"vram": "2 GB", "speed": "4x"},
    "medium": {"vram": "5 GB", "speed": "2x"},
    "large": {"vram": "10 GB", "speed": "1x"},
    "turbo": {"vram": "6 GB", "speed": "8x"}
}


TASK_WEIGHTS = {
    "base": {'extract_audio': 0.029447, 'load_model': 0.340212, 'transcribe': 0.073078, 'translate': 0.204338},
    "medium": {'extract_audio': 0.029447, 'load_model': 2.544401, 'transcribe': 0.210081, 'translate': 0.214918},
    "small": {'extract_audio': 0.029447, 'load_model': 0.860841, 'transcribe': 0.120865, 'translate': 0.178356},
    "tiny": {'extract_audio': 0.029447, 'load_model': 0.214486, 'transcribe': 0.059103, 'translate': 0.249711},
    "turbo": {'extract_audio': 0.029447, 'load_model': 2.528063, 'transcribe': 0.063907, 'translate': 0.222897},
    "large": {'extract_audio': 0.029447, 'load_model': 5.049726, 'transcribe': 0.264191, 'translate': 0.244318}
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