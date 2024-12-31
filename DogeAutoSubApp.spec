# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['AutoUI.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('icons/*', 'icons'),
        ('modules/ffmpeg/bin/ffmpeg.exe', 'ffmpeg/bin'),
        ('modules/styleSheetDark.css', 'modules'),
        ('modules/styleSheetLight.css', 'modules'),
        ('modules/*', 'modules'),
        ('ui_DogeAutoSub.py', '.'),
        ('modules/constants.py', 'modules'),
        ('modules/AutoSub.py', 'modules'),
        ('models/*', 'models'),
    ],
    hiddenimports=[
        'deep_translator',
        'whisper',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
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
    console=False,
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