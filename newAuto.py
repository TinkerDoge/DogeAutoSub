import tkinter as tk
from tkinter import filedialog
from googletrans import Translator
from moviepy.video.io.VideoFileClip import VideoFileClip
import speech_recognition as sr
import os


class VideoSubtitleGenerator:

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Video Subtitle Generator")
        self.file_path = ""
        self.output_folder = ""
        self.output_language = "en"
        self.original_language = ""
        self.translator = Translator()
        self.audio_split_size = 5 * 1024 * 1024  # 5MB in bytes

        self.create_ui()
        self.window.mainloop()  # call mainloop() on the window attribute instead of the instance


    def create_ui(self):
        # Create UI elements
        tk.Label(self.window, text="Choose a video file:").grid(row=0, column=0, sticky="w")
        self.file_button = tk.Button(self.window, text="Browse", command=self.choose_file)
        self.file_button.grid(row=0, column=1)

        tk.Label(self.window, text="Choose an output folder:").grid(row=1, column=0, sticky="w")
        self.folder_button = tk.Button(self.window, text="Browse", command=self.choose_folder)
        self.folder_button.grid(row=1, column=1)

        tk.Label(self.window, text="Choose output language:").grid(row=2, column=0, sticky="w")
        self.languages = ["en", "fr", "es", "jp", "vi"]
        self.output_language = tk.StringVar(value="en")
        self.dropdown = tk.OptionMenu(self.window, self.output_language, *self.languages)
        self.dropdown.grid(row=2, column=1)

        self.start_button = tk.Button(self.window, text="Start", command=self.start)
        self.start_button.grid(row=3, column=0)

        self.progress_label = tk.Label(self.window, text="")
        self.progress_label.grid(row=3, column=1)


    def choose_file(self):
        self.file_path = filedialog.askopenfilename()

    def choose_folder(self):
        self.output_folder = filedialog.askdirectory()

    def start(self):
        if not self.file_path:
            tk.messagebox.showerror("Error", "Please choose a video file")
            return
        if not self.output_folder:
            tk.messagebox.showerror("Error", "Please choose an output folder")
            return

        self.output_language = self.output_language.get()

        # Extract audio from video file
        video = VideoFileClip(self.file_path)
        audio = video.audio.subclip()
        audio_path = os.path.join(self.output_folder, "audio.wav")
        audio.write_audiofile(audio_path)

        # Split audio into smaller files if necessary
        audio_size = os.path.getsize(audio_path)
        if audio_size > self.audio_split_size:
            split_audio_paths = self.split_audio(audio_path)
        else:
            split_audio_paths = [audio_path]

        # Transcribe audio and generate subtitles for each split audio file
        subtitles = []
        for audio_path in split_audio_paths:
            transcription = self.transcribe_audio(audio_path)
            subtitles += self.generate_subtitles(transcription)

        # Translate subtitles if necessary
        if self.output_language != self.original_language:
            subtitles = self.translate_subtitles(subtitles)

        # Write subtitles to file
        subtitles_path = os.path.join(self.output_folder, "subtitles.srt")
        with open(subtitles_path, "w", encoding="utf-8") as f:
            for i, subtitle in enumerate(subtitles):
                f.write(str(i+1) + "\n")
                f.write(subtitle[0] + "\n")
                f.write(subtitle[1] + "\n")
                f.write("\n")

        self.progress_label.config(text="Subtitles generated successfully!")

    def transcribe_audio(self, audio_path):
        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
        
        return recognizer.recognize_google(audio_data, language=self.original_language)

    def generate_subtitles(self, transcription):
        subtitles = []
        # Split the transcription into chunks of 10 seconds
        chunk_size = 10
        chunks = [transcription[i:i+chunk_size] for i in range(0, len(transcription), chunk_size)]
        start_time = 0
        # Generate subtitles for each chunk
        for i, chunk in enumerate(chunks):
            end_time = start_time + chunk_size
            subtitle_text = chunk
            subtitle_time = "{:02d}:{:02d}:{:02d},000 --> {:02d}:{:02d}:{:02d},000".format(
                start_time // 3600, (start_time // 60) % 60, start_time % 60,
                end_time // 3600, (end_time // 60) % 60, end_time % 60)
            subtitle = (subtitle_time, subtitle_text)
            subtitles.append(subtitle)
            start_time = end_time
        return subtitles

    def translate_subtitles(self, subtitles):
        translated_subtitles = []
        for subtitle in subtitles:
            translated_text = self.translator.translate(subtitle[1], dest=self.output_language).text
            translated_subtitles.append((subtitle[0], translated_text))
        return translated_subtitles



if __name__ == "__main__":
    app = VideoSubtitleGenerator()
    app.mainloop()
