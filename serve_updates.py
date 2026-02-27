"""
DogeAutoSub — Update Server
============================
Run this on your machine to serve app updates to users on the LAN.

Usage:
    python serve_updates.py                       # Start server on port 8100
    python serve_updates.py --port 9000           # Custom port
    python serve_updates.py --generate 2.1.0      # Generate manifest + copy files
    python serve_updates.py --generate 2.1.0 --notes "Bug fixes and new features"

Directory structure (auto-created by --generate):
    releases/
    ├── version.json                  ← manifest with file hashes
    ├── files/                        ← individual files for delta patching
    │   ├── AutoUI.py
    │   ├── ui_DogeAutoSub.py
    │   └── modules/
    │       ├── mlaas_client.py
    │       └── ...
    └── DogeAutoSub_v2.1.0.zip       ← full release (optional, for fresh installs)
"""

import argparse
import http.server
import json
import os
import shutil
import socket
import socketserver
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RELEASES_DIR = os.path.join(SCRIPT_DIR, "releases")


def get_local_ip():
    """Get this machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def generate_release(version: str, notes: str = ""):
    """
    Generate a delta-patchable release:
    1. Create version.json with file hashes
    2. Copy patchable files into releases/files/
    """
    # Import the manifest generator from updater module
    sys.path.insert(0, SCRIPT_DIR)
    from modules.updater import generate_manifest, _file_hash

    print(f"\n  Generating release v{version}…\n")

    # Generate manifest
    manifest = generate_manifest(SCRIPT_DIR, version, notes)

    # Save version.json
    os.makedirs(RELEASES_DIR, exist_ok=True)
    manifest_path = os.path.join(RELEASES_DIR, "version.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Copy tracked files into releases/files/
    files_dir = os.path.join(RELEASES_DIR, "files")
    if os.path.exists(files_dir):
        shutil.rmtree(files_dir)

    copied = 0
    for rel_path in manifest["files"]:
        src = os.path.join(SCRIPT_DIR, rel_path.replace("/", os.sep))
        dst = os.path.join(files_dir, rel_path.replace("/", os.sep))

        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1

    print(f"  ✓ Manifest:  {manifest_path}")
    print(f"  ✓ Files dir:  {files_dir}")
    print(f"  ✓ Tracked:    {len(manifest['files'])} files")
    print(f"  ✓ Copied:     {copied} files")

    # Also create the full zip for old clients that don't support delta patching
    import zipfile
    zip_filename = manifest["filename"]
    zip_path = os.path.join(RELEASES_DIR, zip_filename)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path in manifest["files"]:
            src = os.path.join(SCRIPT_DIR, rel_path.replace("/", os.sep))
            if os.path.exists(src):
                zf.write(src, rel_path)
    
    zip_size = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"  ✓ Full zip:   {zip_filename} ({zip_size:.1f} MB)")
    print(f"\n  Release v{version} ready for serving!")
    print(f"  Run: python serve_updates.py\n")


def start_server(port: int):
    """Start the HTTP update server."""
    os.makedirs(RELEASES_DIR, exist_ok=True)

    # Check version.json exists
    manifest_path = os.path.join(RELEASES_DIR, "version.json")
    if not os.path.exists(manifest_path):
        print(f"\n  ⚠ No version.json found in {RELEASES_DIR}")
        print(f"  Run first: python serve_updates.py --generate <version>\n")
        return

    os.chdir(RELEASES_DIR)
    local_ip = get_local_ip()
    handler = http.server.SimpleHTTPRequestHandler

    # Allow port reuse to avoid "address already in use"
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    with ReusableTCPServer(("0.0.0.0", port), handler) as httpd:
        print(f"")
        print(f"  ╔══════════════════════════════════════════════════╗")
        print(f"  ║  DogeAutoSub Update Server                      ║")
        print(f"  ╠══════════════════════════════════════════════════╣")
        print(f"  ║  Serving:  {RELEASES_DIR:<38}║")
        print(f"  ║  URL:      http://{local_ip}:{port:<24}║")
        print(f"  ║  Mode:     Delta Patch (modified files only)     ║")
        print(f"  ╚══════════════════════════════════════════════════╝")
        print(f"")
        print(f"  Press Ctrl+C to stop.")
        print(f"")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")


def main():
    parser = argparse.ArgumentParser(description="DogeAutoSub Update Server")
    parser.add_argument("--port", type=int, default=8100, help="Port (default: 8100)")
    parser.add_argument("--generate", metavar="VERSION", help="Generate release for VERSION (e.g. 2.1.0)")
    parser.add_argument("--notes", default="", help="Release notes (used with --generate)")
    args = parser.parse_args()

    if args.generate:
        generate_release(args.generate, args.notes)
    else:
        start_server(args.port)


if __name__ == "__main__":
    main()
