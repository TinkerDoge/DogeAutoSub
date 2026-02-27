# DogeAutoSub Installation Guide

## Prerequisites
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
