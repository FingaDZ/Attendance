# 🔌 API Integration Guide

This system provides a comprehensive REST API for integration with external applications, HR systems, or custom dashboards.

## Base URL

```
http://your-server:8000/api
```

For HTTPS deployments, use your configured domain:
```
https://attendance-api.yourdomain.com/api
```

---

## 📋 Employee Management

### Get All Employees
```http
GET /api/employees/
```

**Query Parameters:**
- `skip` (int, optional): Pagination offset (default: 0)
- `limit` (int, optional): Max results (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "department": "Engineering"
  }
]
```

### Create Employee
```http
POST /api/employees/
Content-Type: multipart/form-data
```

**Form Data:**
- `name` (string, required)
- `department` (string, optional)
- `pin` (string, optional)
- `file1` (file, required): Photo 1
- `file2` (file, required): Photo 2 (auto-converted to B&W)
- `file3` (file, required): Photo 3

**Response:**
```json
{
  "id": 1,
  "name": "John Doe"
}
```

### Update Employee
```http
PUT /api/employees/{emp_id}
Content-Type: multipart/form-data
```

**Form Data:** Same as Create (photos are optional)

### Delete Employee
```http
DELETE /api/employees/{emp_id}
```

### Get Employee Photo
```http
GET /api/employees/{emp_id}/photo?photo_num=1
```

**Query Parameters:**
- `photo_num` (int): 1, 2, or 3

**Response:** JPEG image

---

## 📊 Attendance Logs

### Get Attendance Logs
```http
GET /api/attendance/
```

**Query Parameters:**
- `skip` (int, optional): Pagination offset
- `limit` (int, optional): Max results
- `employee_id` (int, optional): Filter by employee
- `start_date` (string, optional): ISO format (e.g., "2024-01-01")
- `end_date` (string, optional): ISO format

**Response:**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "employee_name": "John Doe",
    "camera_id": "Webcam",
    "confidence": 0.95,
    "type": "ENTRY",
    "worked_minutes": null,
    "timestamp": "2024-01-15T08:30:00"
  }
]
```

### Log Attendance (Manual)
```http
POST /api/log-attendance/
Content-Type: application/x-www-form-urlencoded
```

**Form Data:**
- `employee_id` (int, required)
- `camera_id` (string, required)
- `confidence` (float, required)

**Response:**
```json
{
  "status": "logged",
  "type": "ENTRY",
  "worked_minutes": null
}
```

### Get Work Time
```http
GET /api/work_time/?employee_id=1&date=2024-01-15
```

**Response:**
```json
{
  "work_minutes": 480,
  "status": "complete",
  "minimum_required": 300,
  "entry_time": "2024-01-15T08:00:00",
  "exit_time": "2024-01-15T16:00:00"
}
```

### Delete Attendance Log
```http
DELETE /api/attendance/{log_id}
```

### Delete All Logs
```http
DELETE /api/attendance/
```

---

## 📹 Camera Management

### Get All Cameras
```http
GET /api/cameras/
```

### Create Camera
```http
POST /api/cameras/
Content-Type: application/x-www-form-urlencoded
```

**Form Data:**
- `name` (string): Camera name
- `source` (string): "0" for webcam, RTSP URL for IP cameras

### Delete Camera
```http
DELETE /api/cameras/{cam_id}
```

### Toggle Camera
```http
PUT /api/cameras/{cam_id}/toggle
```

### Select Camera
```http
PUT /api/cameras/{cam_id}/select
```

---

## 🔍 Face Recognition

### Recognize Face from Image
```http
POST /api/recognize/
Content-Type: multipart/form-data
```

**Form Data:**
- `file` (file): Image file

**Response:**
```json
{
  "name": "John Doe",
  "confidence": 0.95,
  "employee_id": 1,
  "timestamp": "14:30:25"
}
```

### Verify PIN
```http
POST /api/verify-pin/
Content-Type: application/x-www-form-urlencoded
```

**Form Data:**
- `employee_id` (int)
- `pin` (string)

**Response:**
```json
{
  "status": "verified",
  "name": "John Doe",
  "type": "ENTRY"
}
```

---

## 📺 Live Video Stream

### Get Live Stream
```http
GET /api/stream/{camera_id}
```

**Response:** MJPEG video stream

---

## 💡 Integration Examples

### Python Example
```python
import requests

BASE_URL = "http://localhost:8000/api"

# Get all employees
response = requests.get(f"{BASE_URL}/employees/")
employees = response.json()

# Get attendance logs for today
from datetime import date
today = date.today().isoformat()
response = requests.get(
    f"{BASE_URL}/attendance/",
    params={"start_date": today, "end_date": today}
)
logs = response.json()

# Get work time for employee
response = requests.get(
    f"{BASE_URL}/work_time/",
    params={"employee_id": 1, "date": today}
)
work_data = response.json()
print(f"Worked: {work_data['work_minutes']} minutes")
```

### JavaScript Example
```javascript
const BASE_URL = "http://localhost:8000/api";

// Get all employees
fetch(`${BASE_URL}/employees/`)
  .then(res => res.json())
  .then(employees => console.log(employees));

// Get attendance logs
const today = new Date().toISOString().split('T')[0];
fetch(`${BASE_URL}/attendance/?start_date=${today}&end_date=${today}`)
  .then(res => res.json())
  .then(logs => console.log(logs));
```

### cURL Example
```bash
# Get employees
curl http://localhost:8000/api/employees/

# Get attendance logs with filters
curl "http://localhost:8000/api/attendance/?employee_id=1&start_date=2024-01-01"

# Recognize face from image
curl -X POST -F "file=@photo.jpg" http://localhost:8000/api/recognize/
```

---

## 🔐 Security Notes

1. **HTTPS**: Always use HTTPS in production.
2. **CORS**: The API allows all origins by default. Restrict this in production.
3. **Authentication**: Consider adding API keys or OAuth for external integrations.
4. **Rate Limiting**: Implement rate limiting for public-facing deployments.

---

## 📖 Interactive Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: `http://your-server:8000/docs`
- **ReDoc**: `http://your-server:8000/redoc`

These interfaces allow you to test all endpoints directly from your browser.
