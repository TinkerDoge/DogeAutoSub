# Changelog

All notable changes to DogeAutoSub are documented in this file.

---

## [2.1.1] - 2026-02-28

### Changed
- **Translation cost optimization (~90% reduction)**
  - Switched from Claude Opus 4.6 → Claude Sonnet 4 for translation
  - Batched translation: 10 segments per API call instead of 1 (174 calls → ~18)
  - Streamlined prompts to reduce token usage
  - Meeting notes summarization also moved to Sonnet
- Translation time for 8-min video: **7.5 min → ~45s**

---

## [2.1.0] - 2026-02-28

### Removed
- Dead `extract_audio()` and `get_audio_duration()` functions from AutoUI.py
- Unused `LANGUAGETRANS` dict and `TASK_TYPES` list from constants.py
- Dead `get_recognizer()` factory function from faster_whisper_engine.py
- Stale "legacy whisper" references from chunk_processor.py comments
- Unused `wave` and `contextlib` imports

### Changed
- Updated README.md with full v2.x documentation
- Updated CHANGELOG.md with complete version history

---

## [2.0.6] - 2026-02-28

### Fixed
- Auto-updater now works correctly with PyInstaller builds
  - Stripped app modules from PYZ archive via `a.pure` filtering in `.spec`
  - Added `sys.path.insert(0, _internal)` + `importlib.invalidate_caches()` at startup
  - Disk `.py` files now take priority over frozen bytecode after delta patch

### Changed
- "Get Token" button moved to title row, aligned with MLAAS section header
- Version bump test comments on `chunk_processor`, `mlaas_client`, `faster_whisper_engine`
- Regenerated release manifest with 21 tracked files

---

## [2.0.4] - 2026-02-28

### Added
- Delta patching auto-updater — only changed files are downloaded over LAN
- `serve_updates.py` — update server with manifest generation and file serving
- `updater_config.json` — configurable update server URL
- SHA-256 hash-based file change detection
- Automatic app restart after successful update

### Changed
- Build spec (`DogeAutoSubApp.spec`) updated:
  - App modules removed from `hiddenimports`
  - App modules stripped from `a.pure` to keep them out of PYZ archive
  - Enables runtime replacement of `.py` files by the auto-updater

---

## [2.0.0] - 2026-02-25

### Added
- **faster-whisper engine** — CTranslate2-based GPU transcription (4x faster than OpenAI Whisper)
- **MLAAS translation** — Integration with Virtuos ML-as-a-Service API (GPT-4o backend)
- **Meeting Notes tab** — Upload `.docx` transcripts, AI-powered summarization via MLAAS
- **File Translation tab** — Standalone translation of `.srt`, `.docx`, `.txt` files
- **Tabbed UI** — Subtitles / Meeting Notes / Translate tabs
- Word-level timestamps for intelligent segment splitting
- Built-in VAD (Voice Activity Detection) to skip silence
- Batched inference pipeline for GPU acceleration
- Audio volume boost slider
- Dark/Light theme with CSS stylesheets
- MLAAS Bearer token input with "Get Token" shortcut

### Changed
- Replaced OpenAI Whisper with faster-whisper (CTranslate2)
- Replaced legacy model selection with auto-optimized `large-v3-turbo`
- UI rebuilt from scratch with hand-coded PySide6 (replaced Qt Designer `.ui` file)
- Modernized project structure with dedicated `modules/` directory

### Removed
- OpenAI Whisper dependency
- Legacy `whisper` model support
- Qt Designer generated UI file
- Batch processing (replaced by single-pass with better performance)

---

## [1.0.0] - 2024-01-01

### Added
- Initial release of DogeAutoSub
- Speech recognition using OpenAI Whisper
- Multiple model sizes (tiny, base, small, medium, large)
- Multi-language transcription with auto-detection
- Translation via Google Translate and MarianMT
- GPU acceleration with CUDA support
- PySide6 GUI with dark/light theme
- Real-time progress tracking
- SRT subtitle output
