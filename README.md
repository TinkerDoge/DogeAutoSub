# DogeAutoSub - Automatic Subtitle Generation

DogeAutoSub is a powerful desktop application that automatically generates subtitles for video files using OpenAI's Whisper model and provides translation capabilities through multiple engines.

## Features

- **Automatic Speech Recognition**: Uses OpenAI Whisper for high-quality transcription
- **Multiple Model Sizes**: Support for tiny, base, small, medium, and large models
- **Multi-language Support**: Auto-detect language or specify source language
- **Translation Engines**: 
  - Google Translate (online)
  - MarianMT (offline)
  - Whisper (built-in)
- **GPU Acceleration**: CUDA support for faster processing
- **User-friendly GUI**: Dark/Light theme support
- **Progress Tracking**: Real-time progress and time estimation

## System Requirements

- Windows 10/11 (64-bit)
- 4GB RAM minimum (8GB+ recommended for large models)
- GPU with CUDA support (optional, for acceleration)
- Internet connection (for Google Translate and model downloads)

## Installation

### Option 1: Download Installer (Recommended)
1. Download the latest installer from [Releases](https://github.com/yourusername/DogeAutoSub/releases)
2. Run `DogeAutoSub-Setup-v1.0.0.exe`
3. Follow the installation wizard

### Option 2: Portable Version
1. Download the portable version from [Releases]
2. Extract to desired folder
3. Run `DogeAutoSub.exe`

## Usage

1. **Select Input Video**: Click "Select Video File" and choose your video file
2. **Choose Output Folder**: Select where to save subtitle files (optional)
3. **Configure Settings**:
   - Source Language: Auto-detect or specify
   - Target Language: Choose translation target
   - Model Size: Balance between speed and accuracy
   - Translation Engine: Select your preferred method
4. **Start Processing**: Click "Start" and wait for completion

## Supported Formats

**Input**: MP4, AVI, MKV, MOV, and other common video formats
**Output**: SRT subtitle files

## Building from Source

### Prerequisites
- Python 3.11
- Git

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/DogeAutoSub.git
   cd DogeAutoSub
   ```

2. Create virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements-full.txt
   ```

4. Run the application:
   ```bash
   python AutoUI.py
   ```

### Building Executable
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the application:
   ```bash
   build.bat
   ```

## Troubleshooting

### Common Issues

**"Model not found" error**: 
- Check internet connection for initial model download
- Ensure sufficient disk space in models folder

**GPU not detected**:
- Install CUDA toolkit compatible with your GPU
- Verify PyTorch CUDA installation

**Translation fails**:
- Check internet connection for Google Translate
- Try MarianMT for offline translation

**Empty subtitle files**:
- Check audio quality of input video
- Try different model sizes
- Verify language settings

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI Whisper team for the amazing speech recognition model
- PySide6 for the GUI framework
- All open-source contributors

## Support

- Report issues: [GitHub Issues](https://github.com/yourusername/DogeAutoSub/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/DogeAutoSub/discussions)