# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

hiddenimports = [
    'altgraph',
    'beautifulsoup4',
    'certifi',
    'charset-normalizer',
    'colorama',
    'deep-translator',
    'filelock',
    'fsspec',
    'idna',
    'Jinja2',
    'llvmlite',
    'MarkupSafe',
    'more-itertools',
    'mpmath',
    'networkx',
    'numba',
    'numpy',
    'openai-whisper',
    'packaging',
    'pefile',
    'pyinstaller',
    'pyinstaller-hooks-contrib',
    'PySide6',
    'PySide6_Addons',
    'PySide6_Essentials',
    'pywin32-ctypes',
    'regex',
    'requests',
    'shiboken6',
    'soupsieve',
    'sympy',
    'tiktoken',
    'torch',
    'tqdm',
    'typing_extensions',
    'urllib3',
    'whisper',
]

a = Analysis(
    ['AutoUI.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('icons/*', 'icons'),
        ('modules/styleSheetDark.css', 'modules'),
        ('modules/styleSheetLight.css', 'modules'),
        ('modules/*', 'modules'),
        ('ui_DogeAutoSub.py', '.'),
        ('modules/models/*', 'modules/models'),
        ('modules/ffmpeg/bin/*', 'modules/ffmpeg/bin'),
        ('.venv/Lib/site-packages/whisper/assets*', 'whisper/assets'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DogeAutoSubApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon='icons/doge.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DogeAutoSubApp',
)

app = BUNDLE(
    coll,
    name='DogeAutoSubApp',
    icon='icons/doge.ico',
    onefile=True
)