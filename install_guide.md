# DogeAutoSub Installation Guide

## End-Users — Pre-built install (recommended)

You don't need Python. You just need the LAN update server reachable from your PC.

1. Make sure someone on the LAN is running `python serve_updates.py` on the host machine (default `http://dogeautosub.local:8100`).
2. Download `Install_DogeAutoSub.bat` from this repo (or copy it from a teammate's machine).
3. Double-click it. The script will:
   - Probe the update server and read the latest version.
   - Download the full bundle `DogeAutoSub_v<ver>_full.zip`.
   - Extract it to `%USERPROFILE%\DogeAutoSub`.
   - Optionally place a desktop shortcut.
   - Optionally launch the app.

To override the server or install dir, run from a command prompt:
```
Install_DogeAutoSub.bat http://192.168.1.50:8100  D:\Apps\DogeAutoSub
```

After install, future updates happen in-app via the auto-updater — you don't need to re-run the installer.

---

## Developers — Run from source

### Prerequisites
- Python 3.11
- FFmpeg (included in the project under modules/ffmpeg/)

## Installation Options

### Option 1: Basic Installation
```bash
pip install -r requirements.txt
```

### Option 2: Full Installation (with MarianMT)
```bash
pip install -r requirements-full.txt
```

### Option 3: Minimal Installation
```bash
pip install -r requirements-minimal.txt
```

## GPU Support (Optional)
For CUDA support, visit [PyTorch Installation](https://pytorch.org/get-started/locally/) and install the appropriate CUDA version for your GPU.

Example for CUDA 11.8:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Troubleshooting
- If you encounter issues with transformers, ensure Python 3.8+ is installed
- For audio processing issues, verify FFmpeg is properly configured
- For translation issues, check your internet connection (for Google Translate)
