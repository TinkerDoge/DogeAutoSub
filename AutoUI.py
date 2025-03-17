import sys
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QMovie, QPixmap, QDesktopServices, QIcon
from PySide6.QtCore import QThread, QUrl, QObject
import os
import ui_DogeAutoSub
from modules.constants import MODEL_INFO, LANGUAGETRANS, LANGUAGE_CODES_AI
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
                return [], None
            
            start_time = time.time()
            
            # Handle "auto" language parameter
            language_param = None if self.language == "auto" else self.language
            
            # Perform the transcription
            result = self.model.transcribe(audio_path, language=language_param, task="transcribe", ffmpeg_path=ffmpeg_path)
            segments = result["segments"]
            detected_language = result.get("language", "unknown")
            print(f"Transcription successful. Detected language: {detected_language}")

            # Emit final progress update
            if progress_callback:
                progress_callback(75)
            
            return segments, detected_language  # Return both segments and detected language
        except Exception as e:
            print(f"Error during transcription: {e}")
            return [], None
        
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
        # Dynamic stage weights based on model size and audio duration
        self.stage_weights = {
            "extract_audio": 0.05,  # Extract audio is usually quick
            "load_model": 0.0,      # Will be calculated dynamically based on model size
            "transcribe": 0.0,      # Will be calculated dynamically based on audio duration and model
            "translate": 0.0        # Will be calculated dynamically based on segments and target language
        }
        self.audio_duration = 0
        self.start_time = 0
        self.segments_count = 0
        self.model_loaded = False
        
    def calculate_dynamic_weights(self):
        """Calculate stage weights dynamically based on model size and audio duration"""
        model_size = self.args.model_size
        translate = self.args.src_language != self.args.dst_language
        
        # Model loading times vary significantly by size
        model_load_factors = {
            "tiny": 0.05,
            "base": 0.1,
            "small": 0.15,
            "medium": 0.2,
            "large": 0.25,
            "turbo": 0.15
        }
        
        # Transcription time factors
        transcribe_factors = {
            "tiny": 0.55,
            "base": 0.6,
            "small": 0.65,
            "medium": 0.7,
            "large": 0.8,
            "turbo": 0.6
        }
        
        # Get factors for selected model
        load_factor = model_load_factors.get(model_size, 0.1)
        transcribe_factor = transcribe_factors.get(model_size, 0.6)
        
        # Set stage weights
        if translate:
            # Adjust weights if translation is needed
            self.stage_weights["load_model"] = load_factor
            self.stage_weights["transcribe"] = transcribe_factor
            self.stage_weights["translate"] = 0.9 - load_factor - transcribe_factor - self.stage_weights["extract_audio"]
        else:
            # Adjust weights if no translation is needed
            self.stage_weights["load_model"] = load_factor
            self.stage_weights["transcribe"] = 0.95 - load_factor - self.stage_weights["extract_audio"]
            self.stage_weights["translate"] = 0.0
        
        print(f"Dynamic weights: {self.stage_weights}")
        
    def update_progress(self, stage, progress_within_stage=1.0):
        """Update progress based on current stage and progress within that stage"""
        # Recalculate weights if audio duration is known but weights aren't set yet
        if self.audio_duration > 0 and not self.model_loaded and stage == "load_model":
            self.calculate_dynamic_weights()
            self.model_loaded = True
        
        # Get list of stages based on whether translation is needed
        if self.args.src_language != self.args.dst_language:
            stages = ["extract_audio", "load_model", "transcribe", "translate"]
        else:
            stages = ["extract_audio", "load_model", "transcribe"]
        
        # Handle special case for transcription progress
        if stage == "transcribe":
            # Adjust progress for longer audio files (transcription is not linear)
            if self.audio_duration > 300:  # For files longer than 5 minutes
                # Apply logarithmic scaling to better reflect perceived progress
                # This helps avoid the feeling of "stuck at 60%" for long files
                progress_within_stage = 0.4 + (0.6 * (progress_within_stage ** 0.7))
        
        # Calculate progress up to the previous stages
        previous_progress = sum(self.stage_weights[s] for s in stages[:stages.index(stage)])
        
        # Add progress from current stage
        current_progress = self.stage_weights[stage] * progress_within_stage
        
        # Calculate total progress percentage
        total_progress = int((previous_progress + current_progress) * 100)
        
        # Update UI
        self.progress_update.emit(total_progress)
        
        # Update remaining time estimate - now accounting for non-linear progress
        elapsed = time.time() - self.start_time
        if total_progress > 0:
            # For better estimation on longer tasks
            if total_progress < 50:
                # Early stages tend to be faster than later ones
                estimated_total = elapsed / (total_progress / 100) * 1.2
            else:
                # Later stages can be more accurately predicted
                estimated_total = elapsed / (total_progress / 100)
                
            remaining = max(1, estimated_total - elapsed)  # Ensure at least 1 second
            remaining_str = time.strftime("%H:%M:%S", time.gmtime(remaining))
            self.duration_update.emit(f"Estimated time remaining: {remaining_str}")
            
    def calculate_initial_estimate(self):
        """Calculate initial time estimate based on audio duration and model size"""
        model_size = self.args.model_size
        translate = self.args.src_language != self.args.dst_language
        
        # Base processing rates (seconds of audio processed per second) for different models
        # These are rough estimates and should be adjusted based on actual performance
        base_rates = {
            "tiny": 5.0,
            "base": 3.0,
            "small": 1.5,
            "medium": 0.8,
            "large": 0.4,
            "turbo": 1.5
        }
        
        # Get processing rate for selected model or default to base
        rate = base_rates.get(model_size, 3.0)
        
        # Calculate base estimate
        estimated_seconds = self.audio_duration / rate
        
        # Add overhead for extraction and loading
        estimated_seconds += 15  # Base overhead
        
        # Add translation overhead if needed
        if translate:
            estimated_seconds *= 1.3  # 30% more time for translation
            
        # Convert to readable format
        estimated_str = time.strftime("%H:%M:%S", time.gmtime(estimated_seconds))
        self.duration_update.emit(f"Initial estimate: {estimated_str}")
        
    def run(self):
        args = self.args
        self.start_time = time.time()
        
        # Determine if translation is needed
        translate = args.src_language != args.dst_language
        
        if not args.source_path:
            print("Error: You need to specify a source path.")
            sys.exit(1)

        self.task_start.emit()  # Emit task start signal
        self.status_update.emit("Starting process")
        os.makedirs(temp_dir, exist_ok=True)

        # Step 1: Extract audio
        self.status_update.emit("Extracting audio")
        extract_start_time = time.time()
        try:
            audio_filename = extract_audio(ffmpeg_path, args.source_path, temp_dir, volume=args.volume)
            self.audio_duration = get_audio_duration(audio_filename, ffmpeg_path)
            print(f"Audio duration: {self.audio_duration:.2f} seconds")
            
            # Calculate initial time estimate
            self.calculate_initial_estimate()
            
            # Update progress for audio extraction
            self.update_progress("extract_audio")
            
        except Exception as e:
            self.status_update.emit(f"Error extracting audio: {e}")
            print(f"Error extracting audio: {e}")
            return
        
        extract_end_time = time.time()
        print(f"Time to Extract Audio: {extract_end_time - extract_start_time:.2f} seconds")
        
        # Ensure the audio file exists and is accessible
        if not os.path.exists(audio_filename):
            print(f"Error: Extracted audio file not found at {audio_filename}")
            sys.exit(1)
            
        # Step 2: Initialize model and detect language if needed
        self.status_update.emit("Loading model")
        load_model_start_time = time.time()
        
        whisper_src_lang = LANGUAGETRANS.get(args.src_language, None)  # Default to None for Whisper auto-detection
        google_src_lang = LANGUAGETRANS.get(args.src_language, "auto")  # Default to "auto" for Google Translate auto-detection
        
        if whisper_src_lang is None:
            recognizer = WhisperRecognizer(model_size=args.model_size)
            detected_language = recognizer.detect_language(audio_filename, ffmpeg_path)
            whisper_src_lang = detected_language if detected_language else "unknown"
            google_src_lang = detected_language if detected_language else "auto"
            self.status_update.emit(f"Detected language: {whisper_src_lang}")
            
        dst_lang = LANGUAGETRANS.get(args.dst_language, "en")
        recognizer = WhisperRecognizer(language=whisper_src_lang, model_size=args.model_size)
        
        # Update progress for model loading
        self.update_progress("load_model")
        
        load_model_end_time = time.time()
        print(f"Time to Load Model: {load_model_end_time - load_model_start_time:.2f} seconds")
        
        # Step 3: Transcribe audio
        self.status_update.emit("Transcribing audio")
        transcribe_start_time = time.time()
                
        def transcription_progress(value):
            # Map the internal progress to our stage progress
            stage_progress = value / 75  # Whisper's callback uses values up to 75
            self.update_progress("transcribe", stage_progress)

        segments, detected_language = recognizer.transcribe(audio_filename, ffmpeg_path, progress_callback=transcription_progress)

        # Save the original transcription to SRT file
        self.status_update.emit("Saving transcription")
        base_name = os.path.splitext(os.path.basename(args.source_path))[0]

        # Use the detected language if we used auto detection
        if whisper_src_lang == "auto" and detected_language:
            file_language_code = detected_language
            # Also update the source language for translation
            google_src_lang = detected_language  # Use detected language instead of "auto"
        else:
            file_language_code = whisper_src_lang

        original_srt_path = os.path.join(
            args.output_folder, f"{base_name}.{file_language_code}.srt"
        )
        save_as_srt(segments, original_srt_path)
        
        # Update progress for transcription completed
        self.update_progress("transcribe")
        
        transcribe_end_time = time.time()
        print(f"Time to Transcribe: {transcribe_end_time - transcribe_start_time:.2f} seconds")

        # Step 4: Translate segments if necessary
        translate_start_time = time.time()
        if translate:

            self.status_update.emit("Translating segments")
            
            # Track translation progress
            translation_steps = len(segments) if segments else 1
            
            if args.translateEngine == "whisper":
                print(f"Translating segments using Whisper from {args.src_language} to {args.dst_language}")
                debug_translation_setup(args.src_language, args.dst_language)
                # Custom progress callback for translation
                def translation_progress(value):
                    # Map the internal progress to our stage progress
                    stage_progress = value / 80  # Whisper's callback uses values up to 80
                    self.update_progress("translate", stage_progress)
                
                segments = recognizer.translate(audio_filename, dst_lang, ffmpeg_path, progress_callback=translation_progress)
                
            elif args.translateEngine == "google":
                print(f"Translating segments using Google Translate from {file_language_code if args.src_language == 'Auto' else args.src_language} to {args.dst_language}")
                
                # Implement progress tracking for Google translation
                translated_segments = []
                
                # Use detected language for Google translator if original was Auto
                source_lang = google_src_lang if args.src_language == 'Auto' else LANGUAGETRANS.get(args.src_language, "auto")
                debug_translation_setup(source_lang, dst_lang)
                    # Special handling for Chinese variants
                if google_src_lang == 'zh':
                    # You can try different variants if one fails
                    source_options = 'zh-CN'
                translator = GoogleTranslator(source=source_options, target=dst_lang)
                
                for i, segment in enumerate(segments):
                    translated_text = translator.translate(segment["text"])
                    translated_segments.append({
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": translated_text
                    })
                    
                    # Update progress every few segments
                    if i % max(1, len(segments) // 10) == 0:
                        progress = (i + 1) / len(segments)
                        self.update_progress("translate", progress)
                        
                segments = translated_segments
                
            print("Translation completed.")

            self.status_update.emit("Saving translation")
            # Save the translated transcription to SRT file
            translated_srt_path = os.path.join(
                args.output_folder, f"{base_name}.{dst_lang}.srt"
            )
            save_as_srt(segments, translated_srt_path)
            
            # Update progress for translation completed
            self.update_progress("translate")
        
        translate_end_time = time.time()
        if translate:
            print(f"Time to Translate: {translate_end_time - translate_start_time:.2f} seconds")
        
        self.status_update.emit("Cleaning up temporary files")
        # Clean up the temporary directory and files
        try:
            print("Cleaning up temporary files")
            os.remove(audio_filename)  # Removing the extracted audio file
        except Exception as e:
            print(f"Error cleaning up temporary files: {e}")

        # Calculate final statistics
        total_time = time.time() - self.start_time
        elapsed_time_str = time.strftime("%H:%M:%S", time.gmtime(total_time))
        
        self.task_complete.emit()
        self.status_update.emit(f"Done in {elapsed_time_str}")
        self.progress_update.emit(100)
        
        print(f"Audio duration: {self.audio_duration:.2f} seconds")
        print(f"Total time: {total_time:.2f} seconds")
               
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("GPU cache cleared.")
            
        return 0

# Add this method to debug translation issues
def debug_translation_setup(source_lang, target_lang):
    """Debug translation setup to identify issues with specific language pairs"""
    print(f"\nDEBUG TRANSLATION: {source_lang} -> {target_lang}")
    
    # Check if languages are in our mapping
    print(f"Source in LANGUAGETRANS: {source_lang in LANGUAGE_CODES_AI}")
    print(f"Target in LANGUAGETRANS: {target_lang in LANGUAGE_CODES_AI}")
    
    # Get the language codes
    src_code = LANGUAGETRANS.get(source_lang, source_lang)
    dst_code = LANGUAGETRANS.get(target_lang, target_lang)
    print(f"Source code: {src_code}")
    print(f"Target code: {dst_code}")

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
    """
    Translates transcription segments using Google Translate with better handling
    for Chinese and other languages.
    """
    translated_segments = []
    
    # Debug info
    print(f"Translating from '{src_lang}' to '{dst_lang}'")
    
    # Map 'auto' to None for source language as needed by GoogleTranslator
    source = None if src_lang == 'auto' else src_lang
    
    # Special handling for Chinese variants
    if src_lang == 'zh':
        # You can try different variants if one fails
        source_options = ['zh-CN', 'zh-TW']
    else:
        source_options = [source]
    
    # Initialize translator with first option
    try:
        translator = GoogleTranslator(source=source_options[0], target=dst_lang)
        test_success = False
        
        # Test the translator with a simple phrase
        if segments and segments[0]:
            try:
                test_text = segments[0]["text"][:50]  # Use first 50 chars for testing
                translator.translate(test_text)
                test_success = True
            except Exception as e:
                print(f"Initial translation test failed: {e}")
        
        # If test failed and we have alternatives, try them
        if not test_success and len(source_options) > 1:
            for alt_source in source_options[1:]:
                try:
                    print(f"Trying alternative source language: {alt_source}")
                    translator = GoogleTranslator(source=alt_source, target=dst_lang)
                    if segments and segments[0]:
                        translator.translate(segments[0]["text"][:50])
                        break
                except Exception as e:
                    print(f"Alternative source {alt_source} failed: {e}")
    
    except Exception as e:
        print(f"Error initializing translator: {e}")
        # Fallback to simple pass-through if translation fails
        return segments
    
    # Process segments in batches to improve efficiency
    batch_size = 10
    total_segments = len(segments)
    
    for i in range(0, total_segments, batch_size):
        batch = segments[i:i+batch_size]
        print(f"Translating batch {i//batch_size + 1}/{(total_segments + batch_size - 1)//batch_size}")
        
        # Translate each segment in the batch
        for segment in batch:
            try:
                original_text = segment["text"].strip()
                if not original_text:
                    translated_text = ""
                else:
                    translated_text = translator.translate(original_text)
                
                translated_segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": translated_text
                })
            except Exception as e:
                print(f"Error translating segment: {e}")
                # If translation fails, keep the original text
                translated_segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"]
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
            "QComboBox::down-arrow { image: url(../icons/drop-down-menu.png); width: 16px; height: 16px; }"
        )
        self.source_language_dropdown.setStyleSheet(
            "QComboBox::down-arrow { image: url(../icons/drop-down-menu.png); width: 16px; height: 16px; }"
        )
        self.target_language_dropdown.setStyleSheet(
            "QComboBox::down-arrow { image: url(../icons/drop-down-menu.png); width: 16px; height: 16px; }"
        )
        self.target_engine.setStyleSheet(
            "QComboBox::down-arrow { image: url(../icons/drop-down-menu.png); width: 16px; height: 16px; }"
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
        
        # Call this in your __init__ method after UI setup
        self.setup_language_dropdowns()

    def setup_language_dropdowns(self):
        """Setup language dropdowns with proper mapping between display names and codes"""
        # Clear existing items
        self.source_language_dropdown.clear()
        self.target_language_dropdown.clear()
        
        # Add "Auto" detection option only to source language
        self.source_language_dropdown.addItem("Auto")
        
        # Add all languages from LANGUAGE_CODES_AI
        for code, name in LANGUAGE_CODES_AI:
            if code != "auto":  # Skip auto in the loop since we already added it
                self.source_language_dropdown.addItem(name)
                self.target_language_dropdown.addItem(name)
        
        # Set default selections
        self.source_language_dropdown.setCurrentText("Auto")
        self.target_language_dropdown.setCurrentText("English")

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
