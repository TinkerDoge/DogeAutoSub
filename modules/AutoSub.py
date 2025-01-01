import argparse
import os
import subprocess
import sys
import whisper
from datetime import timedelta
from modules.constants import LANGUAGETRANS  # Import the language translation mapping
from deep_translator import GoogleTranslator  # Import the deep-translator library
from PySide6.QtCore import QObject

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)

def extract_audio(filename, temp_dir, channels=1, rate=44100, volume="3"):
    """Extracts audio from the source file and saves it as a WAV file."""
    print(f"Extracting audio from filename: {filename}")
    try:
        temp_audio_path = os.path.join(os.path.dirname(__file__), temp_dir, "extracted_audio.wav")
        print(f"Temporary audio path: {temp_audio_path}")
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
            "-i", filename, "-ac", str(channels), "-ar", str(rate),
            "-filter:a", f"volume={volume}", "-vn", "-f", "wav", temp_audio_path
        ]
        print(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)
        print("Audio extraction successful")
        return temp_audio_path
    except Exception as e:
        print(f"Error extracting audio: {e}")
        sys.exit(1)
        
class WhisperRecognizer(QObject):
    """Wrapper class for Whisper transcription."""

    def __init__(self, language=None, model_size="base"):
        super().__init__()
        model_path = os.path.join(os.path.dirname(__file__), "models")
        if language is None:
            print("Initializing WhisperRecognizer with auto-detection for language")
        else:
            print(f"Initializing WhisperRecognizer with language: {language}, model_size: {model_size}")
        self.language = language
        try:
            self.model = whisper.load_model(model_size, download_root=model_path)
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            sys.exit(1)

    def detect_language(self, audio_path):
        """Detects the language spoken in the audio using Whisper."""
        try:
            print(f"Detecting language for audio: {audio_path}")
            result = self.model.transcribe(audio_path, task="detect-language")
            detected_language = result["language"]
            print(f"Detected language: {detected_language}")
            return detected_language
        except Exception as e:
            print(f"Error during language detection: {e}")
            return None

    def transcribe(self, audio_path):
        """Transcribes audio using Whisper."""
        try:
            print(f"Transcribing audio: {audio_path}")
            if not os.path.exists(audio_path):
                print(f"Error: Audio file not found at {audio_path}")
                return []
            print(f"Audio file found: {audio_path}")
            result = self.model.transcribe(audio_path, language=self.language, task="transcribe")
            print("Transcription successful")
            segments = result["segments"]
            return segments  # Returning segments for SRT formatting
        except Exception as e:
            print(f"Error during transcription: {e}")
            return []

    def translate(self, audio_path, target_language):
        """Translates audio using Whisper."""
        try:
            print(f"Translating audio: {audio_path} to {target_language}")
            result = self.model.transcribe(audio_path, language=target_language, task="translate")
            print("Translation successful")
            segments = result["segments"]
            return segments  # Returning segments for SRT formatting
        except Exception as e:
            print(f"Error during translation: {e}")
            return []

def format_timestamp(seconds):
    """Formats time in seconds to SRT timestamp format."""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def translate_segments_google(segments, src_lang, dst_lang):
    """Translates transcription segments to the desired language using Google Translate."""
    translator = GoogleTranslator(source=src_lang, target=dst_lang)
    translated_segments = []
    for segment in segments:
        translated_text = translator.translate(segment["text"])
        translated_segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": translated_text
        })
    return translated_segments

def save_as_srt(segments, output_path):
    """Saves transcription segments as an SRT file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Ensure output directory exists
    with open(output_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(segments, start=1):
            start_time = format_timestamp(segment["start"])
            end_time = format_timestamp(segment["end"])
            text = segment["text"].strip()
            srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
    print(f"Subtitles saved to {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_path", help="Path to the video or audio file to subtitle", nargs="?")
    parser.add_argument("-o", "--output-folder", help="Folder to save the output SRT file", default=os.getcwd())
    parser.add_argument("-S", "--src-language", help="Language spoken in the source file", default=None)
    parser.add_argument("-M", "--model-size", help="Whisper model size (tiny, base, small, medium, large)", default="base")
    parser.add_argument('-F', '--format', help="Destination subtitle format", default="srt")
    parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles", default="en")
    parser.add_argument('-E', '--translateEngine', help="Type of Translator Engine", default="whisper")
    args = parser.parse_args()

    if not args.source_path:
        print("Error: You need to specify a source path.")
        sys.exit(1)

    # Create or use existing 'temp' directory
    temp_dir = os.path.join(os.getcwd(), "modules", "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Step 1: Extract audio
    try:
        audio_filename = extract_audio(args.source_path, temp_dir)
        print(f"Extracted audio filename: {audio_filename}")
    except Exception as e:
        print(f"Error extracting audio: {e}")
        sys.exit(1)

    # Ensure the audio file exists and is accessible
    if not os.path.exists(audio_filename):
        print(f"Error: Extracted audio file not found at {audio_filename}")
        sys.exit(1)

    # Step 2: Detect language if not provided
    whisper_src_lang = LANGUAGETRANS.get(args.src_language, None)  # Default to None for Whisper auto-detection
    google_src_lang = LANGUAGETRANS.get(args.src_language, "auto")  # Default to "auto" for Google Translate auto-detection
    if whisper_src_lang is None:
        recognizer = WhisperRecognizer(model_size=args.model_size)
        detected_language = recognizer.detect_language(audio_filename)
        whisper_src_lang = detected_language if detected_language else "unknown"
        google_src_lang = detected_language if detected_language else "auto"
    dst_lang = LANGUAGETRANS.get(args.dst_language, "en")
    recognizer = WhisperRecognizer(language=whisper_src_lang, model_size=args.model_size)
    try:
        segments = recognizer.transcribe(audio_filename)
        print(f"Transcription segments: {segments}")

        # Save the original transcription to SRT file
        base_name = os.path.splitext(os.path.basename(args.source_path))[0]
        original_srt_path = os.path.join(
            args.output_folder, f"{base_name}.{whisper_src_lang}.srt"
        )
        save_as_srt(segments, original_srt_path)

        # Step 3: Translate segments if necessary
        if args.src_language != args.dst_language:
            if args.translateEngine == "whisper":
                print(f"Translating segments using Whisper from {args.src_language} to {args.dst_language}")
                segments = recognizer.translate(audio_filename, dst_lang)
            elif args.translateEngine == "google":
                print(f"Translating segments using Google Translate from {args.src_language} to {args.dst_language}")
                segments = translate_segments_google(segments, google_src_lang, dst_lang)
            print("Translation completed.")

            # Save the translated transcription to SRT file
            translated_srt_path = os.path.join(
                args.output_folder, f"{base_name}.{dst_lang}.srt"
            )
            save_as_srt(segments, translated_srt_path)

    finally:
        # Clean up the temporary directory and files
        try:
            print("Cleaning up temporary files")
            os.remove(audio_filename)  # Removing the extracted audio file
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")

    return 0

if __name__ == "__main__":
    sys.exit(main())