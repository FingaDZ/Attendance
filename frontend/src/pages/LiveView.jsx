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
                    // Server mode (RTSP), nothing to start on client, just show image
                    setIsRecognizing(true); // Server handles recognition
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
            alert("Could not access camera. Ensure permissions are granted.");
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

                            // Log attendance if confidence > 0.87 AND name is not Unknown
                            if (confidence > 0.87 && name !== "Unknown") {
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
                }, 'image/jpeg', 0.95);
            }
        }, 2000); // Check every 2 seconds to reduce CPU load

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

        if (conf < 0.87) {
            return { color: '#FF0000', text: `Precision: ${(conf * 100).toFixed(0)}%`, verified: false, positioning: false }; // Red
        } else {
            return { color: '#00FF00', text: `Precision: ${(conf * 100).toFixed(0)}%`, verified: true, name: result.name, positioning: false }; // Green
        }
    };

    const overlayStyle = getOverlayStyle();

    // Draw landmarks on overlay canvas
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
            ctx.arc(x, y, 2, 0, 2 * Math.PI); // Larger dots (radius 2)
            ctx.fill();
        });

    }, [currentResults]);

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
                    <img
                        src={`/api/stream/${selectedCamera.id}`}
                        alt="Live Stream"
                        className="w-full h-full object-cover"
                    />
                )}

                {/* Landmark Overlay Canvas */}
                <canvas
                    ref={overlayCanvasRef}
                    className="absolute inset-0 w-full h-full pointer-events-none"
                />

                {/* Overlay */}
                <div className="absolute inset-0 pointer-events-none">
                    {/* Oval Positioning Guide - Responsive */}
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                        <div className="border-4 border-white border-opacity-40 rounded-full w-[60vw] h-[40vh] md:w-[min(70vw,448px)] md:h-[min(85vh,560px)]"></div>
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
                                    <p className="text-sm">Minimum: 87%</p>
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
                        <span className="ml-2 font-medium text-gray-800">87%</span>
                    </div>
                    <div>
                        <span className="text-gray-500">Recognition Mode:</span>
                        <span className="ml-2 font-medium text-gray-800">
                            {selectedCamera.source === '0' ? 'Client-Side' : 'Server-Side'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LiveView;
