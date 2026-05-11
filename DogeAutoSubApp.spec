# -*- mode: python ; coding: utf-8 -*-
"""
DogeAutoSub v2.2.2 — PyInstaller spec file.
Updated for the cleaned-up module structure (faster-whisper only).
"""
import os

block_cipher = None
binaries = []

current_dir = os.path.dirname(os.path.abspath('AutoUI.py'))

# ── Hidden imports ──────────────────────────────────────────────
hiddenimports = [
    # Core GUI
    'PySide6', 'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui',
    'shiboken6',

    # Audio libraries (faster_whisper will be imported from disk-based modules.faster_whisper_engine)
    'ctranslate2',
    'torch', 'numpy',
    'av',

    # Translation
    'deep_translator',
    'transformers', 'sentencepiece', 'tokenizers', 'sacremoses',

    # Meeting notes
    'docx',

    # Networking / utilities
    'regex', 'requests', 'urllib3', 'certifi',
    'charset_normalizer', 'idna',
    'packaging', 'typing_extensions',
    'filelock', 'fsspec', 'tqdm',
    'huggingface_hub',

    # NOTE: Application modules (ui_DogeAutoSub, modules.*) are intentionally
    # NOT listed here. They are included only as 'datas' (source .py files)
    # so that the auto-updater can replace them on disk and have the changes
    # take effect after restart. If they were in hiddenimports, PyInstaller
    # would compile them into the PYZ archive, making them un-updatable.
]

# ── Data files ──────────────────────────────────────────────────
datas = [
    # Icons and assets
    ('icons', 'icons'),

    # Modules (all app code lives here)
    ('modules/ui_DogeAutoSub.py', 'modules'),

    # Modules
    ('modules/constants.py', 'modules'),
    ('modules/subtitle_args.py', 'modules'),
    ('modules/faster_whisper_engine.py', 'modules'),
    ('modules/chunk_processor.py', 'modules'),
    ('modules/marian_translator.py', 'modules'),
    ('modules/meeting_notes.py', 'modules'),
    ('modules/mlaas_client.py', 'modules'),
    ('modules/updater.py', 'modules'),
    ('modules/subtitle_thread.py', 'modules'),
    ('modules/meeting_notes_thread.py', 'modules'),
    ('modules/translate_thread.py', 'modules'),
    ('modules/styleSheetDark.css', 'modules'),
    ('modules/styleSheetLight.css', 'modules'),

    # New UI modules (v2.4.0 redesign)
    ('modules/theme_tokens.py', 'modules'),
    ('modules/eta_tracker.py', 'modules'),
    ('modules/phase_strip.py', 'modules'),
    ('modules/stripe_widget.py', 'modules'),
    ('modules/palette_menu.py', 'modules'),
    ('modules/mascot.py', 'modules'),
    ('modules/toast.py', 'modules'),
    ('modules/log_panel.py', 'modules'),
    ('modules/log_writer.py', 'modules'),
    ('modules/animations.py', 'modules'),
    ('modules/splash.py', 'modules'),

    # FFmpeg binaries
    ('modules/ffmpeg', 'modules/ffmpeg'),

    # Model cache directories (pre-downloaded models)
    ('modules/models', 'modules/models'),
]

# Include CUDA binaries if present
cuda_dir = os.path.join('modules', 'CUDA')
if os.path.isdir(cuda_dir):
    datas.append((cuda_dir, 'modules/CUDA'))

# Collect faster-whisper (Python source + VAD assets + binaries).
# Using collect_all() puts the Python source on disk as data files so that
# PathFinder can import it at runtime. This is required because the
# faster_whisper/ data directory already exists for the VAD assets — having
# that directory without Python source makes Python treat faster_whisper as
# an empty namespace package, shadowing any frozen copy in PYZ.
try:
    from PyInstaller.utils.hooks import collect_all
    fw_datas, fw_binaries, fw_hidden = collect_all('faster_whisper')
    datas += fw_datas
    binaries += fw_binaries
    hiddenimports += fw_hidden
    print(f"collect_all('faster_whisper'): {len(fw_datas)} datas, {len(fw_binaries)} binaries, {len(fw_hidden)} hidden")
except Exception as e:
    print(f"Warning: collect_all('faster_whisper') failed: {e}")

# Collect numpy (Python source + binary extensions).
# PyInstaller's default hook may miss numpy 2.x source; collect_all ensures
# numpy/__init__.py and subpackage sources are on disk so PathFinder can
# load them. Without this, import numpy finds the numpy/ data directory as
# a namespace package and 'numpy.ndarray' is undefined.
try:
    from PyInstaller.utils.hooks import collect_all
    np_datas, np_binaries, np_hidden = collect_all('numpy')
    datas += np_datas
    binaries += np_binaries
    hiddenimports += np_hidden
    print(f"collect_all('numpy'): {len(np_datas)} datas, {len(np_binaries)} binaries, {len(np_hidden)} hidden")
except Exception as e:
    print(f"Warning: collect_all('numpy') failed: {e}")

# Include config files if they exist
for cfg in ('mlaas_config.json', 'updater_config.json'):
    cfg_path = os.path.join('modules', cfg)
    if os.path.exists(cfg_path):
        datas.append((cfg_path, 'modules'))

# ── Analysis ────────────────────────────────────────────────────
a = Analysis(
    ['AutoUI.py'],
    pathex=[current_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'jupyter', 'IPython', 'notebook',
        'scipy', 'sklearn', 'pandas',
        'whisper',  # Legacy whisper removed
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── Strip app modules from PYZ so they load from disk ───────────
# PyInstaller traces imports and compiles them into a.pure (PYZ archive).
# The PYZ FrozenImporter always takes priority over disk files, which
# prevents the auto-updater from replacing modules at runtime.
# By removing app modules from a.pure, they only exist as data files
# in _internal/ and Python loads them from disk via sys.path.
updatable_modules = {
    'AutoUI',
    'modules', 'modules.ui_DogeAutoSub', 'modules.constants', 'modules.subtitle_args',
    'modules.faster_whisper_engine', 'modules.chunk_processor',
    'modules.marian_translator', 'modules.meeting_notes',
    'modules.mlaas_client', 'modules.updater',
    'modules.subtitle_thread', 'modules.meeting_notes_thread', 'modules.translate_thread',
    # v2.4.0 UI redesign modules
    'modules.theme_tokens', 'modules.eta_tracker', 'modules.phase_strip',
    'modules.stripe_widget', 'modules.palette_menu', 'modules.mascot',
    'modules.toast', 'modules.log_panel', 'modules.log_writer',
    'modules.animations', 'modules.splash',
}

def _exclude_from_pyz(module_name: str) -> bool:
    if module_name in updatable_modules:
        return True
    # Keep these heavy packages on disk to avoid mixed PYZ/disk import paths
    # that can trigger duplicate native module loads in frozen apps.
    if module_name == 'faster_whisper' or module_name.startswith('faster_whisper.'):
        return True
    if module_name == 'numpy' or module_name.startswith('numpy.'):
        return True
    return False

a.pure = [entry for entry in a.pure if not _exclude_from_pyz(entry[0])]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── Executable ──────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DogeAutoSub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,          # Release build: no console window beside the GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/doge.ico',  # Use the .ico file for proper Windows icon
)

# ── Collect ─────────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DogeAutoSub',
)