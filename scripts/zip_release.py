"""Zip the PyInstaller dist/DogeAutoSub/ folder as a full-package release.

Outputs:  releases/DogeAutoSub_v<VERSION>_full.zip

Usage:
    python scripts/zip_release.py
"""
from __future__ import annotations

import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(ROOT, "dist", "DogeAutoSub")
RELEASES_DIR = os.path.join(ROOT, "releases")

sys.path.insert(0, ROOT)
from modules.updater import APP_VERSION  # noqa: E402


def main() -> int:
    if not os.path.isdir(DIST_DIR):
        print(f"ERROR: dist folder not found: {DIST_DIR}", file=sys.stderr)
        print("Run `python -m PyInstaller DogeAutoSubApp.spec --noconfirm` first.",
              file=sys.stderr)
        return 2

    os.makedirs(RELEASES_DIR, exist_ok=True)
    out_path = os.path.join(RELEASES_DIR, f"DogeAutoSub_v{APP_VERSION}_full.zip")

    print(f"Zipping {DIST_DIR} -> {out_path}")
    file_count = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for dirpath, _dirnames, filenames in os.walk(DIST_DIR):
            for fname in filenames:
                src = os.path.join(dirpath, fname)
                # Inside the zip, root the tree at "DogeAutoSub/..." so users
                # extracting it get a single folder, not loose files.
                rel = os.path.relpath(src, os.path.dirname(DIST_DIR))
                zf.write(src, rel)
                file_count += 1

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"\nDone.")
    print(f"  Files:  {file_count:,}")
    print(f"  Size:   {size_mb:.1f} MB")
    print(f"  Path:   {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
