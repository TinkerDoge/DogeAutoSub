import sys
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QMovie, QPixmap, QDesktopServices
from PySide6.QtCore import QThread, QUrl
import subprocess
import os
import ui_DogeAutoSub
from modules.constants import MODEL_INFO

class SubtitleThread(QThread):
    task_complete = QtCore.Signal()
    task_start = QtCore.Signal()

    def __init__(self, parent=None, autosub_cmd=None):
        super().__init__(parent)
        self.autosub_cmd = autosub_cmd

    def run(self):
        # Display the loading GIF while the task is in progress
        self.task_start.emit()

        # Run the autosub command
        subprocess.run(self.autosub_cmd, shell=True)

        # Emit the task_complete signal to indicate that the task is complete
        self.task_complete.emit()

class DogeAutoSub(ui_DogeAutoSub.Ui_Dialog, QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.adjustSize()
        # Load and apply the default stylesheet (Dark theme)
        with open("modules/styleSheetDark.css", "r") as file:
            self.setStyleSheet(file.read())
        self.current_theme = "Dark"
        
        # Add a loading label and movie
        self.loading_movie = QMovie("icons/loading.gif")
        
        self.standbyMovie = QMovie("icons/start.gif")
        self.statusimage.setMovie(self.standbyMovie)
        self.standbyMovie.start()
        self.statusLb.setText("Standby")
                
        self.progressBar.setValue(0)
        self.done_pixmap = QPixmap("icons/done.jpg").scaled(130, 150)
        
        self.input_file_button.clicked.connect(self.select_input_file)
        self.output_folder_button.clicked.connect(self.select_output_folder)
        self.start_button.clicked.connect(self.start_subtitle_thread)
        self.model_size_dropdown.currentTextChanged.connect(self.changeModelsinfo)
        
        self.themeBtn.clicked.connect(self.changeThemes)
        
        self.openBtn.clicked.connect(self.open_output_folder)
        
        self.subtitle_thread = None

    def load_stylesheet(self, filename):
        with open(filename, "r") as file:
            self.setStyleSheet(file.read())

    def changeThemes(self):
        if self.current_theme == "Dark":
            with open("modules/styleSheetLight.css", "r") as file:
                self.setStyleSheet(file.read())
            self.current_theme = "Light"
        else:
            with open("modules/styleSheetDark.css", "r") as file:
                self.setStyleSheet(file.read())
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
        # Get the path to the Python executable in the virtual environment
        python_path = os.path.join(sys.prefix, 'Scripts', 'python.exe')

        # Build the autosub command with the selected options
        autosub_cmd = f'"{python_path}" "modules/AutoSub.py" "{input_file_path}" -S "{source_lang}" -D "{target_lang}" -o "{output_folder_path}" -M {modelSize} -E "{engine}"'
        print(autosub_cmd)
        
        # Create and start the subtitle thread
        self.subtitle_thread = SubtitleThread(parent=self, autosub_cmd=autosub_cmd)
        self.subtitle_thread.task_start.connect(self.start_loading_animation)
        self.subtitle_thread.task_complete.connect(self.stop_loading_animation)
        self.subtitle_thread.start()
        
    def changeModelsinfo(self, modelSize):
        # Update VRamUsage and rSpeed based on the selected model size
        if modelSize in MODEL_INFO:
            self.VRamUsage.setText(MODEL_INFO[modelSize]["vram"])
            self.rSpeed.setText(MODEL_INFO[modelSize]["speed"])
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