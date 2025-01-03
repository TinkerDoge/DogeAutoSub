import sys
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QMovie, QPixmap, QDesktopServices, QIcon
from PySide6.QtCore import QThread, QUrl, QObject
import os
import ui_DogeAutoSub
from modules.constants import MODEL_INFO, LANGUAGETRANS, BASE_WEIGHTS, TRANSLATE_WEIGHTS
import argparse
import re
import subprocess
import whisper
import torch  # Import torch to check for GPU availability
from datetime import timedelta
from deep_translator import GoogleTranslator  # Import the deep-translator library
import time  # Import time to measure elapsed time

# Set CUDA environment variables to the modules/CUDA directory
cuda_path = os.path.join(os.path.dirname(__file__),'modules','CUDA')
print("CUDA path:", cuda_path)
os.environ['CUDA_PATH'] = cuda_path
os.environ['PATH'] = os.path.join(cuda_path, 'bin') + os.pathsep + os.environ['PATH']
os.environ['CUDA_HOME'] = cuda_path
os.environ['CUDA_ROOT'] = cuda_path
os.environ['LD_LIBRARY_PATH'] = os.path.join(cuda_path, 'lib') + os.pathsep + os.environ.get('LD_LIBRARY_PATH', '')

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
ffmpeg_path = os.path.join(script_dir,"modules", "ffmpeg", "bin", "ffmpeg.exe")
temp_dir = os.path.join(script_dir,"modules", "temp")

# WhisperRecognizer class for Whisper transcription
class WhisperRecognizer(QObject):

    def __init__(self, language=None, model_size="base"):
        super().__init__()
        model_path = os.path.join(os.path.dirname(__file__), "modules", "models")
        print(f"Model path: {model_path}")
        if language is None:
            print("Initializing WhisperRecognizer with auto-detection for language")
        else:
            print(f"Initializing WhisperRecognizer with language: {language}, model_size: {model_size}")
        self.language = language
        try:
            self.model = whisper.load_model(model_size, download_root=model_path)
            print("Model loaded successfully")
            # Move the model to GPU if available and model size is not large
            if torch.cuda.is_available() and model_size != "large":
                self.model = self.model.to('cuda')
                print("Model moved to GPU")
            else:
                self.model = self.model
                print("GPU not available or model size is large, using CPU")
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
 
# AutoSub class for autosub functionality

