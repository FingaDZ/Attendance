from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db, SessionLocal
from ..models import Employee, AttendanceLog, Camera, SystemSettings
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

# --- System Settings ---
@router.get("/settings/")
def get_settings(db: Session = Depends(get_db)):
    return db.query(SystemSettings).all()

@router.get("/settings/{key}")
def get_setting(key: str, db: Session = Depends(get_db)):
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if not setting:
        # Return default for wan_domain if not set
        if key == "wan_domain":
            return {"key": "wan_domain", "value": "https://hgq09k0j9p1.sn.mynetname.net"}
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.post("/settings/")
def update_setting(key: str = Form(...), value: str = Form(...), description: str = Form(None), db: Session = Depends(get_db)):
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if setting:
        setting.value = value
        if description:
            setting.description = description
    else:
        setting = SystemSettings(key=key, value=value, description=description)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting

@router.delete("/settings/{key}")
def delete_setting(key: str, db: Session = Depends(get_db)):
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    db.delete(setting)
    db.commit()
    return {"status": "deleted"}


# Global lock for attendance logging to prevent race conditions
attendance_lock = threading.Lock()
# Dictionary to store last processed time for each employee to prevent duplicate logs
last_processed = {}
# Dictionary to store last block reason to persist error message during debounce
last_block_info = {}

