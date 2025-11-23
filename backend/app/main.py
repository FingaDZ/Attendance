from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import api
from .database import engine, Base, SessionLocal
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

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")

# Initialize scheduler
scheduler = BackgroundScheduler()

@app.on_event("startup")
def startup_event():
    # Load embeddings
    db = SessionLocal()
    employees = db.query(Employee).all()
    face_service.load_embeddings(employees)
    
    # Initialize cameras
    # Check if we have any cameras, if not add the default RTSP one provided by user
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
    # Runs daily at 2:00 AM
    scheduler.add_job(cleanup_old_logs, 'cron', hour=2, minute=0)
    scheduler.start()
    logger.info("Log cleanup scheduler started (runs daily at 02:00)")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler shut down")

@app.get("/")
def read_root():
    return {"message": "Attendance System API is running"}
