# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('trilhas.csv', '.'), ('ponto_interesse.csv', '.'), ('vinculos-aprovados.csv', '.'), ('observacao-piloto.csv', '.'), ('inventario-estacoes-pluviometricas-rj.csv', '.'), ('conhecimento', 'conhecimento'), ('gpx', 'gpx'), ('src/assets', 'src/assets')]
datas += collect_data_files('tzdata')


a = Analysis(
    ['src/abrir_trilhas.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TrilhasRJ',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