@router.post("/employees/")
async def create_employee(
    name: str = Form(...),
    department: str = Form(None),
    pin: str = Form(None),
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    file3: UploadFile = File(...),
    file4: UploadFile = File(...),  # v1.6.5
    file5: UploadFile = File(...),  # v1.6.5
    file6: UploadFile = File(...),  # v1.6.5
    db: Session = Depends(get_db)
):
    """Create employee with 6 photos for better recognition accuracy (v1.6.5: increased from 3)"""
    photos = []
    embeddings = []
    
    # Process all 6 photos (photo2 will be grayscale)
    for i, file in enumerate([file1, file2, file3, file4, file5, file6], 1):
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
        embedding4=embeddings[3],  # v1.6.5
        embedding5=embeddings[4],  # v1.6.5
        embedding6=embeddings[5],  # v1.6.5
        pin=pin, 
        photo1=photos[0],
        photo2=photos[1],
        photo3=photos[2],
        photo4=photos[3],  # v1.6.5
        photo5=photos[4],  # v1.6.5
        photo6=photos[5]   # v1.6.5
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
    file4: UploadFile = File(None),  # v1.6.5
    file5: UploadFile = File(None),  # v1.6.5
    file6: UploadFile = File(None),  # v1.6.5
    db: Session = Depends(get_db)
):
    """Update employee - can update individual photos or all 6 (v1.6.5: increased from 3)"""
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    emp.name = name
    emp.department = department
    emp.pin = pin
    
    # Update photos if provided
    files = [file1, file2, file3, file4, file5, file6]
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
async def verify_pin(
    employee_id: int = Form(...), 
    pin: str = Form(...),
    photo: UploadFile = File(None),  # v2.11.0: Optional photo capture
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if emp.pin and emp.pin == pin:
        # Log attendance with Entry/Exit logic
        log_type, error_msg = check_attendance_status(emp.id, db)
        if not log_type:
            return {"status": "blocked", "name": emp.name, "message": error_msg}

        # v2.11.0: Capture photo if provided
        photo_data = None
        if photo:
            print(f"DEBUG: Received photo for PIN auth. Filename: {photo.filename}")
            photo_data = await photo.read()
        else:
            print("DEBUG: No photo received for PIN auth")

        log = AttendanceLog(
            employee_id=emp.id, 
            employee_name=emp.name, 
            camera_id="PIN", 
            confidence=1.0, 
            type=log_type,
            photo_capture=photo_data  # v2.11.0
        )
        db.add(log)
        db.commit()
        return {"status": "verified", "name": emp.name, "type": log_type}
    else:
        raise HTTPException(status_code=401, detail="Invalid PIN")

@router.get("/logs/{log_id}/photo")
def get_log_photo(log_id: int, db: Session = Depends(get_db)):
    """v2.11.0: Retrieve photo captured during attendance log"""
    log = db.query(AttendanceLog).filter(AttendanceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    if not log.photo_capture:
        raise HTTPException(status_code=404, detail="No photo available for this log")
    
    return StreamingResponse(io.BytesIO(log.photo_capture), media_type="image/jpeg")


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
async def recognize_face(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Recognize face from uploaded image with enhanced landmarks and liveness"""
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image")
        
        # Recognize faces with liveness detection
        # Recognize faces (liveness is now built-in)
        results = face_service.recognize_faces(img, db=db)
        
        if not results:
            return {"name": "Unknown", "confidence": 0.0, "employee_id": None, "liveness_score": 0.0}
        
        # Get the first (best) result
        result = results[0]
        
        # Get server timestamp
        server_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        return {
            "name": result["name"],
            "confidence": float(result["confidence"]),
            "liveness_score": float(result["liveness"]),
            "employee_id": result["employee_id"],
            "timestamp": server_time,
            "landmarks_count": len(result["keypoints"]) if result["keypoints"] is not None else 0,
            "landmarks": result["keypoints"] if result["keypoints"] is not None else []
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

# --- Async Detection Helper ---
class AsyncFrameProcessor:
    def __init__(self, camera_id):
        self.camera_id = camera_id
        self.latest_frame = None
        self.latest_results = []
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()

    def update_frame(self, frame):
        with self.lock:
            self.latest_frame = frame.copy()

    def get_results(self):
        with self.lock:
            return self.latest_results

    def stop(self):
        self.running = False
        self.thread.join(timeout=1.0)

    def _detection_loop(self):
        # Create a dedicated DB session for this thread
        db = SessionLocal()
        try:
            while self.running:
                frame_to_process = None
                with self.lock:
                    if self.latest_frame is not None:
                        frame_to_process = self.latest_frame.copy()
                
                if frame_to_process is not None:
                    # Run detection (heavy operation)
                    results = face_service.recognize_faces(frame_to_process, db=db)
                    with self.lock:
                        self.latest_results = results
                    
                    # ✅ AUTO-LOGGING: Enregistrement automatique des logs d'attendance
                    if results:
                        for result in results:
                            # Vérifier si c'est une reconnaissance valide
                            if (result["employee_id"] is not None and 
                                result["confidence"] > 0.85 and 
                                result["liveness"] > 0.4):
                                
                                employee_id = result["employee_id"]
                                confidence = result["confidence"]
                                
                                # Debounce : éviter les doublons (5 secondes)
                                with attendance_lock:
                                    now = time.time()
                                    if employee_id in last_processed:
                                        if now - last_processed[employee_id] < 5:
                                            # 🔴 FIX v2.0.6: Si on est dans le debounce, on vérifie s'il y avait un blocage
                                            # pour ré-afficher le message d'erreur (sinon ça clignote vert)
                                            if employee_id in last_block_info:
                                                block_data = last_block_info[employee_id]
                                                # Vérifier si l'info de blocage est encore pertinente (< 5s)
                                                if now - block_data["time"] < 5:
                                                    with self.lock:
                                                        for res in self.latest_results:
                                                            if res.get("employee_id") == employee_id:
                                                                res["block_reason"] = block_data["reason"]
                                                                res["block_subtext"] = block_data["subtext"]
                                                                break
                                            continue  # Skip, trop récent
                                    
                                    last_processed[employee_id] = now
                                    
                                    # Vérifier le statut (ENTRY ou EXIT)
                                    log_type, error_msg = check_attendance_status(employee_id, db)
                                    
                                    if log_type:
                                        # Enregistrer le log
                                        emp = db.query(Employee).filter(Employee.id == employee_id).first()
                                        if emp:
                                            # Calculer worked_minutes si EXIT
                                            worked_minutes = None
                                            if log_type == 'EXIT':
                                                today_start = datetime.datetime.now().replace(
                                                    hour=0, minute=0, second=0, microsecond=0
                                                )
                                                entry_log = db.query(AttendanceLog).filter(
                                                    AttendanceLog.employee_id == employee_id,
                                                    AttendanceLog.type == 'ENTRY',
                                                    AttendanceLog.timestamp >= today_start
                                                ).order_by(AttendanceLog.timestamp.desc()).first()
                                                
                                                if entry_log:
                                                    diff = datetime.datetime.now() - entry_log.timestamp
                                                    worked_minutes = int(diff.total_seconds() / 60)
                                            
                                            # Créer le log
                                            log = AttendanceLog(
                                                employee_id=employee_id,
                                                employee_name=emp.name,
                                                camera_id=str(self.camera_id),
                                                confidence=confidence,
                                                type=log_type,
                                                worked_minutes=worked_minutes
                                            )
                                            db.add(log)
                                            db.commit()
                                            
                                            print(f"✅ Auto-logged: {emp.name} - {log_type} (Conf: {confidence:.2f}, Cam: {self.camera_id})")
                                            
                                            # Succès : on nettoie les infos de blocage
                                            if employee_id in last_block_info:
                                                del last_block_info[employee_id]
                                    else:
                                        # Log bloqué - Déterminer la raison spécifique pour affichage visuel
                                        if error_msg:
                                            print(f"⚠️ Log blocked for Emp {employee_id}: {error_msg}")
                                            
                                            # Ajouter la raison du blocage dans les résultats pour affichage
                                            block_reason = None
                                            block_subtext = None
                                            
                                            # Analyser le message d'erreur pour déterminer la raison
                                            if "entrées sont autorisées uniquement entre" in error_msg:
                                                block_reason = "Heure Entrée Dépassée"
                                                block_subtext = "Entrée: 03h00-13h30"
                                            elif "sorties sont autorisées uniquement entre" in error_msg:
                                                block_reason = "Heure Sortie Dépassée"
                                                block_subtext = "Sortie: 12h00-23h59"
                                            elif "attendre" in error_msg.lower() and "minutes" in error_msg.lower():
                                                # Extraire le nombre de minutes du message
                                                import re
                                                match = re.search(r'(\d+)\s+minutes', error_msg)
                                                if match:
                                                    minutes = match.group(1)
                                                    block_reason = "Temps de Travail minimum non achevé"
                                                    block_subtext = f"Attendre {minutes} minutes"
                                                else:
                                                    block_reason = "Temps de Travail minimum non achevé"
                                                    block_subtext = "Attendre quelques minutes"
                                            elif "déjà enregistré" in error_msg.lower():
                                                block_reason = "Detection Déjà Effectué"
                                                block_subtext = "1 entrée/sortie max"
                                            
                                            # Mettre à jour le résultat avec la raison du blocage
                                            if block_reason:
                                                # Sauvegarder l'info de blocage pour le debounce
                                                last_block_info[employee_id] = {
                                                    "reason": block_reason,
                                                    "subtext": block_subtext,
                                                    "time": time.time()
                                                }
                                                
                                                with self.lock:
                                                    for res in self.latest_results:
                                                        if res.get("employee_id") == employee_id:
                                                            res["block_reason"] = block_reason
                                                            res["block_subtext"] = block_subtext
                                                            break

                
                # Sleep to limit detection FPS (2.5 FPS for CPU optimization)
                time.sleep(0.4) 
        except Exception as e:
            print(f"Detection thread error: {e}")
        finally:
            db.close()

# Global processors cache
processors = {}

@router.get("/stream/{camera_id}")
async def stream_camera(camera_id: int):
    """
    MJPEG streaming endpoint optimized for RTSP cameras.
    Provides low-latency, bandwidth-efficient streaming for web browsers.
    """
    def generate():
        # Ensure we have a processor for this camera
        if camera_id not in processors:
            print(f"Starting new AsyncFrameProcessor for camera {camera_id}")
            processors[camera_id] = AsyncFrameProcessor(camera_id)
        
        processor = processors[camera_id]
        
        try:
            while True:
                # Get raw frame (640x360 optimized for performance)
                frame = camera_service.get_frame_preview(camera_id, width=640, height=360)
                
                if frame is None:
                    time.sleep(0.05)
                    continue
                
                # Feed frame to async detector
                processor.update_frame(frame)
                
                # Get latest available results (instant)
                results = processor.get_results()
                
                # Draw results on the current frame
                try:
                    frame = face_service.draw_results(frame, results)
                except Exception as e:
                    print(f"Drawing error: {e}")
                
                # Encode to JPEG with optimizations
                encode_params = [
                    int(cv2.IMWRITE_JPEG_QUALITY), 75,  # Reduced for faster encoding
                    int(cv2.IMWRITE_JPEG_OPTIMIZE), 1,  # Optimize Huffman tables
                    int(cv2.IMWRITE_JPEG_PROGRESSIVE), 1  # Progressive JPEG
                ]
                ret, buffer = cv2.imencode('.jpg', frame, encode_params)
                
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Synchronized with camera FPS (15 FPS)
                time.sleep(0.067)
        except GeneratorExit:
            pass
        except Exception as e:
            print(f"Stream error: {e}")
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/stream/{camera_id}/clean")
async def stream_camera_clean(camera_id: int):
    """
    MJPEG stream endpoint WITHOUT detection overlays.
    Used for employee photo capture to get clean frames.
    """
    def generate():
        try:
            while True:
                # Get raw frame without any processing
                frame = camera_service.get_frame_preview(camera_id, width=800, height=600)
                
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Encode to JPEG (NO overlays drawn)
                ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(0.066)  # 15 FPS
        except GeneratorExit:
            pass
        except Exception as e:
            print(f"Clean stream error: {e}")
    
    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# --- Streaming & Recognition ---

# Ancienne fonction generate_frames supprimée pour éviter les conflits avec AsyncFrameProcessor
# L'endpoint /stream/{camera_id} est maintenant géré par stream_camera plus haut


# --- Attendance Logging ---

def check_time_constraints(log_type: str) -> tuple[bool, str]:
    """
    Vérifie si l'heure actuelle respecte les contraintes horaires.
    
    Args:
        log_type: 'ENTRY' ou 'EXIT'
    
    Returns:
        (is_valid, error_message)
    """
    now = datetime.datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    current_time_minutes = current_hour * 60 + current_minute
    
    if log_type == 'ENTRY':
        # ENTRY: 03h00 à 13h30
        start_time = 3 * 60  # 03:00 = 180 minutes
        end_time = 13 * 60 + 30  # 13:30 = 810 minutes
        
        if not (start_time <= current_time_minutes <= end_time):
            return False, "Les entrées sont autorisées uniquement entre 03h00 et 13h30"
    
    elif log_type == 'EXIT':
        # EXIT: 12h00 à 23h59 (pas après minuit)
        start_time = 12 * 60  # 12:00 = 720 minutes
        end_time = 23 * 60 + 59  # 23:59 = 1439 minutes
        
        if not (start_time <= current_time_minutes <= end_time):
            return False, "Les sorties sont autorisées uniquement entre 12h00 et 23h59"
    
    return True, ""

def check_attendance_status(employee_id: int, db: Session) -> tuple[str | None, str | None]:
    """Determine if next log should be ENTRY or EXIT
    
    v2.10.0: Allow EXIT without ENTRY during standard hours
    
    Returns:
        (log_type, error_message)
    """
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    logs = db.query(AttendanceLog).filter(
        AttendanceLog.employee_id == employee_id,
        AttendanceLog.timestamp >= today_start
    ).order_by(AttendanceLog.timestamp.asc()).all()
    
    # Nouvelle logique stricte : 1 seule entrée et 1 seule sortie par jour
    entry_logs = [log for log in logs if log.type == 'ENTRY']
    exit_logs = [log for log in logs if log.type == 'EXIT']

    # Cas 1: Déjà ENTRY + EXIT → Bloquer
    if len(entry_logs) >= 1 and len(exit_logs) >= 1:
        print(f"Blocked: Already has ENTRY and EXIT for today.")
        return None, "Vous avez déjà enregistré une entrée et une sortie aujourd'hui."

    # Cas 2: Aucune ENTRY
    if len(entry_logs) == 0:
        # Sous-cas 2a: Aucune SORTIE → Permettre ENTRY ou EXIT
        if len(exit_logs) == 0:
            # Vérifier contrainte horaire pour ENTRY
            is_valid_entry, error_msg_entry = check_time_constraints('ENTRY')
            if is_valid_entry:
                return 'ENTRY', None
            
            # v2.10.0: Si hors heures ENTRY, permettre EXIT si dans heures EXIT
            is_valid_exit, error_msg_exit = check_time_constraints('EXIT')
            if is_valid_exit:
                print(f"Flexible Exit: Allowing EXIT without ENTRY (within EXIT hours)")
                return 'EXIT', None
            
            # Hors de toutes les heures standard
            return None, "Hors des heures standard d'entrée et de sortie."
        
        # Sous-cas 2b: Déjà SORTIE sans ENTRÉE → Bloquer
        else:
            print(f"Blocked: EXIT already logged without ENTRY.")
            return None, "Sortie déjà enregistrée aujourd'hui."

    # Cas 3: ENTRY existe, pas de SORTIE
    if len(entry_logs) == 1 and len(exit_logs) == 0:
        # Check cooldown (4 hours = 14400 seconds)
        last_log = logs[-1]
        time_diff = (datetime.datetime.now() - last_log.timestamp.replace(tzinfo=None)).total_seconds()
        if time_diff < 14400:
            remaining_minutes = int((14400 - time_diff) / 60)
            print(f"Blocked: Cooldown active. {remaining_minutes} minutes remaining.")
            return None, f"Vous devez attendre {remaining_minutes} minutes avant de pouvoir sortir."
        
        # Vérifier contrainte horaire pour EXIT
        is_valid, error_msg = check_time_constraints('EXIT')
        if not is_valid:
            return None, error_msg
        return 'EXIT', None

    # Toute autre situation : blocage
    print(f"Blocked: Invalid state for entry/exit logs.")
    return None, "État invalide des logs d'assiduité."

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

        log_type, error_msg = check_attendance_status(employee_id, db)
        print(f"Log Request: Emp {employee_id}, Conf {confidence}. Status: {log_type}")
        if not log_type:
            return {"status": "blocked", "message": error_msg}
    
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
        "timestamp": log.timestamp.isoformat(),
        "photo_capture": log.photo_capture is not None  # v2.11.0: Flag to show View button
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

# Routes d'import/export d'employés
@router.get("/employees/export")
def export_employees(format: str = "csv", db: Session = Depends(get_db)):
    """
    Exporte la liste des employés en CSV ou Excel.
    Format: csv ou excel
    """
    employees = db.query(Employee).all()
    
    # Préparer les données
    data = []
    for emp in employees:
        data.append({
            "id": emp.id,
            "name": emp.name,
            "department": emp.department or "",
            "pin": emp.pin or "",
            "created_at": emp.created_at.strftime("%Y-%m-%d %H:%M:%S") if emp.created_at else ""
        })
    
    if format == "excel":
        # Export Excel
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Employees')
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=employees.xlsx"}
        )
    else:
        # Export CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "name", "department", "pin", "created_at"])
        writer.writeheader()
        writer.writerows(data)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=employees.csv"}
        )

@router.post("/employees/import")
async def import_employees(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Importe des employés depuis un fichier CSV ou Excel.
    Les photos et embeddings doivent être ajoutés manuellement après l'import.
    """
    try:
        content = await file.read()
        
        # Déterminer le format
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Format de fichier non supporté. Utilisez CSV ou Excel.")
        
        # Valider les colonnes requises
        required_columns = ['name']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"Colonnes requises: {required_columns}")
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Vérifier si l'employé existe déjà (par nom)
                existing = db.query(Employee).filter(Employee.name == row['name']).first()
                if existing:
                    skipped_count += 1
                    continue
                
                # Créer nouvel employé (sans photos)
                new_emp = Employee(
                    name=row['name'],
                    department=row.get('department', None) if 'department' in row else None,
                    pin=str(row.get('pin', '')) if 'pin' in row and not pd.isna(row['pin']) else None
                )
                db.add(new_emp)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Ligne {index + 2}: {str(e)}")
        
        db.commit()
        
        return {
            "status": "success",
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors,
            "message": f"{imported_count} employés importés, {skipped_count} ignorés (déjà existants). Les photos doivent être ajoutées manuellement."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")
