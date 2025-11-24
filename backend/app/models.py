from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, Float
from sqlalchemy.sql import func
from .database import Base
import datetime

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    department = Column(String, nullable=True)
    # Storing 6 embeddings as bytes (pickle or numpy tobytes) for better accuracy
    embedding1 = Column(LargeBinary, nullable=True)
    embedding2 = Column(LargeBinary, nullable=True)
    embedding3 = Column(LargeBinary, nullable=True)
    embedding4 = Column(LargeBinary, nullable=True) # v1.6.5
    embedding5 = Column(LargeBinary, nullable=True) # v1.6.5
    embedding6 = Column(LargeBinary, nullable=True) # v1.6.5
    # Store 6 actual images for display
    photo1 = Column(LargeBinary, nullable=True)
    photo2 = Column(LargeBinary, nullable=True)
    photo3 = Column(LargeBinary, nullable=True)
    photo4 = Column(LargeBinary, nullable=True) # v1.6.5: Additional angle (left rotation)
    photo5 = Column(LargeBinary, nullable=True) # v1.6.5: Additional angle (right rotation)
    photo6 = Column(LargeBinary, nullable=True) # v1.6.5: Additional angle (tilt)
    pin = Column(String, nullable=True) # 4-digit PIN
    created_at = Column(DateTime(timezone=False), default=datetime.datetime.now)

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, index=True)
    employee_name = Column(String)
    camera_id = Column(String, nullable=True)
    confidence = Column(Float)
    type = Column(String, nullable=True) # 'ENTRY' or 'EXIT'
    worked_minutes = Column(Integer, nullable=True) # Minutes worked for the day
    timestamp = Column(DateTime(timezone=False), default=datetime.datetime.now, index=True)

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    source = Column(String) # URL or Index
    is_active = Column(Integer, default=1) # 1 for active, 0 for inactive
    is_selected = Column(Integer, default=0) # 1 if this is the currently selected camera for LiveView

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=True)
    description = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=False), default=datetime.datetime.now, onupdate=datetime.datetime.now)
