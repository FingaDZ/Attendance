#!/usr/bin/env python3
"""
Script to patch Employees.jsx to add RTSP camera selection support.
This avoids file corruption issues from manual editing.
"""

def patch_employees_jsx():
    filepath = r"f:\Code\attendance\frontend\src\pages\Employees.jsx"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add imgRef after videoRef
    content = content.replace(
        "    const videoRef = useRef(null);\r\n    const canvasRef = useRef(null);",
        "    const videoRef = useRef(null);\r\n    const imgRef = useRef(null); // For RTSP stream\r\n    const canvasRef = useRef(null);"
    )
    
    # 2. Add camera selection state after currentResults
    content = content.replace(
        "    const [currentResults, setCurrentResults] = useState([]); // For landmarks\r\n\r\n    const fetchEmployees",
        """    const [currentResults, setCurrentResults] = useState([]); // For landmarks
    
    // Camera Selection
    const [cameras, setCameras] = useState([]);
    const [selectedCamera, setSelectedCamera] = useState(null);

    useEffect(() => {
        const getCameras = async () => {
            try {
                const res = await api.get('/cameras/');
                setCameras(res.data);
                const defaultCam = res.data.find(c => c.source === '0') || res.data[0];
                setSelectedCamera(defaultCam);
            } catch (err) {
                console.error("Failed to fetch cameras", err);
            }
        };
        getCameras();
    }, []);

    const fetchEmployees"""
    )
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Step 1: Added imgRef and camera selection state")

if __name__ == "__main__":
    patch_employees_jsx()
