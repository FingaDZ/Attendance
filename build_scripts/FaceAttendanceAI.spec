# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Project paths
project_root = r'F:\Code\attendance'
backend_dir = r'F:\Code\attendance\backend'
frontend_dist = r'F:\Code\attendance\frontend\dist'

# Collect all backend files
backend_files = []
backend_files.append((backend_dir + r'\app', 'app'))

# Collect frontend dist files
frontend_files = []
if os.path.exists(frontend_dist):
    frontend_files.append((frontend_dist, 'frontend/dist'))

# Collect InsightFace models (if they exist in user's home)
import os
from pathlib import Path
models_dir = Path.home() / '.insightface' / 'models'
model_files = []
if models_dir.exists():
    model_files.append((str(models_dir), 'models'))

a = Analysis(
    [r'F:\Code\attendance\build_scripts\launcher.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=backend_files + frontend_files + model_files,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'insightface',
        'insightface.app',
        'insightface.model_zoo',
        'onnxruntime',
        'onnxruntime.capi',
        'onnxruntime.capi.onnxruntime_pybind11_state',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.sql.default_comparator',
        'apscheduler.schedulers.background',
        'apscheduler.triggers.cron',
        'fastapi.staticfiles',
        'starlette.staticfiles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    name='FaceAttendanceAI',
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
