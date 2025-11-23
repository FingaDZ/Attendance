from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Employee, AttendanceLog, Camera
from ..services.face_service import face_service
from ..services.camera_service import camera_service
import cv2
import numpy as np
from fastapi.responses import StreamingResponse
import io
import threading
import time
import datetime

router = APIRouter()

# Global lock for attendance logging to prevent race conditions
attendance_lock = threading.Lock()
# Dictionary to store last processed time for each employee to prevent duplicate logs
last_processed = {}

@router.post("/employees/")
async def create_employee(
    name: str = Form(...),
    department: str = Form(None),
    pin: str = Form(None),
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    file3: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Create employee with 3 photos for better recognition accuracy"""
    photos = []
    embeddings = []
    
    # Process all 3 photos (photo2 will be grayscale)
    for i, file in enumerate([file1, file2, file3], 1):
        content = await file.read()
        
        # Check quality first
        is_good, msg = face_service.check_face_quality(content)
        if not is_good:
            raise HTTPException(status_code=400, detail=f"Photo {i} quality check failed: {msg}")

        # Mark photo2 (index 1) as grayscale
        is_grayscale = (i == 2)
        
        # Use new preprocessing pipeline
        processed_content, embedding_pickle = face_service.register_face(content, is_grayscale=is_grayscale)
        
        if processed_content is None or embedding_pickle is None:
            raise HTTPException(status_code=400, detail=f"No face detected in photo {i}")
        
        photos.append(processed_content)
        embeddings.append(embedding_pickle)

    new_emp = Employee(
        name=name, 
        department=department, 
        embedding1=embeddings[0],
        embedding2=embeddings[1],
        embedding3=embeddings[2],
        pin=pin, 
        photo1=photos[0],
        photo2=photos[1],
        photo3=photos[2]
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    
    # Reload embeddings in service
    all_emps = db.query(Employee).all()
    face_service.load_embeddings(all_emps)
    
    return {"id": new_emp.id, "name": new_emp.name}

@router.put("/employees/{emp_id}")
async def update_employee(
    emp_id: int,
    name: str = Form(...),
    department: str = Form(None),
    pin: str = Form(None),
    file1: UploadFile = File(None),
    file2: UploadFile = File(None),
    file3: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Update employee - can update individual photos or all 3"""
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    emp.name = name
    emp.department = department
    emp.pin = pin
    
    # Update photos if provided
    files = [file1, file2, file3]
    for i, file in enumerate(files, 1):
        if file:
            content = await file.read()
            is_good, msg = face_service.check_face_quality(content)
            if not is_good:
                raise HTTPException(status_code=400, detail=f"Photo {i} quality check failed: {msg}")
            
            # Mark photo2 as grayscale
            is_grayscale = (i == 2)
            
            # Use new preprocessing pipeline
            processed_content, embedding_pickle = face_service.register_face(content, is_grayscale=is_grayscale)
            if processed_content is None or embedding_pickle is None:
                raise HTTPException(status_code=400, detail=f"No face detected in photo {i}")
                
            # Update specific photo and embedding
            setattr(emp, f'embedding{i}', embedding_pickle)
            setattr(emp, f'photo{i}', processed_content)
    
    # Reload embeddings if any photo was updated
    if any(files):
        all_emps = db.query(Employee).all()
        face_service.load_embeddings(all_emps)
    
    db.commit()
    return {"status": "updated"}

@router.get("/employees/{emp_id}/photo")
def get_employee_photo(emp_id: int, photo_num: int = 1, db: Session = Depends(get_db)):
    """Get employee photo - photo_num can be 1, 2, or 3"""
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    photo = getattr(emp, f'photo{photo_num}', None)
    if not photo:
        raise HTTPException(status_code=404, detail=f"Photo {photo_num} not found")
    
    return StreamingResponse(io.BytesIO(photo), media_type="image/jpeg")

@router.post("/verify-pin/")
def verify_pin(employee_id: int = Form(...), pin: str = Form(...), db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if emp.pin and emp.pin == pin:
        # Log attendance with Entry/Exit logic
        log_type = check_attendance_status(emp.id, db)
        if not log_type:
            return {"status": "already_logged", "name": emp.name, "message": "Already logged Entry and Exit for today."}

        log = AttendanceLog(employee_id=emp.id, employee_name=emp.name, camera_id="PIN", confidence=1.0, type=log_type)
        db.add(log)
        db.commit()
        return {"status": "verified", "name": emp.name, "type": log_type}
    else:
        raise HTTPException(status_code=401, detail="Invalid PIN")

@router.get("/employees/")
def read_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    employees = db.query(Employee).offset(skip).limit(limit).all()
    return [{"id": e.id, "name": e.name, "department": e.department} for e in employees]

@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(emp)
    db.commit()
    
    # Reload embeddings
    all_emps = db.query(Employee).all()
    face_service.load_embeddings(all_emps)
    return {"status": "deleted"}

@router.post("/recognize/")
async def recognize_face(file: UploadFile = File(...)):
    """Recognize face from uploaded image"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        # Recognize faces
        results = face_service.recognize_faces(img)
        
        if not results:
            return {"name": "Unknown", "confidence": 0.0, "employee_id": None}
        
        # Get the first (best) result
        name, bbox, conf, emp_id, kps = results[0]
        
        # Get server timestamp
        server_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        return {
            "name": name,
            "confidence": float(conf),
            "employee_id": emp_id,
            "timestamp": server_time
        }
    except Exception as e:
        print(f"Recognition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Cameras ---

@router.post("/cameras/")
def create_camera(name: str, source: str, db: Session = Depends(get_db)):
    new_cam = Camera(name=name, source=source)
    db.add(new_cam)
    db.commit()
    db.refresh(new_cam)
    
    # Start the camera
    camera_service.start_camera(new_cam.id, new_cam.source)
    
    return new_cam

@router.get("/cameras/")
def read_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()

@router.delete("/cameras/{cam_id}")
def delete_camera(cam_id: int, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.id == cam_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    camera_service.stop_camera(cam.id)
    db.delete(cam)
    db.commit()
    return {"status": "deleted"}

@router.put("/cameras/{cam_id}/toggle")
def toggle_camera(cam_id: int, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.id == cam_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    cam.is_active = 1 if cam.is_active == 0 else 0
    db.commit()
    
    if cam.is_active:
        camera_service.start_camera(cam.id, cam.source)
    else:
        camera_service.stop_camera(cam.id)
        
    return {"status": "toggled", "is_active": cam.is_active}

@router.put("/cameras/{cam_id}/select")
def select_camera(cam_id: int, db: Session = Depends(get_db)):
    # Deselect all
    db.query(Camera).update({Camera.is_selected: 0})
    
    # Select target
    cam = db.query(Camera).filter(Camera.id == cam_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    cam.is_selected = 1
    db.commit()
    return {"status": "selected", "camera": cam.name}

# --- Streaming & Recognition ---

def generate_frames(camera_id: int, db_session_factory):
    frame_count = 0
    skip_frames = 2 # Process 1 out of 3 frames for detection
    last_results = []
    
    # Create a local session for logging
    db = db_session_factory()
    
    while True:
        frame = camera_service.get_frame(camera_id)
        if frame is None:
            time.sleep(0.01)
            continue
        
        # Perform recognition every N frames
        if frame_count % skip_frames == 0:
            results = face_service.recognize_faces(frame)
            last_results = results
        
        frame_count += 1
        
        # Draw bounding boxes and names
        display_frame = frame.copy()
        for name, bbox, conf, emp_id, kps in last_results:
            x1, y1, x2, y2 = map(int, bbox)
            color = (0, 255, 0) if conf > 0.87 else (0, 0, 255)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(display_frame, f"{name} ({conf:.2f})", (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', display_frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@router.get("/stream/{camera_id}")
def video_feed(camera_id: int, db: Session = Depends(get_db)):
    from ..database import SessionLocal
    return StreamingResponse(generate_frames(camera_id, SessionLocal), 
                           media_type="multipart/x-mixed-replace; boundary=frame")

# --- Attendance Logging ---

def check_attendance_status(employee_id: int, db: Session):
    """Determine if next log should be ENTRY or EXIT"""
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    logs = db.query(AttendanceLog).filter(
        AttendanceLog.employee_id == employee_id,
        AttendanceLog.timestamp >= today_start
    ).order_by(AttendanceLog.timestamp.asc()).all()
    
    # Strict Logic: 1 Entry / 1 Exit per day
    has_entry = any(log.type == 'ENTRY' for log in logs)
    has_exit = any(log.type == 'EXIT' for log in logs)
    
    if has_exit:
        print(f"Blocked: Already has EXIT for today.")
        return None # Day complete
        
    if not has_entry:
        return 'ENTRY'
        
    # If has_entry and not has_exit:
    # Check cooldown (4 hours = 14400 seconds)
    last_log = logs[-1]
    time_diff = (datetime.datetime.now() - last_log.timestamp.replace(tzinfo=None)).total_seconds()
    if time_diff < 14400:
        print(f"Blocked: Cooldown active. {14400 - time_diff}s remaining.")
        return None

    return 'EXIT'

@router.post("/log_attendance/")
def log_attendance(employee_id: int, camera_id: str, confidence: float, db: Session = Depends(get_db)):
    with attendance_lock:
        # Backend Debounce: Check if we processed this employee recently (last 5 seconds)
        now = time.time()
        if employee_id in last_processed:
            if now - last_processed[employee_id] < 5:
                print(f"Blocked: Debounce active for Emp {employee_id}")
                return {"status": "debounced"}
        
        last_processed[employee_id] = now

        log_type = check_attendance_status(employee_id, db)
        print(f"Log Request: Emp {employee_id}, Conf {confidence}. Status: {log_type}")
        if not log_type:
            return {"status": "already_logged_or_blocked"}
    
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Calculate worked minutes if EXIT
    worked_minutes = None
    if log_type == 'EXIT':
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        entry_log = db.query(AttendanceLog).filter(
            AttendanceLog.employee_id == employee_id,
            AttendanceLog.type == 'ENTRY',
            AttendanceLog.timestamp >= today_start
        ).order_by(AttendanceLog.timestamp.desc()).first()
        
        if entry_log:
            # Calculate minutes
            diff = datetime.datetime.now() - entry_log.timestamp
            worked_minutes = int(diff.total_seconds() / 60)

    log = AttendanceLog(
        employee_id=employee_id, 
        employee_name=emp.name, 
        camera_id=camera_id, 
        confidence=confidence, 
        type=log_type, 
        worked_minutes=worked_minutes
    )
    db.add(log)
    db.commit()
    return {"status": "logged", "type": log_type, "worked_minutes": worked_minutes}

@router.get("/attendance/")
def read_attendance(
    skip: int = 0, 
    limit: int = 100, 
    employee_id: int = None, 
    start_date: str = None, 
    end_date: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(AttendanceLog)
    
    if employee_id:
        query = query.filter(AttendanceLog.employee_id == employee_id)
    
    if start_date:
        start = datetime.datetime.fromisoformat(start_date)
        query = query.filter(AttendanceLog.timestamp >= start)
    
    if end_date:
        # Include the entire end_date day (until 23:59:59)
        end = datetime.datetime.fromisoformat(end_date)
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        query = query.filter(AttendanceLog.timestamp <= end)
    
    logs = query.order_by(AttendanceLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [{
        "id": log.id,
        "employee_id": log.employee_id,
        "employee_name": log.employee_name,
        "camera_id": log.camera_id,
        "confidence": log.confidence,
        "type": log.type,
        "worked_minutes": log.worked_minutes,
        "timestamp": log.timestamp.isoformat()
    } for log in logs]

@router.delete("/attendance/{log_id}")
def delete_attendance_log(log_id: int, db: Session = Depends(get_db)):
    log = db.query(AttendanceLog).filter(AttendanceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    db.delete(log)
    db.commit()
    return {"status": "deleted"}

@router.delete("/attendance/")
def delete_all_attendance_logs(db: Session = Depends(get_db)):
    db.query(AttendanceLog).delete()
    db.commit()
    return {"status": "all_deleted"}

@router.get("/work_time/")
def get_work_time(employee_id: int = None, date: str = None, db: Session = Depends(get_db)):
    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    start = datetime.datetime.fromisoformat(f"{date}T00:00:00")
    end = datetime.datetime.fromisoformat(f"{date}T23:59:59")
    
    query = db.query(AttendanceLog).filter(
        AttendanceLog.timestamp >= start,
        AttendanceLog.timestamp <= end
    )
    
    if employee_id:
        query = query.filter(AttendanceLog.employee_id == employee_id)
    
    entry_log = query.filter(AttendanceLog.type == 'ENTRY').first()
    exit_log = query.filter(AttendanceLog.type == 'EXIT').first()
    
    if not entry_log or not exit_log:
        return {"work_minutes": 0, "status": "incomplete"}

    time_diff = (exit_log.timestamp.replace(tzinfo=None) - entry_log.timestamp.replace(tzinfo=None)).total_seconds()
    work_minutes = int(time_diff / 60)
    
    return {
        "work_minutes": work_minutes,
        "status": "complete" if work_minutes >= 300 else "insufficient", # 5 hours = 300 minutes
        "minimum_required": 300,
        "entry_time": entry_log.timestamp.isoformat(),
        "exit_time": exit_log.timestamp.isoformat()
    }
