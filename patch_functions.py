#!/usr/bin/env python3
"""
Final patch to update camera functions for dual webcam/RTSP support
"""
import re

def patch_camera_functions():
    filepath = r"f:\Code\attendance\frontend\src\pages\Employees.jsx"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update overlay drawing useEffect to support both video and img
    old_overlay = """    // Draw landmarks
    useEffect(() => {
        const canvas = overlayCanvasRef.current;
        const video = videoRef.current;
        if (!canvas || !video || currentResults.length === 0) {
            if (canvas) {
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
            return;
        }

        const result = currentResults[0];
        if (!result.landmarks || result.landmarks.length === 0) return;

        const ctx = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw landmarks
        ctx.fillStyle = '#00FFFF'; // Cyan
        result.landmarks.forEach(([x, y]) => {
            ctx.beginPath();
            ctx.arc(x, y, 2, 0, 2 * Math.PI);
            ctx.fill();
        });
    }, [currentResults]);"""
    
    new_overlay = """    // Draw landmarks
    useEffect(() => {
        const canvas = overlayCanvasRef.current;
        const video = videoRef.current;
        const img = imgRef.current;
        const source = selectedCamera?.source === '0' ? video : img;

        if (!canvas || !source || currentResults.length === 0) {
            if (canvas) {
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
            return;
        }

        const result = currentResults[0];
        if (!result.landmarks || result.landmarks.length === 0) return;

        const ctx = canvas.getContext('2d');
        const width = source.videoWidth || source.naturalWidth || source.width;
        const height = source.videoHeight || source.naturalHeight || source.height;
        canvas.width = width;
        canvas.height = height;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw landmarks
        ctx.fillStyle = '#00FFFF'; // Cyan
        result.landmarks.forEach(([x, y]) => {
            ctx.beginPath();
            ctx.arc(x, y, 2, 0, 2 * Math.PI);
            ctx.fill();
        });
    }, [currentResults, selectedCamera]);"""
    
    content = content.replace(old_overlay, new_overlay)
    
    # 2. Update startCamera to support RTSP
    old_start = """    const startCamera = async (photoIndex = 0) => {
        setCurrentPhotoStep(photoIndex);
        setShowCamera(true);
        const newCaptured = [...capturedImages];
        newCaptured[photoIndex] = null;
        setCapturedImages(newCaptured);
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
            startRecognitionLoop(); // Start detecting faces
        } catch (err) {
            console.error("Error accessing camera:", err);
            alert("Could not access camera");
            setShowCamera(false);
        }
    };"""
    
    new_start = """    const startCamera = async (photoIndex = 0) => {
        setCurrentPhotoStep(photoIndex);
        setShowCamera(true);
        const newCaptured = [...capturedImages];
        newCaptured[photoIndex] = null;
        setCapturedImages(newCaptured);

        // Stop any existing stream
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
        
        // Clear any existing interval
        if (videoRef.current && videoRef.current._recognitionInterval) {
            clearInterval(videoRef.current._recognitionInterval);
        }
        if (window._recognitionInterval) {
            clearInterval(window._recognitionInterval);
        }

        if (selectedCamera && selectedCamera.source !== '0') {
            // RTSP Mode
            setTimeout(() => startRecognitionLoop(), 1000);
        } else {
            // Webcam Mode
            try {
                const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
                setStream(mediaStream);
                if (videoRef.current) {
                    videoRef.current.srcObject = mediaStream;
                }
                startRecognitionLoop();
            } catch (err) {
                console.error("Error accessing camera:", err);
                alert("Could not access camera");
                setShowCamera(false);
            }
        }
    };"""
    
    content = content.replace(old_start, new_start)
    
    # 3. Update startRecognitionLoop
    old_loop_pattern = r"const startRecognitionLoop = \(\) => \{[\s\S]*?videoRef\.current\._recognitionInterval = interval;\s*\};"
    
    new_loop = """const startRecognitionLoop = () => {
        let isProcessing = false;
        const interval = setInterval(async () => {
            if (isProcessing) return;
            
            let source = null;
            if (selectedCamera?.source === '0') source = videoRef.current;
            else source = imgRef.current;

            if (source && canvasRef.current) {
                // Check if source is ready
                if (selectedCamera?.source === '0') {
                    if (source.paused || source.ended) return;
                } else {
                    if (!source.complete || source.naturalWidth === 0) return;
                }

                isProcessing = true;

                const context = canvasRef.current.getContext('2d');
                const width = source.videoWidth || source.naturalWidth;
                const height = source.videoHeight || source.naturalHeight;
                
                canvasRef.current.width = width;
                canvasRef.current.height = height;
                context.drawImage(source, 0, 0, width, height);

                canvasRef.current.toBlob(async (blob) => {
                    if (!blob) { isProcessing = false; return; }
                    const formData = new FormData();
                    formData.append('file', blob, 'capture.jpg');

                    try {
                        const response = await api.post('/recognize/', formData, {
                            headers: { 'Content-Type': 'multipart/form-data' }
                        });

                        if (response.data && response.data.name) {
                            setFaceDetected(true);
                            setCurrentResults([{
                                landmarks: response.data.landmarks || []
                            }]);
                        } else {
                            setFaceDetected(false);
                            setCurrentResults([]);
                        }
                    } catch (err) {
                        setFaceDetected(false);
                    } finally {
                        isProcessing = false;
                    }
                }, 'image/jpeg', 0.8);
            }
        }, 500);

        // Store interval
        if (videoRef.current) {
            videoRef.current._recognitionInterval = interval;
        } else {
            window._recognitionInterval = interval;
        }
    };"""
    
    content = re.sub(old_loop_pattern, new_loop, content)
    
    # 4. Update stopCamera
    old_stop = """    const stopCamera = () => {
        if (videoRef.current && videoRef.current._recognitionInterval) {
            clearInterval(videoRef.current._recognitionInterval);
        }
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
        setFaceDetected(false);
        setCurrentResults([]);
    };"""
    
    new_stop = """    const stopCamera = () => {
        if (videoRef.current && videoRef.current._recognitionInterval) {
            clearInterval(videoRef.current._recognitionInterval);
        }
        if (window._recognitionInterval) {
            clearInterval(window._recognitionInterval);
        }
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
        setFaceDetected(false);
        setCurrentResults([]);
    };"""
    
    content = content.replace(old_stop, new_stop)
    
    # 5. Update takePhoto
    old_take = """    const takePhoto = () => {
        if (videoRef.current && canvasRef.current) {
            const video = videoRef.current;
            const canvas = canvasRef.current;

            // Match canvas size to video stream to prevent distortion
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            const context = canvas.getContext('2d');

            // Apply B&W filter for Photo 2 (Index 1)
            if (currentPhotoStep === 1) {
                context.filter = 'grayscale(100%)';
            } else {
                context.filter = 'none';
            }

            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            context.filter = 'none'; // Reset filter
            const dataUrl = canvas.toDataURL('image/jpeg');
            const newCaptured = [...capturedImages];
            newCaptured[currentPhotoStep] = dataUrl;
            setCapturedImages(newCaptured);
        }
    };"""
    
    new_take = """    const takePhoto = () => {
        let source = null;
        if (selectedCamera?.source === '0') source = videoRef.current;
        else source = imgRef.current;

        if (source && canvasRef.current) {
            const canvas = canvasRef.current;
            const width = source.videoWidth || source.naturalWidth;
            const height = source.videoHeight || source.naturalHeight;

            canvas.width = width;
            canvas.height = height;

            const context = canvas.getContext('2d');

            // Apply B&W filter for Photo 2 (Index 1)
            if (currentPhotoStep === 1) {
                context.filter = 'grayscale(100%)';
            } else {
                context.filter = 'none';
            }

            context.drawImage(source, 0, 0, canvas.width, canvas.height);
            context.filter = 'none';
            const dataUrl = canvas.toDataURL('image/jpeg');
            const newCaptured = [...capturedImages];
            newCaptured[currentPhotoStep] = dataUrl;
            setCapturedImages(newCaptured);
        }
    };"""
    
    content = content.replace(old_take, new_take)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ All camera functions updated for dual webcam/RTSP support")

if __name__ == "__main__":
    patch_camera_functions()
