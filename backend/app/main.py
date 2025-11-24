from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import api
from .database import engine, Base, SessionLocal, migrate_database_schema
from .models import Camera
from .services.face_service import face_service
from .services.camera_service import camera_service
from .models import Employee
from .cron_cleanup import cleanup_old_logs
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Smart Auth (LAN bypass, WAN auth)
from .middleware.smart_auth import SmartAuthMiddleware
app.add_middleware(SmartAuthMiddleware)

app.include_router(api.router, prefix="/api")

# Initialize scheduler
scheduler = BackgroundScheduler()

@app.on_event("startup")
async def startup_event():
    # Run database migration first (v1.6.5: auto-add missing columns)
    migrate_database_schema()
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Load embeddings
    db = SessionLocal()
    employees = db.query(Employee).all()
    face_service.load_embeddings(employees)
    
    # Initialize cameras
    # Check if we have any cameras, if not add the default webcam
    cam_count = db.query(Camera).count()
    if cam_count == 0:
        default_cam = Camera(
            name="Webcam", 
            source="0"
        )
        db.add(default_cam)
        db.commit()
        logger.info("Added default webcam.")
    
    camera_service.initialize_cameras_from_db()
    db.close()
    
    # Start automatic log cleanup scheduler
    # Runs daily at 11:00 AM
    scheduler.add_job(cleanup_old_logs, 'cron', hour=11, minute=0)
    scheduler.start()
    logger.info("Log cleanup scheduler started (runs daily at 11:00)")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler shut down")

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Mount frontend static files
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    # Catch-all for SPA
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # Check if file exists in dist
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # Otherwise return index.html
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    logger.warning(f"Frontend dist directory not found at {frontend_dist}")

@app.get("/")
def read_root():
    if os.path.exists(os.path.join(frontend_dist, "index.html")):
        return FileResponse(os.path.join(frontend_dist, "index.html"))
    return {"message": "Attendance System API is running (Frontend not found)"}
