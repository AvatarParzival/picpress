# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

block_cipher = None

try:
    import tkinterdnd2
    dnd_root = Path(tkinterdnd2.__file__).parent
    dnd_datas = [(str(dnd_root), 'tkinterdnd2')]
except ImportError:
    dnd_datas = []

a = Analysis(
    ['picpress.py'],
    pathex=[str(Path('picpress.py').parent.resolve())],
    binaries=[],
    datas=dnd_datas + [
        ('icon.ico',    '.'),
        ('assets',      'assets'),
    ],
    hiddenimports=[
        'tkinterdnd2',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL._tkinter_finder',
        'PIL._imagingtk',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'ctypes',
        'ctypes.wintypes',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas', 'jupyter'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='picpress',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon='icon.ico',
)
