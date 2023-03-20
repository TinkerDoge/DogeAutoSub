import argparse
import audioop
import math
import multiprocessing
import os
import subprocess
import sys
import tempfile
import wave
import json
import requests
import speech_recognition as sr
import chardet

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

from deep_translator import GoogleTranslator
from progressbar import ProgressBar, Percentage, Bar, ETA
from constants import GOOGLE_SPEECH_API_KEY, GOOGLE_SPEECH_API_URL,LANGUAGETRANS
from formatters import FORMATTERS

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
ffmpeg_path = os.path.join(script_dir, "ffmpeg", "bin", "ffmpeg.exe")

def percentile(arr, percent):
    arr = sorted(arr)
    k = (len(arr) - 1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c: return arr[int(k)]
    d0 = arr[int(f)] * (c - k)
    d1 = arr[int(c)] * (k - f)
    return d0 + d1


def is_same_language(lang1, lang2):
    return lang1.split("-")[0] == lang2.split("-")[0]

class FLACConverter(object):
    def __init__(self, source_path, include_before=0.25, include_after=0.25):
        self.source_path = source_path
        self.include_before = include_before
        self.include_after = include_after

    def __call__(self, region):
        try:
            start, end = region
            start = max(0, start - self.include_before)
            end += self.include_after
            temp = tempfile.NamedTemporaryFile(suffix='.flac')
            temp.close()
            command = [ffmpeg_path, "-y", "-i" , self.source_path, "-ss", str(start), "-t", str(end-start),"-loglevel", "error", temp.name]
            subprocess.check_output(command)
            return open(temp.name, "rb").read()

        except KeyboardInterrupt:
            return

class SpeechRecognizerGG:
    def __init__(self,audioFile = "audio_filename"):
        self.audioFile = audioFile
        
    def __call__(self):
        try:
            r = sr.Recognizer()
            with sr.AudioFile(self.audioFile) as source:
                audio = r.record(source)
                text = r.recognize_google(audio)
                for transcript in text().split("\n"):
                    try:
                        transcript = json.loads(transcript)
                        return transcript['result'][0]['alternative'][0]['transcript'].capitalize()
                    except:
                    # no result
                        continue
        except KeyboardInterrupt:
            return

class SpeechRecognizer(object):
    def __init__(self, language="en", rate=44100, retries=3, api_key=GOOGLE_SPEECH_API_KEY):
        self.language = language
        self.rate = rate
        self.api_key = api_key
        self.retries = retries

    def __call__(self, data):
        try:
            for i in range(self.retries):
                url = GOOGLE_SPEECH_API_URL.format(lang=self.language, key=self.api_key)
                headers = {"Content-Type": "audio/x-flac; rate=%d" % self.rate}

                try:
                    resp = requests.post(url, data=data, headers=headers)
                except requests.exceptions.ConnectionError:
                    continue

                for line in resp.content.decode().split("\n"):
                    try:
                        line = json.loads(line)
                        return line['result'][0]['alternative'][0]['transcript'].capitalize()
                    except:
                        # no result
                        continue

        except KeyboardInterrupt:
            return

def extract_audio(filename, channels=1, rate=44100, volume="6"):
    temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    command = [ffmpeg_path, "-y", "-i", filename, "-ac", str(channels), "-ar", str(rate),'-filter:a', f"volume={volume}","-loglevel", "error", temp.name]
    subprocess.check_output(command, shell=True)
    return temp.name, rate
    
def find_speech_regions(filename, frame_width=3500 , min_region_size=0.4, max_region_size=12):

    reader = wave.open(filename)
    sample_width = reader.getsampwidth()
    rate = reader.getframerate()
    n_channels = reader.getnchannels()

    total_duration = reader.getnframes() / rate
    chunk_duration = float(frame_width) / rate

    n_chunks = int(total_duration / chunk_duration)
    energies = []

    for i in range(n_chunks):
        chunk = reader.readframes(frame_width)
        energies.append(audioop.rms(chunk, sample_width * n_channels))

    threshold = percentile(energies, 0.2)

    elapsed_time = 0

    regions = []
    region_start = None

    for energy in energies:
        elapsed_time += chunk_duration

        is_silence = energy <= threshold
        max_exceeded = region_start and elapsed_time - region_start >= max_region_size

        if (max_exceeded or is_silence) and region_start:
            if elapsed_time - region_start >= min_region_size:
                regions.append((region_start, elapsed_time))
            region_start = None

        elif (not region_start) and (not is_silence):
            region_start = elapsed_time

    return regions

def languagecode_tranform(language="en-US"):
    if language in LANGUAGETRANS:
        return LANGUAGETRANS[language]
    else:
        return language

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="Path to the video or audio file to subtitle", nargs='?')
    parser.add_argument('-C', '--concurrency', help="Number of concurrent API requests to make", type=int, default=10)
    parser.add_argument('-o', '--output')
    parser.add_argument('-F', '--format', help="Destination subtitle format", default="srt")
    parser.add_argument('-S', '--src-language', help="Language spoken in source file", default="en")
    parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles", default="en")
    args = parser.parse_args()

    if not args.source_path:
        print("Error: You need to specify a source path.")
        return 1

    audio_filename, audio_rate = extract_audio(args.source_path)
    regions = find_speech_regions(audio_filename)
    codeTransSrc = languagecode_tranform(language=args.src_language)
    codeTransTgr = languagecode_tranform(language=args.dst_language)
    pool = multiprocessing.Pool(args.concurrency)
    converter = FLACConverter(source_path=audio_filename)
    recognizer = SpeechRecognizer(language=args.src_language, rate=audio_rate, api_key=GOOGLE_SPEECH_API_KEY)
    recognizerGG = SpeechRecognizerGG(audioFile = audio_filename)

    transcripts = []
    if regions:
        try:
            widgets = ["Converting speech regions to FLAC files: ", Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()
            extracted_regions = []
            for i, extracted_region in enumerate(pool.imap(converter, regions)):
                extracted_regions.append(extracted_region)
                pbar.update(i)
            pbar.finish()

            widgets = ["Performing speech recognition: ", Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()

            if not is_same_language(args.src_language, args.dst_language):
                    translator = GoogleTranslator(source=codeTransSrc,target=codeTransTgr)
                    prompt = "Translating from {0} to {1}: ".format(args.src_language,args.dst_language)
                    widgets = [prompt, Percentage(), ' ', Bar(), ' ', ETA()]
                    pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()
                    translated = []
                    for i, transcript in enumerate(pool.imap(recognizer, extracted_regions)):
                        if transcript is not None:
                            translated = translator.translate(transcript)
                            transcripts.append(translated)
                        else:
                            transcripts.append(transcript)
                        pbar.update(i)
                    pbar.finish()
            else:
                for i, transcript in enumerate(pool.imap(recognizer, extracted_regions)):
                    transcripts.append(transcript)
                    pbar.update(i)
                pbar.finish()
            print(transcripts)

        except KeyboardInterrupt:
            pbar.finish()
            pool.terminate()
            pool.join()
            print("Cancelling transcription")
            return 1

    timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]
    formatter = FORMATTERS.get(args.format)
    formatted_subtitles = formatter(timed_subtitles)
    dest = args.output

    if not dest:
        base, ext = os.path.splitext(args.source_path)
        dest = "{base}.{format}".format(base=base, format=args.format)

    if os.path.isdir(dest):
        base_name = os.path.basename(args.source_path)
        file_name = os.path.splitext(base_name)[0]  # Remove .mp4 extension from file name
        dest = os.path.join(dest, file_name + '.' + args.dst_language + '.' + args.format)

        with open(dest, "w", encoding="utf-8") as f:
             f.write(formatted_subtitles)

    print("Subtitles file created at {}".format(dest))
    os.remove(audio_filename)
    return 0

if __name__ == '__main__':
    sys.exit(main())
