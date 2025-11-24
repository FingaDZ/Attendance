"""
Build Configuration Helper
Prepares the PyInstaller spec file with correct paths
"""
import os
from pathlib import Path

# Get the project root
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / 'backend'
FRONTEND_DIST = PROJECT_ROOT / 'frontend' / 'dist'
BUILD_SCRIPTS = PROJECT_ROOT / 'build_scripts'

def generate_spec_file():
    """Generate the PyInstaller spec file with correct paths"""
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Project paths
project_root = r'{PROJECT_ROOT}'
backend_dir = r'{BACKEND_DIR}'
frontend_dist = r'{FRONTEND_DIST}'

# Collect all backend files
backend_files = []
backend_files.append((backend_dir + r'\\app', 'app'))

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
    [r'{BUILD_SCRIPTS}\\launcher.py'],
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
    hooksconfig={{}},
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
"""
    
    # Write the spec file
    spec_file = BUILD_SCRIPTS / 'FaceAttendanceAI.spec'
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    print(f"✅ Generated spec file: {spec_file}")
    print(f"   Backend: {BACKEND_DIR}")
    print(f"   Frontend: {FRONTEND_DIST}")
    
    # Check if frontend is built
    if not FRONTEND_DIST.exists():
        print(f"\n⚠️  WARNING: Frontend dist folder not found!")
        print(f"   Please run: cd frontend && npm run build")
        return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("  Build Configuration Helper")
    print("=" * 60)
    print()
    
    if generate_spec_file():
        print("\n✅ Configuration complete!")
        print("   You can now run: build_scripts\\build_executable.bat")
    else:
        print("\n❌ Configuration incomplete!")
        print("   Please build the frontend first.")