class SubtitleThread(QThread):
    task_complete = QtCore.Signal()
    task_start = QtCore.Signal()
    progress_update = QtCore.Signal(int)
    status_update = QtCore.Signal(str)
    duration_update = QtCore.Signal(str)  # Define a duration signal

    
    def __init__(self, args):
        super().__init__()
        self.args = args
        
    def emit_final_signals(self, start_time):
        elapsed_time = time.time() - start_time
        elapsed_time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        self.task_complete.emit()
        self.status_update.emit(f"Done in {elapsed_time_str}")
        self.progress_update.emit(100)  
        
    def update_estimated_time(self, duration, model_size, include_translate=True):

        # Get the base multiplier
        base_multiplier = BASE_WEIGHTS.get(model_size, 2)  # Default to 2 if model size is not found
        
        # Add the translate multiplier if included
        if include_translate:
            translate_multiplier = TRANSLATE_WEIGHTS.get(model_size, 0)  # Default to 0 if model size is not found
            total_multiplier = base_multiplier + translate_multiplier
        else:
            total_multiplier = base_multiplier

        # Calculate the estimated time
        estimated_time = duration * total_multiplier
        estimated_time_str = time.strftime("%H:%M:%S", time.gmtime(estimated_time))

        # Print and emit the estimated time
        print(f"Estimated time to complete: {estimated_time_str}")
        self.duration_update.emit(f"Estimated time to complete: {estimated_time_str}")

    def run(self):
        args = self.args
        start_time = time.time()
        
        if args.src_language != args.dst_language:
            translate = True
            print("need to translate")
        else:
            translate = False
            print("don't translate")
            
        if not args.source_path:
            print("Error: You need to specify a source path.")
            sys.exit(1)

        self.task_start.emit()  # Emit task start signal

        os.makedirs(temp_dir, exist_ok=True)

        # Step 1: Extract audio
        extract_start_time = time.time()
        try:
            audio_filename = extract_audio(ffmpeg_path, args.source_path, temp_dir, volume=args.volume)
            audio_duration = get_audio_duration(audio_filename, ffmpeg_path )
            self.update_estimated_time(audio_duration,args.model_size, translate)  # Emit the audio duration
            
        except Exception as e:
            self.status_update.emit(f"Error extracting audio: {e}")
            print(f"Error extracting audio: {e}")
            return
        
        extract_end_time = time.time()
        
        # Ensure the audio file exists and is accessible
        if not os.path.exists(audio_filename):
            print(f"Error: Extracted audio file not found at {audio_filename}")
            sys.exit(1)
        # Step 2: Detect language if not provided
        load_model_start_time = time.time()
        self.status_update.emit("Detecting language")
        whisper_src_lang = LANGUAGETRANS.get(args.src_language, None)  # Default to None for Whisper auto-detection
        google_src_lang = LANGUAGETRANS.get(args.src_language, "auto")  # Default to "auto" for Google Translate auto-detection
        if whisper_src_lang is None:
            recognizer = WhisperRecognizer(model_size=args.model_size)
            detected_language = recognizer.detect_language(audio_filename, ffmpeg_path)
            whisper_src_lang = detected_language if detected_language else "unknown"
            google_src_lang = detected_language if detected_language else "auto"
        dst_lang = LANGUAGETRANS.get(args.dst_language, "en")
        recognizer = WhisperRecognizer(language=whisper_src_lang, model_size=args.model_size)
        self.progress_update.emit(40)  # Emit progress update
        self.status_update.emit("Transcribing audio")
        load_model_end_time = time.time()
        
        transcribe_start_time = time.time()
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
        
        transcribe_end_time = time.time()
     

        # Step 3: Translate segments if necessary
        translate_start_time = time.time()
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
        
        translate_end_time = time.time()
        self.status_update.emit("Cleaning up temporary files")
        # Clean up the temporary directory and files
        try:
            print("Cleaning up temporary files")
            os.remove(audio_filename)  # Removing the extracted audio file
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")

        self.emit_final_signals(start_time)
        task_end_time = time.time()
        # Clear GPU cache
        print(f"Audio duration: {audio_duration:.2f} seconds")
        print(f"Time to Extract Audio: {extract_end_time - extract_start_time:.2f} seconds")
        print(f"Time to Load Model: {load_model_end_time - load_model_start_time:.2f} seconds")
        print(f"Time to Transcribe: {transcribe_end_time - transcribe_start_time:.2f} seconds")
        print(f"Time to Translate: {translate_end_time - translate_start_time:.2f} seconds")
        print(f"Total times: {task_end_time - start_time:.2f} seconds")
               
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("GPU cache cleared.")
        return 0  
    
def get_audio_duration(audio_path, ffmpeg_path=ffmpeg_path):
    """Get the total duration of an audio file using ffmpeg."""
    try:
        command = [
            ffmpeg_path,
            "-i", audio_path,
            "-f", "null",
            "-"
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration_match = re.search(r"Duration: (\d+:\d+:\d+\.\d+)", result.stderr)
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

def extract_audio(ffmpeg_path, filename, temp_dir, channels=1, rate=16000, volume="3"):
    """Extracts audio from the source file and saves it as a WAV file."""
    temp_audio_path = os.path.join(temp_dir, "extracted_audio.wav")
    command = [
        ffmpeg_path, "-hide_banner", "-loglevel", "warning", "-y",
        "-i", filename, "-ac", str(channels), "-ar", str(rate),
        "-filter:a", f"volume={volume}", "-vn", "-f", "wav", temp_audio_path
    ]
    print(f"Running ffmpeg command: {' '.join(command)}")  # Debugging information
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}")  # Print ffmpeg error message
        raise Exception("ffmpeg failed to extract audio")
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

