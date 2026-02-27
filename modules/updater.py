import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
import zipfile
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

# ── Current app version ─────────────────────────────────────────
APP_VERSION = "2.0.6"

# Default update server — override in updater_config.json
DEFAULT_UPDATE_URL = "http://10.76.171.156:8100"


@dataclass
class UpdateInfo:
    """Information about an available update."""
    version: str
    filename: str
    download_url: str
    notes: str = ""
    is_newer: bool = False
    files: Dict[str, str] = field(default_factory=dict)  # path → hash


def _version_tuple(v: str) -> tuple:
    """Convert version string to comparable tuple: '2.1.0' → (2, 1, 0)"""
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, IOError):
        return ""


def get_app_dir() -> str:
    """Get the root directory where Python files live.
    
    For PyInstaller --onedir builds, files are in <exe_dir>/_internal/
    For dev mode, files are in the project root (parent of modules/).
    """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        internal = os.path.join(exe_dir, "_internal")
        if os.path.isdir(internal):
            return internal
        return exe_dir
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_update_server_url() -> str:
    """Load update server URL from config, or use default."""
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "updater_config.json"
    )
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            return data.get("update_url", DEFAULT_UPDATE_URL).rstrip("/")
        except Exception:
            pass
    return DEFAULT_UPDATE_URL


def save_update_server_url(url: str):
    """Save update server URL to config."""
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "updater_config.json"
    )
    try:
        data = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
        data["update_url"] = url.rstrip("/")
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to save update URL: {e}")


# ── Check for Updates ───────────────────────────────────────────

