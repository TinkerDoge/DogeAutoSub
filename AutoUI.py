import sys
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QMovie, QPixmap, QDesktopServices, QIcon
from PySide6.QtCore import QThread, QUrl
import os
import ui_DogeAutoSub
from modules.constants import MODEL_INFO
from modules.AutoSub import AutoSub
import argparse
import time  # Import time to measure elapsed time

class SubtitleThread(QThread):
    task_complete = QtCore.Signal()
    task_start = QtCore.Signal()
    progress_update = QtCore.Signal(int)
    status_update = QtCore.Signal(str)
    duration_update = QtCore.Signal(float)  # Define a duration signal
    
    def __init__(self, parent=None, autosub_args=None):
        super().__init__(parent)
        self.autosub_args = autosub_args

    def run(self):
        # Display the loading GIF while the task is in progress
        self.task_start.emit()

        # Start the timer
        start_time = time.time()

        # Parse the arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("source_path", help="Path to the video or audio file to subtitle", nargs="?")
        parser.add_argument("-o", "--output-folder", help="Folder to save the output SRT file", default=os.getcwd())
        parser.add_argument("-S", "--src-language", help="Language spoken in the source file", default=None)
        parser.add_argument("-M", "--model-size", help="Whisper model size (tiny, base, small, medium, large)", default="base")
        parser.add_argument('-F', '--format', help="Destination subtitle format", default="srt")
        parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles", default="en")
        parser.add_argument('-E', '--translateEngine', help="Type of Translator Engine", default="whisper")
        parser.add_argument('--volume', help="Volume boost for audio extraction", type=int, default=3)
        args = parser.parse_args(self.autosub_args)

        # Create an instance of AutoSub and connect the progress and status signals
        autosub = AutoSub()
        autosub.progress_update.connect(self.progress_update.emit)
        autosub.status_update.connect(self.status_update.emit)
        autosub.duration_update.connect(self.update_estimated_time.emit)  # Connect the duration signal

        # Run the autosub command
        autosub.run(args)

        # Calculate the elapsed time
        elapsed_time = time.time() - start_time
        elapsed_time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

        # Emit the task_complete signal to indicate that the task is complete
        self.task_complete.emit()

        # Update the status message with the total time taken
        self.status_update.emit(f"Done in {elapsed_time_str}")

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
        if os.path.exists(stylesheet_path):
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
        print("Running AutoSub with arguments:", autosub_args)
        
        # Create and start the subtitle thread
        self.subtitle_thread = SubtitleThread(parent=self, autosub_args=autosub_args)
        self.subtitle_thread.task_start.connect(self.start_loading_animation)
        self.subtitle_thread.task_complete.connect(self.stop_loading_animation)
        self.subtitle_thread.progress_update.connect(self.update_progress_bar)
        self.subtitle_thread.status_update.connect(self.update_status_label)
        self.subtitle_thread.start()

    def update_progress_bar(self, value):
        self.progressBar.setValue(value)
        
    def update_status_label(self, status):
        self.statusLb.setText(status)
        
    def update_estimated_time(self, duration):
        estimated_time = duration * 2  # Rough estimate: 2x the audio duration
        estimated_time_str = time.strftime("%H:%M:%S", time.gmtime(estimated_time))
        self.statusLb.setText(f"Estimated time to complete: {estimated_time_str}")
        
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