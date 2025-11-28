import React, { useEffect, useRef, useState } from 'react';
import { Camera, User, AlertTriangle, RefreshCw } from 'lucide-react';
import api from '../api';

const playAttendanceSound = (logType) => {
    const audio = new Audio(logType === 'ENTRY' ? '/merci.wav' : '/fin.wav');
    audio.volume = 0.5; // 50% volume
    audio.play().catch(err => console.log('Audio play failed:', err));
};

const LiveView = () => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const overlayCanvasRef = useRef(null);
    const imgRef = useRef(null);
    const [stream, setStream] = useState(null);
    const [lastDetection, setLastDetection] = useState(null);
    const [isRecognizing, setIsRecognizing] = useState(false);
    const [currentResults, setCurrentResults] = useState([]);

    // Camera Selection State
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [loadingCam, setLoadingCam] = useState(true);
    const [facingMode, setFacingMode] = useState('user'); // 'user' (front) or 'environment' (back)

    useEffect(() => {
        fetchSelectedCamera();
        return () => {
            stopCamera();
        };
    }, []);

    // Re-run camera start if facingMode changes (only for client mode)
    useEffect(() => {
        if (selectedCamera && selectedCamera.source === '0') {
            stopCamera();
            startClientCamera();
        }
    }, [facingMode]);

    // Draw landmarks on overlay canvas
    useEffect(() => {
        const canvas = overlayCanvasRef.current;
        const video = videoRef.current || imgRef.current;
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
        // Use videoWidth/Height for video, naturalWidth/Height for img
        canvas.width = video.videoWidth || video.naturalWidth;
        canvas.height = video.videoHeight || video.naturalHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw landmarks (Subtle)
        ctx.fillStyle = 'rgba(0, 255, 255, 0.3)'; // Cyan with low opacity
        result.landmarks.forEach(([x, y]) => {
            ctx.beginPath();
            ctx.arc(x, y, 1, 0, 2 * Math.PI); // Small dots (radius 1)
            ctx.fill();
        });

    }, [currentResults]);

    const fetchSelectedCamera = async () => {
        try {
            const res = await api.get('/cameras/');
            const cams = res.data;
            const selected = cams.find(c => c.is_selected === 1) || cams.find(c => c.source === '0') || cams[0];
            setSelectedCamera(selected);

            if (selected) {
                if (selected.source === '0') {
                    startClientCamera();
                } else {
                    // Server mode (RTSP), start recognition loop
                    setIsRecognizing(true);
                    startRecognitionLoop();
                }
            }
        } catch (err) {
            console.error("Failed to fetch cameras", err);
        } finally {
            setLoadingCam(false);
        }
    };

    const startClientCamera = async () => {
        setIsRecognizing(true);
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: facingMode }
            });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
            startRecognitionLoop();
        } catch (err) {
            console.error("Error accessing camera:", err);
            if (window.isSecureContext === false) {
                alert("Camera access requires a Secure Context (HTTPS or localhost). On LAN (HTTP), you must enable 'Insecure origins treated as secure' in chrome://flags.");
            } else {
                alert("Could not access camera. Ensure permissions are granted and no other app is using it.");
            }
        }
    };

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
        setIsRecognizing(false);
    };

    const toggleCameraFacing = () => {
        setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
    };

    const startRecognitionLoop = () => {
        let isProcessing = false;
        const interval = setInterval(async () => {
            if (isProcessing) return; // Skip if busy

            const source = videoRef.current || imgRef.current;

            if (source && canvasRef.current) {
                // Check if video is playing (only for video element)
                if (source.tagName === 'VIDEO' && (source.paused || source.ended)) return;
                // Check if image is loaded
                if (source.tagName === 'IMG' && !source.complete) return;

                isProcessing = true;
                const context = canvasRef.current.getContext('2d');

                const width = source.videoWidth || source.naturalWidth;
                const height = source.videoHeight || source.naturalHeight;

                if (!width || !height) {
                    isProcessing = false;
                    return;
                }

                canvasRef.current.width = width;
                canvasRef.current.height = height;
                context.drawImage(source, 0, 0, width, height);

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
                            if (confidence > 0.85 && name !== "Unknown") {
                                const logRes = await api.post(`/log_attendance/?employee_id=${response.data.employee_id}&camera_id=${selectedCamera ? selectedCamera.name : 'Webcam'}&confidence=${confidence}`);
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
        }, 500); // Check every 500ms (2 FPS detection) - Optimized for faster response

        return () => clearInterval(interval);
    };

    if (loadingCam) return <div className="p-6">Loading camera configuration...</div>;

    if (!selectedCamera) return (
        <div className="p-6 text-center">
            <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-800">No Camera Selected</h2>
            <p className="text-gray-600 mt-2">Please go to Settings and select a camera.</p>
        </div>
    );

    // Determine overlay color and text based on confidence
    const getOverlayStyle = () => {
        if (currentResults.length === 0) return { color: 'white', text: '', verified: false, positioning: false };

        const result = currentResults[0];
        const conf = result.confidence;

        // Check if user is positioning (name is "Positioning...")
        if (result.name === "Positioning...") {
            return { color: '#FFA500', text: 'Position your face in the circle', verified: false, positioning: true }; // Orange
        }

        // Treat "Unknown" as unverified regardless of confidence
        if (result.name === "Unknown") {
            return { color: '#FF0000', text: 'Unknown Face', verified: false, positioning: false }; // Red
        }

        if (conf < 0.85) {
            return { color: '#FF0000', text: `Precision: ${(conf * 100).toFixed(0)}%`, verified: false, positioning: false }; // Red
        } else {
            return { color: '#00FF00', text: `Precision: ${(conf * 100).toFixed(0)}%`, verified: true, name: result.name, positioning: false }; // Green
        }
    };

    const overlayStyle = getOverlayStyle();



    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800">Live View</h1>
                    <p className="text-gray-500 mt-1">
                        Active Camera: <span className="font-semibold text-blue-600">{selectedCamera.name}</span>
                        {selectedCamera.source === '0' && (
                            <span className="ml-2 text-xs bg-gray-100 px-2 py-1 rounded">Client Mode</span>
                        )}
                        {selectedCamera.source !== '0' && (
                            <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-1 rounded">Server Mode (RTSP)</span>
                        )}
                    </p>
                </div>

                {selectedCamera.source === '0' && (
                    <button
                        onClick={toggleCameraFacing}
                        className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg flex items-center hover:bg-gray-50 shadow-sm"
                    >
                        <RefreshCw className="w-5 h-5 mr-2" />
                        Switch Camera
                    </button>
                )}
            </div>

            {/* Status Banner */}
            {isRecognizing && (
                <div className="mb-4 p-3 bg-green-100 border border-green-300 rounded-lg text-green-800 text-sm flex justify-between items-center">
                    <div>
                        <strong>Status:</strong> Recognition active • Monitoring for faces
                    </div>
                    {lastDetection && (
                        <div className="text-green-900">
                            <strong>Last detected: {lastDetection.name} ({(lastDetection.confidence * 100).toFixed(1)}%) at {lastDetection.timestamp}</strong>
                        </div>
                    )}
                </div>
            )}

            {/* Video Container */}
            <div className="relative bg-black rounded-xl overflow-hidden shadow-2xl w-full h-[75vh] md:h-auto md:aspect-video">
                {selectedCamera.source === '0' ? (
                    <>
                        <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full h-full object-cover"
                        />
                        <canvas ref={canvasRef} style={{ display: 'none' }} />
                    </>
                ) : (
                    <>
                        <img
                            ref={imgRef}
                            src={`/api/stream/${selectedCamera.id}/clean`}
                            alt="Live Stream"
                            className="w-full h-full object-cover"
                            crossOrigin="anonymous"
                        />
                        <canvas ref={canvasRef} style={{ display: 'none' }} />
                    </>
                )}

                {/* Landmark Overlay Canvas */}
                <canvas
                    ref={overlayCanvasRef}
                    className="absolute inset-0 w-full h-full pointer-events-none"
                />

                {/* Overlay */}
                <div className="absolute inset-0 pointer-events-none">
                    {/* Oval Positioning Guide - Responsive */}
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex items-center justify-center">
                        <div className="border-4 border-white border-opacity-40 rounded-full w-[60vw] h-[40vh] md:w-[min(70vw,448px)] md:h-[min(85vh,560px)] relative">
                            {/* Static Center Crosshair (+) */}
                            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-8 h-8 opacity-60">
                                <div className="absolute top-1/2 left-0 w-full h-1 bg-cyan-400 -translate-y-1/2"></div>
                                <div className="absolute left-1/2 top-0 h-full w-1 bg-cyan-400 -translate-x-1/2"></div>
                            </div>
                        </div>
                    </div>

                    {/* Recognition Status Overlay */}
                    {overlayStyle.positioning ? (
                        <div className="absolute top-4 left-1/2 transform -translate-x-1/2">
                            <div className="bg-orange-500 bg-opacity-90 text-white px-6 py-3 rounded-lg shadow-lg">
                                <p className="text-lg font-semibold">{overlayStyle.text}</p>
                                <p className="text-sm">Center your face</p>
                            </div>
                        </div>
                    ) : overlayStyle.verified ? (
                        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                            <div className="bg-green-500 bg-opacity-90 text-white px-8 py-4 rounded-lg shadow-lg">
                                <User className="w-16 h-16 mx-auto mb-2" />
                                <p className="text-2xl font-bold">{overlayStyle.name}</p>
                                <p className="text-lg">{overlayStyle.text}</p>
                                <p className="text-sm mt-2">✓ Verified</p>
                            </div>
                        </div>
                    ) : (
                        overlayStyle.text && (
                            <div className="absolute top-4 left-1/2 transform -translate-x-1/2">
                                <div className="bg-red-500 bg-opacity-90 text-white px-6 py-3 rounded-lg shadow-lg">
                                    <p className="text-lg font-semibold">{overlayStyle.text}</p>
                                    <p className="text-sm">Minimum: 85%</p>
                                </div>
                            </div>
                        )
                    )}
                </div>
            </div>

            {/* Info Panel */}
            <div className="mt-6 bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                <h3 className="font-semibold text-gray-800 mb-2">Recognition Info</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span className="text-gray-500">Confidence Threshold:</span>
                        <span className="ml-2 font-medium text-gray-800">85%</span>
                    </div>
                    <div>
                        <span className="text-gray-500">Recognition Mode:</span>
                        <span className="ml-2 font-medium text-gray-800">
                            {selectedCamera.source === '0' ? 'Client-Side' : 'Server-Side'}
                        </span>
                    </div>
                    <div>
                        <span className="text-gray-500">Liveness Detection:</span>
                        <span className="ml-2 font-medium text-green-600">✓ Enabled (Passive)</span>
                    </div>
                    <div>
                        <span className="text-gray-500">Anti-Spoofing:</span>
                        <span className="ml-2 font-medium text-blue-600">Active</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LiveView;
