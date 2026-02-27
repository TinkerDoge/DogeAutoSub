# -*- mode: python ; coding: utf-8 -*-
"""
DogeAutoSub v2.0 — PyInstaller spec file.
Updated for the cleaned-up module structure (faster-whisper only).
"""
import os

block_cipher = None

current_dir = os.path.dirname(os.path.abspath('AutoUI.py'))

# ── Hidden imports ──────────────────────────────────────────────
hiddenimports = [
    # Core GUI
    'PySide6', 'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui',
    'shiboken6',

    # Faster-whisper + audio
    'faster_whisper', 'ctranslate2',
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

    # Application modules
    'ui_DogeAutoSub',
    'modules.constants',
    'modules.subtitle_args',
    'modules.faster_whisper_engine',
    'modules.chunk_processor',
    'modules.transcribe',
    'modules.audio',
    'modules.marian_translator',
    'modules.meeting_notes',
    'modules.mlaas_client',
    'modules.updater',
]

# ── Data files ──────────────────────────────────────────────────
datas = [
    # Icons and assets
    ('icons', 'icons'),

    # Python source files needed at runtime
    ('ui_DogeAutoSub.py', '.'),

    # Modules
    ('modules/constants.py', 'modules'),
    ('modules/subtitle_args.py', 'modules'),
    ('modules/faster_whisper_engine.py', 'modules'),
    ('modules/chunk_processor.py', 'modules'),
    ('modules/marian_translator.py', 'modules'),
    ('modules/meeting_notes.py', 'modules'),
    ('modules/mlaas_client.py', 'modules'),
    ('modules/transcribe.py', 'modules'),
    ('modules/updater.py', 'modules'),
    ('modules/audio.py', 'modules'),
    ('modules/styleSheetDark.css', 'modules'),
    ('modules/styleSheetLight.css', 'modules'),

    # FFmpeg binaries
    ('modules/ffmpeg', 'modules/ffmpeg'),

    # Model cache directories (pre-downloaded models)
    ('modules/models', 'modules/models'),
]

# Include CUDA binaries if present
cuda_dir = os.path.join('modules', 'CUDA')
if os.path.isdir(cuda_dir):
    datas.append((cuda_dir, 'modules/CUDA'))

# Include faster-whisper VAD assets
try:
    import faster_whisper
    fw_path = os.path.dirname(faster_whisper.__file__)
    assets_path = os.path.join(fw_path, 'assets')
    if os.path.exists(assets_path):
        datas.append((assets_path, 'faster_whisper/assets'))
        print(f"Including faster_whisper assets from: {assets_path}")
except Exception as e:
    print(f"Warning: Could not include faster_whisper assets: {e}")

# Include config files if they exist
for cfg in ('mlaas_config.json', 'updater_config.json'):
    cfg_path = os.path.join('modules', cfg)
    if os.path.exists(cfg_path):
        datas.append((cfg_path, 'modules'))

# ── Analysis ────────────────────────────────────────────────────
a = Analysis(
    ['AutoUI.py'],
    pathex=[current_dir],
    binaries=[],
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
    upx=True,
    console=False,          # Windowed app (no console)
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
    upx=True,
    upx_exclude=[],
    name='DogeAutoSub',
)