import sys
from modules.uiStyle import Style
from PySide2.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLabel, QComboBox, QFileDialog, QCheckBox
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtGui import QMovie, QPixmap
from PySide2.QtCore import QThread
import subprocess
import os
import UI

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

class DogeAutoSub(UI.Ui_DogeAutoSub, QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.adjustSize()
        style = Style()
        self.input_file_button.setStyleSheet(style.style_bt_standard)
        self.output_folder_button.setStyleSheet(style.style_bt_standard)
        self.output_file_label.setStyleSheet(style.styleLable)
        self.output_file_path_display.setStyleSheet(style.style_bt_standard)
        self.source_language_label.setStyleSheet(style.styleLable)
        self.source_language_dropdown.setStyleSheet(style.style_bt_standard)
        self.target_language_label.setStyleSheet(style.styleLable)
        self.target_language_dropdown.setStyleSheet(style.style_bt_standard)
        self.model_size_label.setStyleSheet(style.styleLable)
        self.model_size_dropdown.setStyleSheet(style.style_bt_standard)
        self.target_engine_label.setStyleSheet(style.styleLable)
        self.target_engine.setStyleSheet(style.style_bt_standard)
        self.start_button.setStyleSheet(style.style_bt_standard)

        # Add a loading label and movie
        self.loading_movie = QMovie("src/loading.gif")
        self.loading_movie.setScaledSize(QtCore.QSize(57.1, 100))
        self.loading_label = QLabel(self)
        self.loading_label.setMovie(self.loading_movie)
        self.loading_movie.start()
        self.loading_label.setAlignment(QtCore.Qt.AlignCenter)
        self.loading_label.setFixedSize(57.1, 100)
        self.loading_label.hide()

        self.processing_label = QLabel("Processing...", self)
        self.processing_label.setStyleSheet(style.ProcessLable)
        self.processing_label.setFixedSize(100, 100)
        self.processing_label.hide()
        
        self.done_notice = QLabel("Done <3 !", self)
        self.done_notice.setStyleSheet(style.ProcessLable)
        self.done_notice.setFixedSize(100, 100)
        self.done_notice.hide()
    
        self.done_pixmap = QPixmap("src/done.jpg").scaled(85.2, 100)
        self.done_label = QLabel(self)
        self.done_label.setPixmap(self.done_pixmap)
        self.done_label.setAlignment(QtCore.Qt.AlignCenter)
        self.done_label.setFixedSize(85.2, 100)
        self.done_label.hide()

        self.brow.addWidget(self.loading_label, 9, 0)
        self.brow.addWidget(self.processing_label, 9, 1)
        self.brow.addWidget(self.done_notice, 9, 1)
        self.brow.addWidget(self.done_label, 9, 0)
        
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
        self.done_label.hide()
        self.done_notice.hide()
        self.loading_label.show()
        self.processing_label.show()
        self.loading_movie.start()

    def stop_loading_animation(self):
        # Stop the loading animation
        self.done_label.show()
        self.done_notice.show()
        self.loading_movie.stop()
        self.loading_label.hide()
        self.processing_label.hide()

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

    def process_audio_file(self):
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