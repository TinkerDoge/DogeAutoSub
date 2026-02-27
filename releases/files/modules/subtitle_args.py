"""
Subtitle processing arguments dataclass.
Replaces the argparse-based approach for cleaner code.
"""

from dataclasses import dataclass


@dataclass
class SubtitleArgs:
    """Arguments for subtitle generation pipeline."""
    source_path: str
    output_folder: str
    src_language: str = "auto"
    dst_language: str = "en"
    model_size: str = "turbo"
    translate_engine: str = "google"
    volume: int = 3
    mlaas_token: str = ""
