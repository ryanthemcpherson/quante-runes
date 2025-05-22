# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_debug.py'],
    pathex=[],
    binaries=[],
    datas=[('urgot_icon.png', '.'), ('client_secrets.json', '.'), ('token.json', '.'), ('credentials.json', '.'), ('src', 'src'), ('src\\data\\img_url_hack.html', 'src/data')],
    hiddenimports=['qasync', 'gspread', 'google.auth', 'google_auth_oauthlib.flow', 'google.oauth2.credentials', 'google_auth_oauthlib.flow', 'google.auth.transport.requests'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('v', None, 'OPTION')],
    name='UrgotMatchupHelper',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['urgot_icon.png'],
)
