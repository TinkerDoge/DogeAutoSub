import argparse
import os
import subprocess
import sys
import whisper
import torch  # Import torch to check for GPU availability
from datetime import timedelta
from modules.constants import LANGUAGETRANS  # Import the language translation mapping
from deep_translator import GoogleTranslator  # Import the deep-translator library
from PySide6.QtCore import QObject, Signal
import time  # Import time to measure elapsed time

# Set CUDA environment variables to the modules/CUDA directory
cuda_path = os.path.join(os.path.dirname(__file__), 'CUDA')
print("CUDA path:", cuda_path)
os.environ['CUDA_PATH'] = cuda_path
os.environ['PATH'] = os.path.join(cuda_path, 'bin') + os.pathsep + os.environ['PATH']
os.environ['CUDA_HOME'] = cuda_path
os.environ['CUDA_ROOT'] = cuda_path
os.environ['LD_LIBRARY_PATH'] = os.path.join(cuda_path, 'lib') + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')

# Print environment variables for debugging
print("Environment Variables:")
print("CUDA_PATH:", os.environ.get('CUDA_PATH'))
print("PATH:", os.environ.get('PATH'))
print("CUDA_HOME:", os.environ.get('CUDA_HOME'))
print("CUDA_ROOT:", os.environ.get('CUDA_ROOT'))
print("LD_LIBRARY_PATH:", os.environ.get('LD_LIBRARY_PATH'))


script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
ffmpeg_path = os.path.join(script_dir, "ffmpeg", "bin", "ffmpeg.exe")

class WhisperRecognizer(QObject):
    """Wrapper class for Whisper transcription."""

    def __init__(self, language=None, model_size="base"):
        super().__init__()
        model_path = os.path.join(os.path.dirname(__file__), "models")
        print(f"Model path: {model_path}")
        if language is None:
            print("Initializing WhisperRecognizer with auto-detection for language")
        else:
            print(f"Initializing WhisperRecognizer with language: {language}, model_size: {model_size}")
        self.language = language
        try:
            self.model = whisper.load_model(model_size, download_root=model_path)
            print("Model loaded successfully")
            # Move the model to GPU if available
            if torch.cuda.is_available():
                self.model = self.model.to('cuda')
                print("Model moved to GPU")
            else:
                print("GPU not available, using CPU")
        except Exception as e:
            print(f"Error loading model: {e}")
            sys.exit(1)

    def detect_language(self, audio_path, ffmpeg_path):
        """Detects the language spoken in the audio using Whisper."""
        try:
            result = self.model.transcribe(audio_path, task="detect-language", ffmpeg_path=ffmpeg_path)
            detected_language = result["language"]
            print(f"Detected language: {detected_language}")
            return detected_language
        except Exception as e:
            print(f"Error during language detection: {e}")
            return None

    def transcribe(self, audio_path, ffmpeg_path, progress_callback=None):
        """Transcribes audio using Whisper."""
        try:
            if not os.path.exists(audio_path):
                print(f"Error: Audio file not found at {audio_path}")
                return []
            
            start_time = time.time()
            segments = []


            # Perform the transcription in a non-blocking way
            result = self.model.transcribe(audio_path, language=self.language, task="transcribe", ffmpeg_path=ffmpeg_path)
            segments = result["segments"]
            print("Transcription successful")

            # Emit final progress update
            if progress_callback:
                progress_callback(75)
            
            return segments  # Returning segments for SRT formatting
        except Exception as e:
            print(f"Error during transcription: {e}")
            return []
        
    def translate(self, audio_path, target_language, ffmpeg_path, progress_callback=None):
        """Translates audio using Whisper."""
        try:
            print(f"Translating audio: {audio_path} to {target_language}")
            result = self.model.transcribe(audio_path, language=target_language, task="translate", ffmpeg_path=ffmpeg_path)
            print("Translation successful")
            segments = result["segments"]
            if progress_callback:
                progress_callback(80)  # Emit progress update after translation
            return segments  # Returning segments for SRT formatting
        except Exception as e:
            print(f"Error during translation: {e}")
            return []
            