class DogeAutoSub(ui_DogeAutoSub.Ui_Dialog, QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.adjustSize()
        
        # Set the window icon
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "favicon.png")
        self.setWindowIcon(QIcon(icon_path))
        
        # Set other icons
        self.openBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "folder.png")))
        self.themeBtn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "icons", "paint.png")))
        
        # Set the down arrow icon for QComboBox
        self.model_size_dropdown.setStyleSheet(
            "QComboBox::down-arrow { image: url(icons/drop-down-menu.png); width: 16px; height: 16px; }"
        )
        self.source_language_dropdown.setStyleSheet(
            "QComboBox::down-arrow { image: url(icons/drop-down-menu.png); width: 16px; height: 16px; }"
        )
        self.target_language_dropdown.setStyleSheet(
            "QComboBox::down-arrow { image: url(icons/drop-down-menu.png); width: 16px; height: 16px; }"
        )
        self.target_engine.setStyleSheet(
            "QComboBox::down-arrow { image: url(icons/drop-down-menu.png); width: 16px; height: 16px; }"
        )

        # Load and apply the default stylesheet (Dark theme)
        stylesheet_path = os.path.join(os.path.dirname(__file__), "modules", "styleSheetDark.css")
        if (os.path.exists(stylesheet_path)):
            with open(stylesheet_path, "r") as file:
                self.setStyleSheet(file.read())
        else:
            print(f"Error: Stylesheet not found at {stylesheet_path}")
        self.current_theme = "Dark"
        
        # Add a loading label and movie
        self.loading_movie = QMovie(os.path.join(os.path.dirname(__file__), "icons", "loading.gif"))
        
        self.standbyMovie = QMovie(os.path.join(os.path.dirname(__file__), "icons", "start.gif"))
        self.statusimage.setMovie(self.standbyMovie)
        self.standbyMovie.start()
        self.statusLb.setText("Standby")
                
        self.progressBar.setValue(0)
        self.done_pixmap = QPixmap(os.path.join(os.path.dirname(__file__), "icons", "done.jpg")).scaled(130, 150)
        
        self.input_file_button.clicked.connect(self.select_input_file)
        self.output_folder_button.clicked.connect(self.select_output_folder)
        self.start_button.clicked.connect(self.start_subtitle_thread)
        self.model_size_dropdown.currentTextChanged.connect(self.changeModelsinfo)
        
        self.themeBtn.clicked.connect(self.changeThemes)
        
        self.openBtn.clicked.connect(self.open_output_folder)
        self.boostSlider.setValue(3)  # Set default value of boost slider to 3
        
        self.subtitle_thread = None

    def load_stylesheet(self, filename):
        with open(filename, "r") as file:
            self.setStyleSheet(file.read())

    def changeThemes(self):
        if self.current_theme == "Dark":
            self.load_stylesheet(os.path.join(os.path.dirname(__file__), "modules", "styleSheetLight.css"))
            self.current_theme = "Light"
        else:
            self.load_stylesheet(os.path.join(os.path.dirname(__file__), "modules", "styleSheetDark.css"))
            self.current_theme = "Dark"

    def open_output_folder(self):
        input_file_path = getattr(self, 'input_file_path', None)
        output_folder_path = getattr(self, 'output_folder_path', None)
        if not input_file_path:
            print("Error: No input file selected.")
            return
        if not output_folder_path:
            output_folder_path = os.path.dirname(input_file_path)
        
        if output_folder_path and os.path.exists(output_folder_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_folder_path))
        else:
            print("Error: Output folder path is not set or does not exist.")

    def start_subtitle_thread(self):
        self.progressBar.setValue(0)
        # Get selected file path and output folder path
        input_file_path = getattr(self, 'input_file_path', None)
        output_folder_path = getattr(self, 'output_folder_path', None)
        
        if not input_file_path:
            print("Error: No input file selected.")
            return
        
        if not output_folder_path:
            # Set default output folder to the folder containing the source file
            output_folder_path = os.path.dirname(input_file_path)
            self.output_file_path_display.setText(output_folder_path)

        # Get selected source and target languages
        source_lang = self.source_language_dropdown.currentText()
        target_lang = self.target_language_dropdown.currentText()
        modelSize = self.model_size_dropdown.currentText()
        engine = self.target_engine.currentText()

        # Get the current value of the boostSlider
        volume = self.boostSlider.value()

        # Build the autosub arguments with the selected options
        autosub_args = [
            input_file_path,
            "-S", source_lang,
            "-D", target_lang,
            "-o", output_folder_path,
            "-M", modelSize,
            "-E", engine,
            "--volume", str(volume)
        ]
        
        parser = argparse.ArgumentParser()
        parser.add_argument("source_path", help="Path to the video or audio file to subtitle", nargs="?")
        parser.add_argument("-o", "--output-folder", help="Folder to save the output SRT file", default=os.getcwd())
        parser.add_argument("-S", "--src-language", help="Language spoken in the source file", default=None)
        parser.add_argument("-M", "--model-size", help="Whisper model size (tiny, base, small, medium, large)", default="base")
        parser.add_argument('-F', '--format', help="Destination subtitle format", default="srt")
        parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles", default="en")
        parser.add_argument('-E', '--translateEngine', help="Type of Translator Engine", default="whisper")
        parser.add_argument('--volume', help="Volume boost for audio extraction", type=int, default=3)
        args = parser.parse_args(autosub_args)

        # Create and start the subtitle thread
        self.subtitle_thread = SubtitleThread(args=args)
        self.subtitle_thread.task_start.connect(self.start_loading_animation)
        self.subtitle_thread.task_complete.connect(self.stop_loading_animation)
        self.subtitle_thread.progress_update.connect(self.update_progress_bar)
        self.subtitle_thread.status_update.connect(self.update_status_label)
        self.subtitle_thread.duration_update.connect(self.update_duration_lable)
        self.subtitle_thread.start()
        
    def update_progress_bar(self, value):
        self.progressBar.setValue(value)

    def update_status_label(self, status):
        self.statusLb.setText(status)
    
    def update_duration_lable(self, status):
        self.estlb.setText(status)
           
    def changeModelsinfo(self, modelSize):
        # Update VRamUsage and rSpeed based on the selected model size
        if (model_info := MODEL_INFO.get(modelSize)):
            self.VRamUsage.setText(model_info["vram"])
            self.rSpeed.setText(model_info["speed"])
        else:
            self.VRamUsage.setText("Unknown")
            self.rSpeed.setText("Unknown")
        
    def start_loading_animation(self):
        # start the loading animation
        self.statusLb.setText("Processing...")
        self.statusimage.setMovie(self.loading_movie)
        self.loading_movie.start()
        self.progressBar.setValue(0)

    def stop_loading_animation(self):
        self.progressBar.setValue(100)
        self.statusLb.setText("Done <3")
        # Stop the loading animation
        self.loading_movie.stop()
        self.statusimage.setPixmap(self.done_pixmap)
        self.progressBar.setValue(100)

    def select_input_file(self):
        # Allow the user to select the input movie file
        self.input_file_path, _ = QFileDialog.getOpenFileName(self, "Select Movie File", "", "Movie Files (*.mp4 *.avi *.mkv *.mov)")
        if self.input_file_path:
            self.input_file_button.setText(os.path.basename(self.input_file_path))
        
        output_folder_path = os.path.dirname(self.input_file_path)
        self.output_file_path_display.setText(output_folder_path)

    def select_output_folder(self):
        # Allow the user to select the output folder
        self.output_folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if self.output_folder_path:
            self.output_file_path_display.setText(self.output_folder_path)

if __name__ == '__main__':
    app = QApplication([])
    doge = DogeAutoSub()
    doge.show()
    app.exec()
