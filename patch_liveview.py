#!/usr/bin/env python3
"""
Patch LiveView.jsx to support RTSP with dynamic overlays
"""

def patch_liveview():
    filepath = r"f:\Code\attendance\frontend\src\pages\LiveView.jsx"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Add imgRef
    content = content.replace(
        "    const videoRef = useRef(null);\r\n    const canvasRef = useRef(null);",
        "    const videoRef = useRef(null);\r\n    const imgRef = useRef(null); // For RTSP stream\r\n    const canvasRef = useRef(null);"
    )
    
    # 2. Update startRecognitionLoop - find and replace the entire function
    old_loop = """    const startRecognitionLoop = () => {
        let isProcessing = false;
        const interval = setInterval(async () => {
            if (isProcessing) return; // Skip if busy

            if (videoRef.current && canvasRef.current && !videoRef.current.paused && !videoRef.current.ended) {
                isProcessing = true;
                const context = canvasRef.current.getContext('2d');
                canvasRef.current.width = videoRef.current.videoWidth;
                canvasRef.current.height = videoRef.current.videoHeight;
                context.drawImage(videoRef.current, 0, 0);

                canvasRef.current.toBlob(async (blob) => {
                    if (!blob) {
                        isProcessing = false;
                        return;
                    }
                    const formData = new FormData();
                    formData.append('file', blob, 'capture.jpg');

                    try {
                        const response = await api.post('/recognize/', formData, {
                            headers: { 'Content-Type': 'multipart/form-data' }
                        });

                        if (response.data && response.data.name) {
                            const { name, confidence, timestamp, landmarks } = response.data;
                            setLastDetection({ name, confidence, timestamp });

                            // Log attendance if confidence > 0.85 AND name is not Unknown
                            if (confidence > 0.85 && name !== \"Unknown\") {
                                const logRes = await api.post(`/log_attendance/?employee_id=${response.data.employee_id}&camera_id=Webcam&confidence=${confidence}`);
                                if (logRes.data.status === 'logged') {
                                    playAttendanceSound(logRes.data.type);
                                }
                            }

                            // Update overlay with results
                            setCurrentResults([{
                                name,
                                confidence,
                                bbox: [0, 0, 0, 0], // Placeholder
                                landmarks: landmarks || []
                            }]);
                        } else {
                            setCurrentResults([]);
                        }
                    } catch (err) {
                        // Ignore minor errors
                    } finally {
                        isProcessing = false;
                    }
                }, 'image/jpeg', 0.75);
            }
        }, 300); // Optimized: 300ms interval (was 500ms)

        return () => clearInterval(interval);
    };"""
    
    new_loop = """    const startRecognitionLoop = () => {
        let isProcessing = false;
        const interval = setInterval(async () => {
            if (isProcessing) return; // Skip if busy

            let source = null;
            if (selectedCamera.source === '0') {
                source = videoRef.current;
            } else {
                source = imgRef.current; // RTSP image
            }

            if (source && canvasRef.current) {
                // Check if source is ready
                if (selectedCamera.source === '0') {
                    if (source.paused || source.ended) return;
                } else {
                    // For img element, check if loaded
                    if (!source.complete || source.naturalWidth === 0) return;
                }

                isProcessing = true;
                const context = canvasRef.current.getContext('2d');
                const width = source.videoWidth || source.naturalWidth;
                const height = source.videoHeight || source.naturalHeight;
                
                // Optimize: Reduce resolution before sending
                const MAX_WIDTH = 640;
                const MAX_HEIGHT = 480;
                let targetWidth = width;
                let targetHeight = height;
                
                if (width > MAX_WIDTH || height > MAX_HEIGHT) {
                    const scale = Math.min(MAX_WIDTH / width, MAX_HEIGHT / height);
                    targetWidth = Math.floor(width * scale);
                    targetHeight = Math.floor(height * scale);
                }
                
                canvasRef.current.width = targetWidth;
                canvasRef.current.height = targetHeight;
                context.drawImage(source, 0, 0, targetWidth, targetHeight);

                canvasRef.current.toBlob(async (blob) => {
                    if (!blob) {
                        isProcessing = false;
                        return;
                    }
                    const formData = new FormData();
                    formData.append('file', blob, 'capture.jpg');

                    try {
                        const response = await api.post('/recognize/', formData, {
                            headers: { 'Content-Type': 'multipart/form-data' }
                        });

                        if (response.data && response.data.name) {
                            const { name, confidence, timestamp, landmarks } = response.data;
                            setLastDetection({ name, confidence, timestamp });

                            // Log attendance if confidence > 0.85 AND name is not Unknown
                            if (confidence > 0.85 && name !== \"Unknown\") {
                                const cameraName = selectedCamera.source === '0' ? 'Webcam' : selectedCamera.name;
                                const logRes = await api.post(`/log_attendance/?employee_id=${response.data.employee_id}&camera_id=${cameraName}&confidence=${confidence}`);
                                if (logRes.data.status === 'logged') {
                                    playAttendanceSound(logRes.data.type);
                                }
                            }

                            // Update overlay with results
                            setCurrentResults([{
                                name,
                                confidence,
                                bbox: [0, 0, 0, 0], // Placeholder
                                landmarks: landmarks || []
                            }]);
                        } else {
                            setCurrentResults([]);
                        }
                    } catch (err) {
                        // Ignore minor errors
                    } finally {
                        isProcessing = false;
                    }
                }, 'image/jpeg', 0.75);
            }
        }, 300); // Optimized: 300ms interval (was 500ms)

        return () => clearInterval(interval);
    };"""
    
    content = content.replace(old_loop, new_loop)
    
    # 3. Update RTSP rendering to use /clean endpoint and add imgRef + canvas
    old_rtsp = """                ) : (
                    <img
                        src={`/api/stream/${selectedCamera.id}`}
                        alt=\"Live Stream\"
                        className=\"w-full h-full object-cover\"
                    />
                )}"""
    
    new_rtsp = """                ) : (
                    <>
                        <img
                            ref={imgRef}
                            src={`/api/stream/${selectedCamera.id}/clean`}
                            alt=\"Live Stream\"
                            className=\"w-full h-full object-cover\"
                            crossOrigin=\"anonymous\"
                        />
                        <canvas ref={canvasRef} style={{ display: 'none' }} />
                    </>
                )}"""
    
    content = content.replace(old_rtsp, new_rtsp)
    
    # 4. Start recognition loop for RTSP
    old_rtsp_start = """                } else {
                    // Server mode (RTSP), nothing to start on client, just show image
                    setIsRecognizing(true); // Server handles recognition
                }"""
    
    new_rtsp_start = """                } else {
                    // Server mode (RTSP), start recognition loop
                    setIsRecognizing(true);
                    startRecognitionLoop();
                }"""
    
    content = content.replace(old_rtsp_start, new_rtsp_start)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ LiveView.jsx patched successfully")
    print("   - Added imgRef for RTSP")
    print("   - Updated startRecognitionLoop for dual-source")
    print("   - Changed RTSP to use /clean endpoint")
    print("   - Reduced interval to 300ms")
    print("   - Added resolution optimization (640x480)")

if __name__ == "__main__":
    patch_liveview()
