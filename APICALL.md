# API Documentation - Attendance System v1.6.6

## Base URL

### LAN Access (Internal Network)
```
http://192.168.20.56:8000/api
```

### External Access
```
https://hgq09k0j9p1.sn.mynetname.net/api
```

**Note**: The system is configured to accept connections from all networks.

## Employee Management

### Create Employee
**POST** `/employees/`

Register a new employee with 6 face photos.

**Request (multipart/form-data):**
- `name` (string, required)
- `department` (string, optional)
- `pin` (string, optional): 4-digit PIN
- `file1` to `file6` (file, required): 6 face photos

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "department": "Engineering",
  "message": "Employee registered successfully"
}
```

---

### Get All Employees
**GET** `/employees/`

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 100)

**Response:**
```json
[
  {"id": 1, "name": "John Doe", "department": "Engineering"}
]
```

---

### Get Employee Photo
**GET** `/employees/{emp_id}/photo?photo_num={1-6}`

Returns JPEG image.

---

### Update Employee
**PUT** `/employees/{emp_id}`

**Request (multipart/form-data):**
- `name`, `department`, `pin` (optional)
- `file1` to `file6` (optional)

---

### Delete Employee
**DELETE** `/employees/{emp_id}`

---

## Attendance Logs

### Get Attendance Logs
**GET** `/attendance/`

**Query Parameters:**
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)
- `employee_id` (int)
- `camera_id` (string)
- `limit` (int, default: 1000)

**Response:**
```json
[
  {
    "id": 1,
    "employee_id": 1,
    "employee_name": "John Doe",
    "timestamp": "2025-11-24T08:30:15",
    "camera_id": "1",
    "confidence": 0.95,
    "type": "ENTRY",
    "worked_minutes": 555
  }
]
```

---

### Delete Log
**DELETE** `/attendance/{log_id}`

---

### Delete All Logs
**DELETE** `/attendance/`

---

## Face Recognition

### Recognize Face
**POST** `/recognize/`

**Request (multipart/form-data):**
- `file` (image file)

**Response:**
```json
{
  "name": "John Doe",
  "employee_id": 1,
  "confidence": 0.95,
  "liveness_score": 0.78,
  "type": "ENTRY",
  "message": "Entry logged successfully"
}
```

---

## PIN Verification

### Verify PIN
**POST** `/verify-pin/`

**Request (multipart/form-data):**
- `employee_id` (int)
- `pin` (string): 4 digits

**Response:**
```json
{
  "status": "verified",
  "name": "John Doe",
  "type": "ENTRY"
}
```

---

## Camera Management

### Get Cameras
**GET** `/cameras/`

### Add Camera
**POST** `/cameras/`

**Request (JSON):**
```json
{
  "name": "Main Entrance",
  "source": "0",
  "is_active": true
}
```

### Update Camera
**PUT** `/cameras/{camera_id}`

### Delete Camera
**DELETE** `/cameras/{camera_id}`

---

## Integration Examples

### Python
```python
import requests

# Add employee
files = {f'file{i}': open(f'photo{i}.jpg', 'rb') for i in range(1, 7)}
data = {'name': 'John Doe', 'department': 'Engineering', 'pin': '1234'}
r = requests.post('http://192.168.20.56:8000/api/employees/', files=files, data=data)

# Get logs
r = requests.get('http://192.168.20.56:8000/api/attendance/', params={
    'start_date': '2025-11-01',
    'end_date': '2025-11-30'
})
```

### JavaScript
```javascript
const form = new FormData();
form.append('name', 'John Doe');
for (let i = 1; i <= 6; i++) {
  form.append(`file${i}`, fs.createReadStream(`photo${i}.jpg`));
}

fetch('http://192.168.20.56:8000/api/employees/', {
  method: 'POST',
  body: form
});
```

---

## Notes
- Confidence threshold: 85%
- Liveness threshold: 40%
- All timestamps in UTC
- Entry/Exit logic: automatic alternation
