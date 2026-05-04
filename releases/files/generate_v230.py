"""
Quick script to generate version.json and copy delta files for v2.3.0 update.
Run: python generate_v230.py
"""
import hashlib
import json
import os
import shutil

VERSION = "2.3.0"
NOTES = "v2.3.0 - Added GPT-4o Mini as alternative AI translation engine via MLAAS OpenAI proxy. Engine dropdown now shows model names (Claude Sonnet 4, GPT-4o Mini, Google Translate, Whisper). Removed Marian translator."

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def file_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ── Generate manifest ────────────────────────────────────────────
from modules.updater import generate_manifest

manifest = generate_manifest(SCRIPT_DIR, VERSION, NOTES)

# Write version.json
out_path = os.path.join(SCRIPT_DIR, "releases", "version.json")
with open(out_path, "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Generated: {out_path}")
print(f"  Version: {VERSION}")
print(f"  Files tracked: {len(manifest['files'])}")

# ── Copy delta files ─────────────────────────────────────────────
# Load old manifest to find what changed
old_manifest_path = os.path.join(SCRIPT_DIR, "releases", "version_old.json")
if not os.path.exists(old_manifest_path):
    print("\nNo old manifest found. Showing ALL files that would be served:")
    for rel_path in sorted(manifest["files"].keys()):
        print(f"  {rel_path}")
    print(f"\nTotal: {len(manifest['files'])} files")
else:
    with open(old_manifest_path) as f:
        old = json.load(f)
    old_files = old.get("files", {})

    changed = []
    for rel_path, new_hash in manifest["files"].items():
        old_hash = old_files.get(rel_path, "")
        if old_hash != new_hash:
            changed.append(rel_path)

    print(f"\n{'='*50}")
    print(f"DELTA FILES (changed since v{old.get('version', '?')}):")
    print(f"{'='*50}")

    files_dir = os.path.join(SCRIPT_DIR, "releases", "files")
    os.makedirs(files_dir, exist_ok=True)

    for rel_path in sorted(changed):
        src = os.path.join(SCRIPT_DIR, rel_path)
        dst = os.path.join(files_dir, rel_path.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  ✓ {rel_path}")

    print(f"\nCopied {len(changed)} files to releases/files/")

print("\nDone! You can now push releases/ to the update server.")
