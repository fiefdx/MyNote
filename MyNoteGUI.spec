# -*- mode: python -*-

import os
import jieba

jieba_path = os.path.dirname(jieba.__file__)

block_cipher = None


a = Analysis(['app/MyNoteGUI.py'],
             pathex=['/home/breeze/Develop/MyNote'],
             binaries=[],
             datas=[('README', '.'),
                    ('app/keys', 'keys'),
                    ('app/static', 'static'),
                    ('app/templates', 'templates'),
                    ('app/translations', 'translations'),
                    ('app/configuration.yml', '.'),
                    ('app/configuration.yml.readme', '.'),
                    (os.path.join(jieba_path, 'dict.txt'), 'jieba'),
                    (os.path.join(jieba_path, 'analyse', 'idf.txt'), os.path.join('jieba', 'analyse')),
                    ('app/Install.sh', '.'),
                    ('app/MakeShortcut.sh', '.'),
                    ('app/Uninstall.sh', '.'),],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='MyNoteGUI',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='MyNoteGUI')
