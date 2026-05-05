"""Scale + center-crop the mascot GIFs to 64x64 with a clean palette.

Reads from icons/<name>.gif, writes to icons/mascot/<name>.gif. Uses the
bundled FFmpeg (modules/ffmpeg/bin/ffmpeg.exe) so it works regardless of
the user's PATH.

Usage:
    python scripts/resize_mascot_gifs.py
"""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "icons")
DST_DIR = os.path.join(ROOT, "icons", "mascot")
FFMPEG = os.path.join(ROOT, "modules", "ffmpeg", "bin", "ffmpeg.exe")

EXPECTED = [
    "idle_subtitles",
    "idle_notes",
    "idle_translate",
    "preparing",
    "extracting",
    "transcribing",
    "translating",
    "saving",
    "done",
]

# Scale so the shorter dimension is 64, then center-crop to 64x64.
# Generate a per-clip palette so the dithered output stays clean.
FILTER = (
    "[0:v]scale=64:64:force_original_aspect_ratio=increase:flags=lanczos,"
    "crop=64:64,split[a][b];"
    "[a]palettegen=stats_mode=full[p];"
    "[b][p]paletteuse=dither=sierra2_4a"
)


def main() -> int:
    if not os.path.exists(FFMPEG):
        print(f"ERROR: bundled ffmpeg not found at {FFMPEG}", file=sys.stderr)
        return 2

    os.makedirs(DST_DIR, exist_ok=True)

    failed = []
    for name in EXPECTED:
        src = os.path.join(SRC_DIR, f"{name}.gif")
        dst = os.path.join(DST_DIR, f"{name}.gif")
        if not os.path.exists(src):
            print(f"SKIP  {name}.gif — not in icons/")
            continue
        cmd = [
            FFMPEG, "-y", "-loglevel", "error",
            "-i", src,
            "-filter_complex", FILTER,
            "-loop", "0",
            dst,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FAIL  {name}.gif")
            print(result.stderr)
            failed.append(name)
            continue
        size = os.path.getsize(dst)
        print(f"OK    {name}.gif  ->  {dst}  ({size:,} bytes)")

    if failed:
        print(f"\n{len(failed)} failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    print("\nDone. All mascot GIFs are 64x64 in icons/mascot/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
