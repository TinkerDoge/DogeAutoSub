import sys
from uiStyle import Style
import PySide2
from PySide2.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLabel, QComboBox, QFileDialog
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtGui import QMovie
from PySide2.QtCore import QThread
import subprocess
import os

class SubtitleThread(QThread):
    task_complete = QtCore.Signal()
    task_start = QtCore.Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
    
    def run(self):
        # Display the loading GIF while the task is in progress
        self.task_start.emit()

        # Do the task here
        self.parent.process_audio_file()

        # Emit the task_complete signal to indicate that the task is complete
        self.task_complete.emit()


class DogeAutoSub(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create an instance of the Style class
        style = Style()
        # Set the size and position of the window
        self.setWindowTitle("Doge AutoSub")
        self.setWindowIcon(QtGui.QIcon("icons/favicon.png"))
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.adjustSize()
        self.setStyleSheet(
            """
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop: 0 grey, stop: 1 grey);
            border-radius: 10px;
            """
        )



        # Create a grid layout
        mainlayout = QtWidgets.QGridLayout()
        mainlayout.setSpacing(8)
        self.setLayout(mainlayout)

        trow = QtWidgets.QGridLayout()
        trow.setSpacing(8)
        mainlayout.addLayout(trow,4,0,2,1)
        
        brow = QtWidgets.QGridLayout()
        brow.setSpacing(8)
        mainlayout.addLayout(brow,8,0,2,1)
        
        # Initialize widgets
        self.input_file_button = QPushButton("SELECT INPUT", self)
        self.input_file_button.setStyleSheet(style.style_bt_standard)
        # Output folder selection button
        self.output_folder_button = QPushButton("OUTPUT FOLDER", self)
        self.output_folder_button.setStyleSheet(style.style_bt_standard)
        # Output file path label
        self.output_file_label = QLabel("Output File Path:", self)
        self.output_file_label.setStyleSheet(style.styleLable)
        # Output file path display
        self.output_file_path_display = QLabel("No folder selected", self)
        self.output_file_path_display.setStyleSheet(style.style_bt_standard)
        # Language selection dropdown for source language
        self.source_language_label = QLabel("Source Language:", self)
        self.source_language_label.setStyleSheet(style.styleLable)
        self.source_language_dropdown = QComboBox(self)
        self.source_language_dropdown.setStyleSheet(style.style_bt_standard)
        self.source_language_dropdown.addItems(["en","fr", "ja", "zh-CN","zh-TW","vi"])
        # Language selection dropdown for target language
        self.target_language_label = QLabel("Translate to:", self)
        self.target_language_label.setStyleSheet(style.styleLable)
        self.target_language_dropdown = QComboBox(self)
        self.target_language_dropdown.setStyleSheet(style.style_bt_standard)
        self.target_language_dropdown.addItems(["en","fr", "ja", "zh-CN","zh-TW", "vi"])
        # Transcription and translation start button
        self.start_button = QPushButton("START", self)
        self.start_button.setStyleSheet(style.style_bt_standard)

        # Add a loading label and movie
        self.loading_movie = QMovie("src/loading.gif")
        self.loading_movie.setScaledSize(QtCore.QSize(100, 100))
        self.loading_label = QLabel(self)
        self.loading_label.setMovie(self.loading_movie)
        self.loading_movie.start()
        self.loading_label.setAlignment(QtCore.Qt.AlignCenter)
        self.loading_label.setFixedSize(100, 100)
        self.loading_label.hide()

        self.processing_label = QLabel("Processing...", self)
        self.processing_label.setStyleSheet(style.styleLable)
        self.processing_label.setFixedSize(100, 100)
        self.processing_label.hide()

        self.input_file_button.setFixedSize(300, 30)
        self.output_folder_button.setFixedSize(300, 30)
        self.output_file_label.setFixedSize(150, 50)
        self.output_file_path_display.setFixedSize(300, 30)
        self.source_language_label.setFixedSize(150, 30)
        self.source_language_dropdown.setFixedSize(140, 30)
        self.target_language_label.setFixedSize(120, 30)
        self.target_language_dropdown.setFixedSize(140, 30)
        self.start_button.setFixedSize(300, 30)

        mainlayout.addWidget(self.input_file_button, 0,0)
        mainlayout.addWidget(self.output_folder_button, 1,0)
        mainlayout.addWidget(self.output_file_label, 2,0)
        mainlayout.addWidget(self.output_file_path_display, 3,0)
        trow.addWidget(self.source_language_label, 4,0)
        trow.addWidget(self.target_language_label, 4,1)
        trow.addWidget(self.source_language_dropdown, 5,0)
        trow.addWidget(self.target_language_dropdown, 5,1)
        mainlayout.addWidget(self.start_button, 6,0)
        brow.addWidget(self.loading_label, 9,0)
        brow.addWidget(self.processing_label, 9,1)

        self.input_file_button.clicked.connect(self.select_input_file)
        self.output_folder_button.clicked.connect(self.select_output_folder)
        self.start_button.clicked.connect(self.start_subtitle_thread)
        
        self.subtitle_thread = SubtitleThread(self)
        self.subtitle_thread.task_start.connect(self.start_loading_animation)
        self.subtitle_thread.task_complete.connect(self.stop_loading_animation)

    def start_subtitle_thread(self):
        # Start the subtitle thread
        self.subtitle_thread.start()
        
    def start_loading_animation(self):
        # start the loading animation
        self.loading_label.show()
        self.processing_label.show()
        self.loading_movie.start()

    def stop_loading_animation(self):
        # Stop the loading animation
        self.loading_movie.stop()
        self.loading_label.hide()
        self.processing_label.hide()

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
        python_path = os.path.join(sys.prefix, 'Scripts', 'python.exe')

        # Build the autosub command with the selected options
        autosub_cmd = f"{python_path} AutoSub.py {input_file_path} -S {source_lang} -D {target_lang} -o {output_folder_path}"

        # Run the autosub command
        subprocess.run(autosub_cmd, shell=True)
        
        # Update the output file path display with the path of the generated subtitle file
        output_file_path = f"{output_folder_path}/{os.path.splitext(os.path.basename(input_file_path))[0]}.{target_lang}.srt"
        self.output_file_path_display.setText(output_file_path)
        

if __name__ == '__main__':
    app = QApplication([])
    doge = DogeAutoSub()
    doge.show()
    app.exec_()