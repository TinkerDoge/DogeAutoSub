import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import datetime
import os
import moviepy.editor as mp
import tempfile
import speech_recognition as sr
from moviepy.editor import *
from googletrans import Translator
from pydub import AudioSegment
import math

class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):

        # Set window size
        self.master.geometry("420x240")

        # Input file selection button
        self.input_file_button = tk.Button(self, text="Select Input File", command=self.select_input_file)
        self.input_file_button.configure(background='#2E4053', foreground='white', padx=10, pady=10)
        self.input_file_button.pack(side="top")


        # Output folder selection button
        self.output_folder_button = tk.Button(self, text="Select Output Folder", command=self.select_output_folder)
        self.output_folder_button.configure(background='#2E4053', foreground='white', padx=10, pady=10)
        self.output_folder_button.pack(side="top")

        # Output file path label
        self.output_file_label = tk.Label(self, text="Output File Path:")
        self.output_file_label.pack()
            
        # Output file path display
        self.output_file_path_display = tk.Label(self, text="No folder selected")
        self.output_file_path_display.pack()

        # Language selection dropdown
        self.language_label = tk.Label(self, text="Target Language:")
        self.language_label.pack()
        self.language_var = tk.StringVar(self)
        self.language_var.set("en")  # Default value
        self.language_dropdown = tk.OptionMenu(self, self.language_var, "en", "es", "fr", "de", "ja", "ko", "vi")
        self.language_dropdown.pack()

        # Transcription and translation start button
        self.start_button = tk.Button(self, text="Start", command=self.process_audio_file)
        self.start_button.configure(background='#2E4053', foreground='white', padx=10, pady=10)
        self.start_button.pack(side="bottom")
        
    def select_input_file(self):
        # Allow the user to select the input movie file
        self.input_file_path = filedialog.askopenfilename(title="Select Movie File", filetypes=[("Movie Files", "*.mp4 *.avi *.mkv *.mov")])
            
    def select_output_folder(self):
        # Allow the user to select the output folder
        self.output_folder_path = filedialog.askdirectory()
        self.output_file_path_display.configure(text=self.output_folder_path)

    def process_audio_file(self):
        # Use moviepy to extract audio from the movie file and convert it to the required format
        output_audio_file_path = self.input_file_path.replace(".mp4", ".wav")
        video = VideoFileClip(self.input_file_path)
        audio = video.audio
        audio.write_audiofile(output_audio_file_path)

        # Split the audio file into smaller parts if it is larger than 5 MB
        max_file_size = 5 * 1024 * 1024  # 5 MB in bytes
        audio_file_size = os.path.getsize(output_audio_file_path)
        output_folder_path = self.input_file_path
        if audio_file_size > max_file_size:
            # Split the audio file and create a list of the split files
            split_audio_files = self.split_audio_file(output_audio_file_path,max_file_size,output_folder_path)
        else:
            split_audio_files = [output_audio_file_path]

        # Load the audio files and transcribe them using Google Speech API
        r = sr.Recognizer()
        subtitle_text = ""
        start_time = 0
        for i, split_audio_file_path in enumerate(split_audio_files):
            with sr.AudioFile(split_audio_file_path) as source:
                audio_data = r.record(source)
            transcript = r.recognize_google(audio_data)

            # Format the transcribed text into the .srt format
            end_time = start_time + len(transcript)
            subtitle_text += f"{i+1}\n{datetime.timedelta(seconds=start_time)} --> {datetime.timedelta(seconds=end_time)}\n{transcript}\n\n"
            start_time = end_time + 1

        # Allow the user to select a location to save the subtitle file
        if self.output_folder_path == "No folder selected":
            # Display an error message if no output folder has been selected
            messagebox.showerror("Error", "Please select an output folder")
        else:
            # Save the subtitle text to a file
            translator = Translator()
            target_language = self.language_var.get()
            translated_text = translator.translate(subtitle_text, dest=target_language).text
            output_file_path = os.path.join(self.output_folder_path, f"{os.path.basename(self.input_file_path)}.srt")
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(translated_text)

    def split_audio_file(input_file_path, max_file_size, output_folder_path):
        audio = AudioSegment.from_file(input_file_path)
        num_segments = math.ceil(len(audio) / max_file_size)
        segment_size = len(audio) // num_segments
        segments = [audio[i*segment_size:(i+1)*segment_size] for i in range(num_segments)]
        output_files = []
        for i, segment in enumerate(segments):
            output_file_path = os.path.join(output_folder_path, f"part_{i+1}.wav")
            segment.export(output_file_path, format="wav")
            output_files.append(output_file_path)
        return output_files

if __name__ == "__main__":
    root = tk.Tk()
    app = App(master=root)
    app.mainloop()
