import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QComboBox, QLabel, QPushButton, QFileDialog
import subprocess
import os

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Transcription and Translation")
        self.setGeometry(100, 100, 240, 300)
        self.initUI()

    def initUI(self):
        # Input file selection button
        self.input_file_button = QPushButton("Select Input File", self)
        self.input_file_button.setGeometry(20, 20, 200, 50)
        self.input_file_button.setStyleSheet("background-color: #2E4053; color: white; padding: 10px;")
        self.input_file_button.clicked.connect(self.select_input_file)

        # Output folder selection button
        self.output_folder_button = QPushButton("Select Output Folder", self)
        self.output_folder_button.setGeometry(20, 80, 200, 50)
        self.output_folder_button.setStyleSheet("background-color: #2E4053; color: white; padding: 10px;")
        self.output_folder_button.clicked.connect(self.select_output_folder)

        # Output file path label
        self.output_file_label = QLabel("Output File Path:", self)
        self.output_file_label.setGeometry(20, 140, 100, 20)

        # Output file path display
        self.output_file_path_display = QLabel("No folder selected", self)
        self.output_file_path_display.setGeometry(130, 140, 200, 20)

        # Language selection dropdown for target language
        self.target_language_label = QLabel("Target Language:", self)
        self.target_language_label.setGeometry(20, 170, 100, 20)
        self.target_language_dropdown = QComboBox(self)
        self.target_language_dropdown.setGeometry(130, 170, 100, 20)
        self.target_language_dropdown.addItems(["en","fr", "ja", "zh-CN","zh-TW", "vi"])

        # Language selection dropdown for source language
        self.source_language_label = QLabel("Source Language:", self)
        self.source_language_label.setGeometry(20, 200, 100, 20)
        self.source_language_dropdown = QComboBox(self)
        self.source_language_dropdown.setGeometry(130, 200, 100, 20)
        self.source_language_dropdown.addItems(["en","fr", "ja", "zh-CN","zh-TW","vi"])

        # Transcription and translation start button
        self.start_button = QPushButton("Start", self)
        self.start_button.setGeometry(20, 240, 200, 30)
        self.start_button.setStyleSheet("background-color: #2E4053; color: white; padding: 10px;")
        self.start_button.clicked.connect(self.process_audio_file)

    def select_input_file(self):
        # Allow the user to select the input movie file
        self.input_file_path, _ = QFileDialog.getOpenFileName(self, "Select Movie File", "", "Movie Files (*.mp4 *.avi *.mkv *.mov)")
        if self.input_file_path:
            self.input_file_button.setText(os.path.basename(self.input_file_path))

    def select_output_folder(self):
        # Allow the user to select the output folder
        self.output_folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if self.output_folder_path:
            self.output_file_path_display.setText(self.output_folder_path)

    def process_audio_file(self):
        # Get selected file path and output folder path
        input_file_path = self.input_file_path
        output_folder_path = self.output_folder_path

        # Get selected source and target languages
        source_lang = self.source_language_dropdown.currentText()
        target_lang = self.target_language_dropdown.currentText()

        # Get the path to the Python executable in the virtual environment
        python_path = os.path.join(sys.prefix, 'bin', 'python')

        # Build the autosub command with the selected options
        autosub_cmd = f"{python_path} AutoSub.py {input_file_path} -S {source_lang} -D {target_lang} -o {output_folder_path}"

        # Run the autosub command
        subprocess.run(autosub_cmd, shell=True)

        # Update the output file path display with the path of the generated subtitle file
        output_file_path = f"{output_folder_path}/{os.path.splitext(os.path.basename(input_file_path))[0]}.{target_lang}.srt"
        self.output_file_path_display.setText(output_file_path)
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())


