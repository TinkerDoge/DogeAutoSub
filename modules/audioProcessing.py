import sys
import shlex
import logger
import subprocess
import numpy as np
from os.path import basename
import os
try:
    from shlex import quote
except ImportError:
    from pipes import quote

_logger = logger.setup_applevel_logger(__name__)
script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
ffmpeg_path = os.path.join(script_dir, "ffmpeg", "bin", "ffmpeg.exe")

def extract_audio(input_file, audio_file_name):
    try:
        command = [ffmpeg_path, "-hide_banner", "-loglevel", "warning", "-i", input_file, "-ac", "1", "-ar", "16000",
                   "-vn", "-f", "wav", audio_file_name]
        ret = subprocess.run(command).returncode
        _logger.info(f"Extracted audio to audio/{basename(audio_file_name)}")
    except Exception as e:
        _logger.error(str(e))
        sys.exit(1)


def convert_samplerate(audio_path, desired_sample_rate):
    sox_cmd = "sox {} --type raw --bits 16 --channels 1 --rate {} --encoding signed-integer \
        --endian little --compression 0.0 --no-dither norm -3.0 - ".format(
        quote(audio_path), desired_sample_rate)
    try:
        output = subprocess.check_output(
            shlex.split(sox_cmd), stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"SoX returned non-zero status: {e.stderr}")
    except OSError as e:
        raise OSError(e.errno, f"SoX not found, use {desired_sample_rate}hz files or install it: {e.strerror}")
    return np.frombuffer(output, np.int16)
