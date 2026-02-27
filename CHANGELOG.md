# Changelog

All notable changes to DogeAutoSub will be documented in this file.

## [1.0.0] - 2024-01-XX

### Added
- Initial release of DogeAutoSub
- Automatic speech recognition using OpenAI Whisper
- Support for multiple Whisper model sizes (tiny, base, small, medium, large)
- Multi-language transcription with auto-detection
- Translation support via Google Translate and MarianMT
- GPU acceleration with CUDA support
- Modern GUI with dark/light theme support
- Real-time progress tracking and time estimation
- Batch processing capabilities
- SRT subtitle file output
- Audio volume boost feature

### Features
- **Speech Recognition**: High-quality transcription using Whisper models
- **Translation Engines**: 
  - Google Translate (online, 100+ languages)
  - MarianMT (offline, 50+ language pairs)
  - Whisper built-in translation
- **User Interface**: 
  - Intuitive drag-and-drop interface
  - Theme switching (Dark/Light)
  - Progress indicators with time estimates
  - Model performance indicators
- **Performance**: 
  - GPU acceleration support
  - Dynamic progress weighting
  - Memory optimization for large files
- **Compatibility**: 
  - Multiple video formats (MP4, AVI, MKV, MOV)
  - Network path support
  - Windows 10/11 compatibility

### Technical Details
- Built with PySide6 for modern GUI
- OpenAI Whisper for speech recognition
- PyTorch for GPU acceleration
- Transformers library for MarianMT
- FFmpeg for audio extraction
- Deep-translator for Google Translate integration

### Known Issues
- Large model sizes may require significant GPU memory
- First-time model downloads require internet connection
- Some network paths may require specific permissions

### System Requirements
- Windows 10/11 (64-bit)
- Python 3.8+ (for source installation)
- 4GB RAM minimum (8GB+ recommended)
- GPU with CUDA support (optional)
- Internet connection for translations and model downloads
