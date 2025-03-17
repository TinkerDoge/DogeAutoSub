# DogeAutoSub

## Automatic Subtitle Generator

DogeAutoSub is a desktop application that automatically generates subtitles for video files using OpenAI's Whisper speech recognition technology. It supports multiple languages, translation capabilities, and customizable options for optimal subtitle generation.


## Features

- **Automatic Speech Recognition**: Uses Whisper models to transcribe audio from video files
- **Multiple Language Support**: Detects and transcribes in numerous languages
- **Translation Options**: Translate subtitles from source language to target language
- **Model Selection**: Choose from different Whisper model sizes (tiny, base, small, medium, large, turbo)
- **Translation Engines**: Select between Whisper or Google Translate for translations
- **Audio Enhancement**: Adjust volume boost for better recognition of quiet audio
- **User-Friendly Interface**: Simple and intuitive UI with progress tracking
- **Estimated Time Remaining**: Displays time estimates for the subtitling process
- **Dark/Light Theme**: Toggle between dark and light UI themes

## Installation

1. Download the latest version of DogeAutoSub from the [releases page].
2. Extract the ZIP file to a location of your choice.
3. Run the `DogeAutoSub.exe` executable.
4. First run might took a while to download the Whisper Models, you can download the models before use and put them in DogeAutoSubApp\_internal\modules\models 

No additional installation or dependencies required - everything is packaged within the application.

## System Requirements

- Windows 10 or later (64-bit)
- 4GB RAM minimum (8GB+ recommended for larger models)
- GPU with CUDA support recommended for faster processing
- 2GB free disk space

## Usage

1. **Select Input File**: Click "Browse" to select your video file (supports .mp4, .avi, .mkv, .mov)
2. **Choose Output Location**: Select where to save the generated subtitle files
3. **Select Model Size**: Choose based on your needs for accuracy vs. speed
4. **Source Language**: Select the language spoken in the video or choose "Auto" for automatic detection
5. **Target Language**: Select the language for translated subtitles
6. **Translation Engine**: Choose between Whisper or Google Translate
7. **Audio Boost**: Adjust if your video has low volume
8. **Click Start**: Begin the subtitle generation process

Generated subtitles will be saved in SRT format in the specified output folder.

## Model Information

| Size   | Parameters | English-only Model | Multilingual Model | Required VRAM | Relative Speed |
|--------|------------|--------------------|--------------------|---------------|----------------|
| tiny   | 39 M       | tiny.en            | tiny               | ~1 GB         | ~10x           |
| base   | 74 M       | base.en            | base               | ~1 GB         | ~7x            |
| small  | 244 M      | small.en           | small              | ~2 GB         | ~4x            |
| medium | 769 M      | medium.en          | medium             | ~5 GB         | ~2x            |
| large  | 1550 M     | N/A                | large              | ~10 GB        | 1x             |
| turbo  | 809 M      | N/A                | turbo              | ~6 GB         | ~8x            |

- **Tiny**: Fastest option, best for quick transcriptions where perfect accuracy isn't critical
- **Base**: Good balance for shorter content with clear audio
- **Small**: Better accuracy for most everyday uses
- **Medium**: High accuracy with reasonable processing time
- **Large**: Highest accuracy, best for difficult audio or accents
- **Turbo**: Fast processing with quality comparable to the medium model

The application will automatically use GPU acceleration (CUDA) when available to speed up processing times.

## Troubleshooting

- **Slow Processing**: Select a smaller model size or ensure your GPU is being utilized
- **Low Accuracy**: Try a larger model size or increase the audio boost if audio is quiet
- **Out of Memory Errors**: Select a smaller model size or ensure sufficient system resources
- **Language Detection Issues**: Manually specify the source language instead of using Auto
- **Translation Errors**: Try switching between Whisper and Google Translate engines

## License

This software is distributed under the MIT License. See LICENSE file for more information.

## Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) for the speech recognition technology
- [PySide6](https://wiki.qt.io/Qt_for_Python) for the UI framework
- [FFmpeg](https://ffmpeg.org/) for audio extraction and processing

## Contact

For bug reports, feature requests, or general feedback, please solve it yourself, sorry in advance.