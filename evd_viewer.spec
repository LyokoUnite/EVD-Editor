# -*- mode: python; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['evd_viewer.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt5','PyQt5.QtWidgets','PyQt5.QtCore','PyQt5.QtGui'
    ],
    hookspath=[],runtime_hooks=[],excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure,a.zipped_data,cipher=block_cipher)
exe = EXE(
    pyz,a.scripts,[],
    exclude_binaries=True,
    name='evd_viewer',
    debug=False,strip=False,upx=True,
    console=False,icon=None,
)
coll = COLLECT(
    exe,a.binaries,a.zipfiles,a.datas,
    strip=False,upx=True,name='evd_viewer',
)