class AutoSub(QObject):
    progress_update = Signal(int)  # Define a progress signal
    status_update = Signal(str)  # Define a status signal
    duration_update = Signal(float)  # Define a duration signal
    
    def __init__(self):
        super().__init__()


    def run(self, args):
        if not args.source_path:
            print("Error: You need to specify a source path.")
            sys.exit(1)

        # Create or use existing 'temp' directory
        temp_dir = os.path.join(os.getcwd(), "modules", "temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Step 1: Extract audio
        try:
            audio_filename = extract_audio(args.source_path, temp_dir, volume=args.volume)
            audio_duration = get_audio_duration(audio_filename)
            self.duration_update.emit(audio_duration)  # Emit the audio duration
        except Exception as e:
            self.status_update.emit(f"Error extracting audio: {e}")
            return
        
        # Ensure the audio file exists and is accessible
        if not os.path.exists(audio_filename):
            print(f"Error: Extracted audio file not found at {audio_filename}")
            sys.exit(1)

        # Step 2: Detect language if not provided
        self.status_update.emit("Detecting language")
        whisper_src_lang = LANGUAGETRANS.get(args.src_language, None)  # Default to None for Whisper auto-detection
        google_src_lang = LANGUAGETRANS.get(args.src_language, "auto")  # Default to "auto" for Google Translate auto-detection
        if whisper_src_lang is None:
            recognizer = WhisperRecognizer(model_size=args.model_size)
            detected_language = recognizer.detect_language(audio_filename, ffmpeg_path)
            whisper_src_lang = detected_language if detected_language else "unknown"
            google_src_lang = detected_language if detected_language else "auto"
        dst_lang = LANGUAGETRANS.get(args.dst_language, "en")
        print(f"Source language for Whisper: {whisper_src_lang}")
        print(f"Source language for Google Translate: {google_src_lang}")
        print(f"Destination language: {dst_lang}")
        recognizer = WhisperRecognizer(language=whisper_src_lang, model_size=args.model_size)
        self.progress_update.emit(40)  # Emit progress update

        self.status_update.emit("Transcribing audio")
        segments = recognizer.transcribe(audio_filename, ffmpeg_path, progress_callback=self.progress_update.emit)
        #print(f"Transcription segments: {segments}")

        self.status_update.emit("Saving transcription")
        # Save the original transcription to SRT file
        base_name = os.path.splitext(os.path.basename(args.source_path))[0]
        original_srt_path = os.path.join(
            args.output_folder, f"{base_name}.{whisper_src_lang}.srt"
        )
        save_as_srt(segments, original_srt_path)
        self.progress_update.emit(80)  # Emit progress update

        # Step 3: Translate segments if necessary
        if args.src_language != args.dst_language:
            self.status_update.emit("Translating segments")
            if args.translateEngine == "whisper":
                print(f"Translating segments using Whisper from {args.src_language} to {args.dst_language}")
                segments = recognizer.translate(audio_filename, dst_lang, ffmpeg_path, progress_callback=self.progress_update.emit)
            elif args.translateEngine == "google":
                print(f"Translating segments using Google Translate from {args.src_language} to {args.dst_language}")
                segments = translate_segments_google(segments, google_src_lang, dst_lang)
            print("Translation completed.")

            self.status_update.emit("Saving translation")
            # Save the translated transcription to SRT file
            translated_srt_path = os.path.join(
                args.output_folder, f"{base_name}.{dst_lang}.srt"
            )
            save_as_srt(segments, translated_srt_path)
            self.progress_update.emit(80)  # Emit progress update

        self.status_update.emit("Cleaning up temporary files")
        # Clean up the temporary directory and files
        try:
            print("Cleaning up temporary files")
            os.remove(audio_filename)  # Removing the extracted audio file
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")

        self.progress_update.emit(100)  # Emit progress update
        self.status_update.emit("Done")
        return 0  

def get_audio_duration(audio_path, ffmpeg_path="ffmpeg"):
    """Get the total duration of an audio file using ffmpeg."""
    try:
        command = [
            ffmpeg_path,
            "-i", audio_path,
            "-f", "null",
            "-"
        ]
        result = subprocess.run(command, capture_output=True, text=True, stderr=subprocess.STDOUT)
        duration_match = re.search(r"Duration: (\d+:\d+:\d+\.\d+)", result.stdout)
        if duration_match:
            duration_str = duration_match.group(1)
            h, m, s = map(float, duration_str.split(':'))
            duration = h * 3600 + m * 60 + s
            return duration
        else:
            print("Could not find duration in ffmpeg output.")
            return None
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return None

def extract_audio(filename, temp_dir, channels=1, rate=44100, volume="3"):
    """Extracts audio from the source file and saves it as a WAV file."""
    temp_audio_path = os.path.join(temp_dir, "extracted_audio.wav")
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
        "-i", filename, "-ac", str(channels), "-ar", str(rate),
        "-filter:a", f"volume={volume}", "-vn", "-f", "wav", temp_audio_path
    ]
    subprocess.run(command, check=True)
    return temp_audio_path
        
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
    parser.add_argument('--volume', help="Volume boost for audio extraction", type=int, default=3)
    args = parser.parse_args()

    autosub = AutoSub()
    return autosub.run(args)
   
if __name__ == "__main__":
    sys.exit(main())
