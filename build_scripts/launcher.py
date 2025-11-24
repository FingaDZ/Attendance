"""
FaceAttendanceAI Launcher
Main entry point for the Windows executable
"""
import sys
import os
import threading
import time
import webbrowser
import socket
from pathlib import Path
import tempfile
import shutil

# Add the bundled app to the path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BUNDLE_DIR = sys._MEIPASS
    APP_DIR = Path(BUNDLE_DIR) / 'app'
    sys.path.insert(0, str(APP_DIR.parent))
else:
    # Running in development
    BUNDLE_DIR = Path(__file__).parent.parent
    APP_DIR = BUNDLE_DIR / 'backend' / 'app'

# Set up data directory in user's AppData
APPDATA_DIR = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / 'FaceAttendanceAI'
APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# Database path
DB_PATH = APPDATA_DIR / 'attendance.db'
os.environ['DATABASE_URL'] = f'sqlite:///{DB_PATH}'

# Models directory
MODELS_DIR = APPDATA_DIR / 'models'
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Photos directory
PHOTOS_DIR = APPDATA_DIR / 'photos'
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

# Copy models if bundled
if getattr(sys, 'frozen', False):
    bundled_models = Path(BUNDLE_DIR) / 'models'
    if bundled_models.exists() and not any(MODELS_DIR.iterdir()):
        print("Copying AI models to user directory...")
        shutil.copytree(bundled_models, MODELS_DIR, dirs_exist_ok=True)

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def wait_for_server(host='localhost', port=8000, timeout=30):
    """Wait for the server to be ready"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex((host, port)) == 0:
                    return True
        except:
            pass
        time.sleep(0.5)
    return False

def start_backend():
    """Start the FastAPI backend server"""
    print("Starting Face Attendance AI backend...")
    
    # Import here to avoid issues with frozen app
    import uvicorn
    from app.main import app as fastapi_app
    from fastapi.staticfiles import StaticFiles
    
    # Mount the frontend static files
    if getattr(sys, 'frozen', False):
        frontend_dist = Path(BUNDLE_DIR) / 'frontend' / 'dist'
    else:
        frontend_dist = BUNDLE_DIR / 'frontend' / 'dist'
    
    if frontend_dist.exists():
        # Serve static files at root
        fastapi_app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    
    # Run the server
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=False
    )
    server = uvicorn.Server(config)
    server.run()

def main():
    """Main entry point"""
    print("=" * 60)
    print("  Face Attendance AI - Windows Edition")
    print("=" * 60)
    print()
    
    # Check if port is already in use
    if is_port_in_use(8000):
        print("⚠️  Port 8000 is already in use!")
        print("   Another instance may be running.")
        print("   Please close it and try again.")
        input("\nPress Enter to exit...")
        return
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    print("⏳ Starting server...")
    
    # Wait for server to be ready
    if wait_for_server():
        print("✅ Server is ready!")
        print()
        print("🌐 Opening browser...")
        print("   URL: http://localhost:8000")
        print()
        
        # Open browser
        time.sleep(1)
        webbrowser.open('http://localhost:8000')
        
        print("=" * 60)
        print("  Application is running!")
        print("  - Frontend: http://localhost:8000")
        print("  - API Docs: http://localhost:8000/docs")
        print("  - Data stored in: " + str(APPDATA_DIR))
        print("=" * 60)
        print()
        print("Press Ctrl+C to stop the server...")
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            print("   Goodbye!")
    else:
        print("❌ Failed to start server!")
        print("   Please check the logs above for errors.")
        input("\nPress Enter to exit...")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