def check_for_update(
    server_url: Optional[str] = None,
    timeout: int = 5,
) -> Optional[UpdateInfo]:
    """
    Check the update server for a newer version.
    Returns UpdateInfo if newer version available, None otherwise.
    """
    url = (server_url or get_update_server_url()).rstrip("/")
    manifest_url = f"{url}/version.json"

    try:
        req = urllib.request.Request(manifest_url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as e:
        print(f"Update check skipped: {e}")
        return None

    remote_version = data.get("version", "0.0.0")
    filename = data.get("filename", "")
    notes = data.get("notes", "")
    files = data.get("files", {})

    if _version_tuple(remote_version) > _version_tuple(APP_VERSION):
        return UpdateInfo(
            version=remote_version,
            filename=filename,
            download_url=f"{url}/{filename}",
            notes=notes,
            is_newer=True,
            files=files,
        )

    return None


# ── Delta Patch (only modified files) ───────────────────────────

def get_changed_files(update: UpdateInfo, app_dir: Optional[str] = None) -> List[str]:
    """
    Compare remote file hashes with local files.
    Returns list of relative paths that need updating.
    """
    if not update.files:
        return []

    app_dir = app_dir or get_app_dir()
    changed = []

    for rel_path, remote_hash in update.files.items():
        local_path = os.path.join(app_dir, rel_path.replace("/", os.sep))
        local_hash = _file_hash(local_path) if os.path.exists(local_path) else ""
        if local_hash != remote_hash:
            changed.append(rel_path)

    return changed


def download_delta_patch(
    update: UpdateInfo,
    app_dir: Optional[str] = None,
    server_url: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> bool:
    """
    Download only modified files from the server's files/ directory.
    
    Server structure:
        releases/
        ├── version.json
        └── files/
            ├── AutoUI.py
            ├── ui_DogeAutoSub.py
            ├── modules/
            │   ├── mlaas_client.py
            │   └── ...
    """
    app_dir = app_dir or get_app_dir()
    url = (server_url or get_update_server_url()).rstrip("/")

    changed = get_changed_files(update, app_dir)

    if not changed:
        if progress_callback:
            progress_callback("All files are up to date.")
        return True

    total = len(changed)
    if progress_callback:
        progress_callback(f"Patching {total} modified file(s)…")

    success_count = 0
    for i, rel_path in enumerate(changed):
        file_url = f"{url}/files/{rel_path}"
        local_path = os.path.join(app_dir, rel_path.replace("/", os.sep))

        if progress_callback:
            progress_callback(f"Updating ({i+1}/{total}): {rel_path}")

        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Download to temp file first, then move atomically
            tmp_path = local_path + ".tmp"
            urllib.request.urlretrieve(file_url, tmp_path)

            # Replace the file
            try:
                if os.path.exists(local_path):
                    os.replace(tmp_path, local_path)
                else:
                    os.rename(tmp_path, local_path)
                success_count += 1
            except PermissionError:
                # File is locked (e.g., running exe)
                pending_path = local_path + ".update_pending"
                os.replace(tmp_path, pending_path)
                print(f"Pending update for locked file: {rel_path}")
                success_count += 1

        except Exception as e:
            print(f"Failed to update {rel_path}: {e}")
            # Clean up temp file
            tmp_path = local_path + ".tmp"
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    if progress_callback:
        progress_callback(f"Patched {success_count}/{total} files → v{update.version} ✓")

    return success_count > 0


# ── Full Update (zip) ───────────────────────────────────────────

def download_full_update(
    update: UpdateInfo,
    app_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> bool:
    """Download the full update zip and extract over current install."""
    app_dir = app_dir or get_app_dir()

    if progress_callback:
        progress_callback(f"Downloading {update.filename}…")

    tmp_dir = tempfile.mkdtemp(prefix="dogeautosub_update_")
    zip_path = os.path.join(tmp_dir, update.filename)

    try:
        urllib.request.urlretrieve(update.download_url, zip_path)
    except Exception as e:
        if progress_callback:
            progress_callback(f"Download failed: {e}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return False

    if progress_callback:
        progress_callback("Extracting update…")

    extract_dir = os.path.join(tmp_dir, "extracted")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except Exception as e:
        if progress_callback:
            progress_callback(f"Extract failed: {e}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return False

    if progress_callback:
        progress_callback("Applying update…")

    # Find source root (step into single folder if present)
    items = os.listdir(extract_dir)
    source_dir = extract_dir
    if len(items) == 1 and os.path.isdir(os.path.join(extract_dir, items[0])):
        source_dir = os.path.join(extract_dir, items[0])

    # Skip directories and config files that should be preserved
    skip_dirs = {".venv", "__pycache__", ".git", "build", "dist", "DOCs", "releases"}
    skip_files = {"updater_config.json", "mlaas_config.json"}

    try:
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            rel_root = os.path.relpath(root, source_dir)
            target_root = os.path.join(app_dir, rel_root) if rel_root != "." else app_dir
            os.makedirs(target_root, exist_ok=True)

            for file in files:
                if file in skip_files:
                    continue
                src = os.path.join(root, file)
                dst = os.path.join(target_root, file)
                try:
                    shutil.copy2(src, dst)
                except PermissionError:
                    pending = dst + ".update_pending"
                    shutil.copy2(src, pending)
                    print(f"Pending update for locked file: {file}")
    except Exception as e:
        if progress_callback:
            progress_callback(f"Apply failed: {e}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return False

    shutil.rmtree(tmp_dir, ignore_errors=True)

    if progress_callback:
        progress_callback(f"Updated to v{update.version} ✓")

    return True


# ── Smart Update (delta if possible, full as fallback) ──────────

def download_and_apply_update(
    update: UpdateInfo,
    app_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> bool:
    """
    Apply update using the best strategy:
    - If version.json has a 'files' manifest → delta patch (only changed files)
    - Otherwise → full zip download
    """
    if update.files:
        # Delta patch mode
        if progress_callback:
            progress_callback("Using delta patch (modified files only)…")
        return download_delta_patch(update, app_dir, progress_callback=progress_callback)
    else:
        # Full update fallback
        if progress_callback:
            progress_callback("Using full update…")
        return download_full_update(update, app_dir, progress_callback=progress_callback)


# ── Restart ─────────────────────────────────────────────────────

def restart_app():
    """Restart the application after an update."""
    python = sys.executable
    script = os.path.abspath(sys.argv[0])

    if getattr(sys, 'frozen', False):
        subprocess.Popen([script] + sys.argv[1:])
    else:
        subprocess.Popen([python, script] + sys.argv[1:])

    sys.exit(0)


# ── Manifest Generator (run on server to create version.json) ───

def generate_manifest(
    app_dir: str,
    version: str,
    notes: str = "",
    zip_filename: str = "",
) -> dict:
    """
    Generate a version.json manifest with file hashes for delta patching.
    Run this on the server side to create the manifest.
    
    Usage:
        python -c "from modules.updater import generate_manifest; ..."
        
    Or use the serve_updates.py --generate flag.
    """
    manifest = {
        "version": version,
        "filename": zip_filename or f"DogeAutoSub_v{version}.zip",
        "notes": notes,
        "files": {},
    }

    skip_dirs = {".venv", "__pycache__", ".git", "build", "dist",
                 "DOCs", "releases", "temp", "models", "CUDA", "ffmpeg",
                 "marian_cache", "QTDesign", ".no_exist", "snapshots"}
    skip_files = {"updater_config.json", "mlaas_config.json",
                  "Thumbs.db", ".gitignore", "serve_updates.py",
                  "build.bat", "DogeAutoSubApp.spec", "requirements.txt",
                  "subtitle_translator_app.py"}
    include_exts = {".py", ".css", ".json", ".ico", ".png", ".jpg", ".gif"}

    for root, dirs, files in os.walk(app_dir):
        # Filter by directory NAME directly
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if file in skip_files:
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext not in include_exts:
                continue

            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, app_dir).replace("\\", "/")
            manifest["files"][rel_path] = _file_hash(filepath)

    return manifest


if __name__ == "__main__":
    """Run directly to generate a manifest for the current codebase."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate update manifest")
    parser.add_argument("--version", required=True, help="Version string (e.g. 2.1.0)")
    parser.add_argument("--notes", default="", help="Release notes")
    parser.add_argument("--dir", default=None, help="App directory (default: auto-detect)")
    parser.add_argument("--output", default="releases/version.json", help="Output path")
    args = parser.parse_args()

    app_dir = args.dir or get_app_dir()
    manifest = generate_manifest(app_dir, args.version, args.notes)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated manifest: {args.output}")
    print(f"  Version: {args.version}")
    print(f"  Files tracked: {len(manifest['files'])}")
