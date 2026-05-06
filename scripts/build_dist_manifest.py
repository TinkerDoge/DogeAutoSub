"""Walk dist/DogeAutoSub/ and emit releases/dist_manifest.json.

Each entry is `{relpath: {size, sha256}}` so the installer can stream
individual files and skip ones that already match locally — making fresh
installs resumable across flaky LAN drops.

Run after PyInstaller:
    python scripts/build_dist_manifest.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist", "DogeAutoSub")
OUT = os.path.join(ROOT, "releases", "dist_manifest.json")

sys.path.insert(0, ROOT)
from modules.updater import APP_VERSION  # noqa: E402


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not os.path.isdir(DIST):
        print(f"ERROR: {DIST} not found. Run PyInstaller first.", file=sys.stderr)
        return 2

    files: dict[str, dict] = {}
    total_size = 0
    n = 0
    started = time.time()

    print(f"Scanning {DIST} ...")
    for dirpath, _dirs, filenames in os.walk(DIST):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, DIST).replace("\\", "/")
            size = os.path.getsize(full)
            files[rel] = {"size": size, "sha256": sha256_of(full)}
            total_size += size
            n += 1
            if n % 200 == 0:
                elapsed = time.time() - started
                rate = total_size / elapsed / (1 << 20)
                print(f"  hashed {n:5d} files, {total_size / (1 << 30):6.2f} GB, {rate:5.1f} MB/s")

    manifest = {
        "version": APP_VERSION,
        "total_files": len(files),
        "total_bytes": total_size,
        "files": files,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(manifest, f, indent=2)

    print(
        f"\nWrote {OUT}\n"
        f"  files : {len(files):,}\n"
        f"  size  : {total_size / (1 << 30):.2f} GB\n"
        f"  time  : {time.time() - started:.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
