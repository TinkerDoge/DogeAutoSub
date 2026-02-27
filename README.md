# 🐕 DogeAutoSub — Automatic Subtitle Generation

**DogeAutoSub** is a GPU-accelerated desktop application for automatic subtitle generation, translation, and meeting note summarization. Built with PySide6 and powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2).

> **Current Version:** v2.0.6

---

## ✨ Features

### 📝 Subtitle Generation
- **GPU-accelerated transcription** using faster-whisper (CTranslate2) — 4x faster than OpenAI Whisper
- **Auto language detection** or manual source language selection
- **Word-level timestamps** for accurate subtitle segmentation
- **Built-in VAD** (Voice Activity Detection) to skip silence
- **Smart segment splitting** — respects sentence boundaries and subtitle length limits

### 🌐 Translation Engines
- **MLAAS** — Internal Virtuos ML-as-a-Service API (fastest, supports GPT-4o backend)
- **Google Translate** — Online fallback via deep-translator
- **MarianMT** — Fully offline translation (50+ language pairs via HuggingFace Transformers)
- **Whisper** — Built-in English-only translation

### 📋 Meeting Notes
- Upload `.docx` meeting transcripts (Teams/Zoom)
- AI-powered summarization via MLAAS API
- Edit and save generated notes

### 🌐 File Translation
- Translate existing `.srt`, `.docx`, or `.txt` files
- Supports all translation engines
- Standalone tab — no video processing required

### 🔄 Auto-Updater
- Delta patching over LAN — only changed files are downloaded
- SHA-256 hash verification for file integrity
- Automatic restart after update
- Configurable update server URL via `updater_config.json`

### 🎨 User Interface
- Modern tabbed UI (Subtitles / Meeting Notes / Translate)
- Dark and Light theme support with CSS stylesheets
- Real-time progress tracking with ETA
- Audio volume boost slider

---

## 💻 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 (64-bit) | Windows 11 (64-bit) |
| RAM | 4 GB | 8 GB+ |
| GPU | — | NVIDIA with CUDA support |
| VRAM | — | 6 GB+ (for large-v3-turbo) |
| Python | 3.11 | 3.11 |

---

## 🚀 Quick Start

### Option 1: Pre-built Executable
1. Download `DogeAutoSub.zip` from your team's distribution
2. Extract and run `DogeAutoSub.exe`

### Option 2: Run from Source
```bash
# Clone and setup
git clone <repo-url>
cd DogeAutoSub
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python AutoUI.py
```

---

## 📖 Usage

### Subtitle Generation
1. Click **🎬 Select Video File** — supports MP4, AVI, MKV, MOV, and other common formats
2. (Optional) Click **📁 Output Folder** to choose output location
3. Configure **Source Language** (Auto or specific) and **Target Language**
4. Select **Translation Engine** (MLAAS recommended)
5. If using MLAAS, paste your **Bearer token** (get one from the 🔗 Get Token button)
6. Click **▶ START PROCESSING**
7. Output: `filename.srt` (original) + `filename_vi.srt` (translated)

### Meeting Notes
1. Switch to the **📋 Meeting Notes** tab
2. Upload a `.docx` transcript from Teams or Zoom
3. Click **✨ Generate Meeting Notes**
4. Edit the output as needed, then **💾 Save**

### File Translation
1. Switch to the **🌐 Translate** tab
2. Upload an `.srt`, `.docx`, or `.txt` file
3. Select source/target languages and engine
4. Click **🌐 Translate File**

---

## 🔧 Building the Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build (uses DogeAutoSubApp.spec)
python -m PyInstaller DogeAutoSubApp.spec --noconfirm

# Or use the build script
build.bat
```

> **Note:** Application modules are excluded from the PYZ archive in the `.spec` file to support the auto-updater's delta patching. They exist only as `.py` data files in `_internal/`.

---

## 🔄 Update Server

Host updates for LAN deployment:

```bash
# Generate a release manifest
python serve_updates.py --generate <version> --notes "Release notes"

# Serve updates on port 8100
python serve_updates.py --serve
```

The update server provides:
- `version.json` — manifest with version, file hashes, and release notes
- `files/` — individual files for delta patching
- `DogeAutoSub_v<version>.zip` — full zip for fresh installs

Configure the client's update URL in `modules/updater_config.json`:
```json
{
  "update_url": "http://<server-ip>:8100"
}
```

---

## 📁 Project Structure

```
DogeAutoSub/
├── AutoUI.py                    # Main application entry point
├── ui_DogeAutoSub.py            # UI layout (PySide6 widgets)
├── DogeAutoSubApp.spec          # PyInstaller build spec
├── build.bat                    # Build script
├── serve_updates.py             # Update server + manifest generator
├── requirements.txt             # Python dependencies
├── modules/
│   ├── updater.py               # Auto-update client (version, download, restart)
│   ├── faster_whisper_engine.py  # GPU transcription engine (CTranslate2)
│   ├── chunk_processor.py       # Parallel audio chunk processing
│   ├── mlaas_client.py          # MLAAS API client (translate + summarize)
│   ├── marian_translator.py     # Offline MarianMT translation
│   ├── meeting_notes.py         # Meeting note generation
│   ├── constants.py             # Model info, language codes
│   ├── subtitle_args.py         # Subtitle parameter dataclass
│   ├── updater_config.json      # Update server URL config
│   ├── styleSheetDark.css       # Dark theme
│   ├── styleSheetLight.css      # Light theme
│   ├── ffmpeg/                  # Bundled FFmpeg binaries
│   └── models/                  # Pre-downloaded Whisper models
├── icons/                       # App icons and assets
├── releases/                    # Generated release files
│   ├── version.json             # Release manifest
│   └── files/                   # Release file copies
└── DOCs/                        # API reference documentation
    ├── taskTranslate.MD         # MLAAS translation API reference
    ├── taskSumarize.MD          # MLAAS summarization API reference
    └── taskAnthropicMessage.MD  # MLAAS Anthropic proxy API reference
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **GPU not detected** | Install CUDA toolkit compatible with your GPU. Verify with `torch.cuda.is_available()` |
| **Model download fails** | Check internet connection. Models are cached in `modules/models/` |
| **MLAAS translation fails** | Token expires every ~2 hours. Click 🔗 Get Token for a fresh one |
| **Empty subtitles** | Check audio quality. Try increasing Volume Boost. Verify language settings |
| **Update not applying** | Ensure the exe was built with the updated `.spec` that strips app modules from PYZ |
| **Network path issues** | Use UNC paths (`\\server\share\...`). Ensure proper permissions |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2-powered Whisper
- [PySide6](https://www.qt.io/) — Qt for Python GUI framework
- [Transformers](https://huggingface.co/docs/transformers) — MarianMT offline translation
- [deep-translator](https://github.com/nidhaloff/deep-translator) — Google Translate integration
- [FFmpeg](https://ffmpeg.org/) — Audio extraction