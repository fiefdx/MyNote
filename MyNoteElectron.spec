# -*- mode: python ; coding: utf-8 -*-
# PyInstaller bundle for the MyNote backend used by the Electron desktop app.
# Creates a self-contained "onedir" bundle (dist/MyNote) that carries its own
# CPython interpreter plus all dependencies. No wxPython (MyNoteGUI is not
# bundled; the Electron shell is the GUI).

import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = [('app/static', 'static'),
         ('app/templates', 'templates'),
         ('app/translations', 'translations'),
         ('app/configuration.yml.readme', '.'),
         ]
datas += collect_data_files('jieba')
datas += collect_data_files('whoosh')

hiddenimports = []
hiddenimports += collect_submodules('whoosh')
hiddenimports += collect_submodules('jieba')
hiddenimports += ['tea_compat', 'toro']

block_cipher = None

a = Analysis(['app/MyNote.py'],
             pathex=['.'],
             binaries=[],
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=['wx', 'wxPython', 'PyQt5', 'PySide2', 'matplotlib', 'tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='MyNote',
          debug=False,
          strip=False,
          upx=False,
          console=True)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='MyNote')
