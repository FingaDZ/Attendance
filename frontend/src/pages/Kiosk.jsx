import React, { useEffect, useRef, useState } from 'react';
import { Camera, RefreshCw, Clock } from 'lucide-react';
import api from '../api';
import PinPanel from '../components/PinPanel';
import { parseAttendanceResponse } from '../utils/attendanceUtils';

const playAttendanceSound = (logType) => {
    let audioFile = '/merci.wav'; // Default SUCCESS

    if (logType === 'EXIT') audioFile = '/fin.wav';
    else if (logType === 'ALREADY_LOGGED') audioFile = '/inok.wav';
    else if (logType === 'MIN_TIME') audioFile = '/mintime.wav';

    const audio = new Audio(audioFile);
    audio.volume = 0.5;
    audio.play().catch(err => console.log('Audio play failed:', err));
};

const Kiosk = () => {
    // --- Video State ---
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const imgRef = useRef(null);
    const [stream, setStream] = useState(null);
    const [currentResults, setCurrentResults] = useState([]);
    const [selectedCamera, setSelectedCamera] = useState(null);
    const [loadingCam, setLoadingCam] = useState(true);
    const [facingMode, setFacingMode] = useState('user');

    // --- Clock State ---
    const [currentTime, setCurrentTime] = useState(new Date());

    // --- Clock Effect ---
    useEffect(() => {
        const timer = setInterval(() => setCurrentTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    // --- Camera Init ---
    useEffect(() => {
        fetchSelectedCamera();
        return () => stopCamera();
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
            const cams = Array.isArray(res.data) ? res.data : [];

            if (!Array.isArray(res.data)) {
                console.error("Invalid API response for cameras:", res.data);
                // If we get HTML (string), it's likely a proxy/port issue
                if (typeof res.data === 'string' && res.data.includes('<!doctype html>')) {
                    console.error("Received HTML instead of JSON. Check API port (8000 vs 3000).");
                }
            }

            const selected = cams.find(c => c.is_selected === 1) || cams.find(c => c.source === '0') || cams[0];
            setSelectedCamera(selected);

            if (selected) {
                if (selected.source === '0') {
                    startClientCamera();
                } else {
                    // Server mode (RTSP), start recognition loop
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
        }
    };

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
    };

    const startRecognitionLoop = () => {
        let isProcessing = false;
        const interval = setInterval(async () => {
            if (isProcessing) return;

            const source = videoRef.current || imgRef.current;

            if (source && canvasRef.current) {
                if (source.tagName === 'VIDEO' && (source.paused || source.ended)) return;
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
                            const { name, confidence, landmarks } = response.data;

                            if (confidence > 0.85 && name !== "Unknown") {
                                const logRes = await api.post(`/log_attendance/?employee_id=${response.data.employee_id}&camera_id=${selectedCamera ? selectedCamera.name : 'Webcam'}&confidence=${confidence}`);

                                // UTILISATION DE LA LOGIQUE UNIFIÉE
                                const result = parseAttendanceResponse(logRes.data);

                                if (result.success) {
                                    playAttendanceSound(result.type);
                                    setCurrentResults([{
                                        name, confidence, landmarks: landmarks || [],
                                        verified: true
                                    }]);
                                } else if (result.blocked) {
                                    // Play specific sound if defined (ALREADY_LOGGED, MIN_TIME)
                                    if (result.sound) {
                                        playAttendanceSound(result.sound);
                                    }

                                    setCurrentResults([{
                                        name, confidence, landmarks: landmarks || [],
                                        blocked: true,
                                        blockReason: result.reason,
                                        blockSubtext: result.subtext,
                                        blockColor: result.color
                                    }]);
                                    return; // Keep error displayed
                                }
                            }

                            // Update overlay if not blocked
                            setCurrentResults([{
                                name, confidence, landmarks: landmarks || []
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
        }, 500);

        return () => clearInterval(interval);
    };

    // --- Overlay Logic ---
    const getOverlayStyle = () => {
        if (currentResults.length === 0) return null;
        const result = currentResults[0];

        // 1. Blocage (Prioritaire)
        if (result.blocked) {
            return {
                color: result.blockColor,
                title: result.blockReason, // Will be translated in attendanceUtils
                subtitle: result.blockSubtext // Will be translated in attendanceUtils
            };
        }

        // 2. Succès
        if (result.verified) {
            return {
                color: '#10B981', // Green
                title: `Bienvenue ${result.name.split(' ')[0]}`,
                subtitle: 'Pointage enregistré / تم تسجيل الدخول'
            };
        }

        // 3. Confiance Faible
        if (result.confidence > 0 && result.confidence <= 0.85) {
            return {
                color: '#F59E0B', // Amber
                title: 'Confiance Faible / ثقة منخفضة',
                subtitle: 'Approchez-vous / اقترب أكثر'
            };
        }

        // 4. Visage Inconnu
        if (result.name === "Unknown") {
            return {
                color: '#EF4444', // Red
                title: 'Visage Inconnu / وجه غير معروف',
                subtitle: 'Non autorisé / غير مصرح'
            };
        }

        return null;
    };

    const overlay = getOverlayStyle();

    if (loadingCam) return <div className="h-screen flex items-center justify-center bg-black text-white">Chargement du Kiosque...</div>;

    return (
        <div className="h-screen w-screen bg-black overflow-hidden flex flex-col md:flex-row">
            {/* --- LEFT: VIDEO AREA (70%) --- */}
            <div className="relative flex-1 bg-black h-[60vh] md:h-full">
                {/* Video Feed */}
                {selectedCamera?.source === '0' ? (
                    <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                ) : (
                    <img ref={imgRef} src={`/api/stream/${selectedCamera?.id}/clean`} alt="Stream" className="w-full h-full object-cover" crossOrigin="anonymous" />
                )}
                <canvas ref={canvasRef} style={{ display: 'none' }} />

                {/* Overlay UI */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    {/* Positioning Guide - Enlarged by 25% (60vw->75vw, 40vh->50vh) */}
                    <div className="absolute w-[75vw] h-[75vw] md:w-[50vh] md:h-[50vh] border-4 border-white/30 rounded-full transition-all duration-500">
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 text-cyan-400/50">+</div>
                        <div className="absolute bottom-[-40px] left-1/2 -translate-x-1/2 text-white/50 text-sm whitespace-nowrap font-cairo">
                            Positionnez votre visage / ضع وجهك في الإطار
                        </div>
                    </div>

                    {/* Status Message */}
                    {overlay && (
                        <div className="absolute bottom-10 md:bottom-20 animate-in fade-in zoom-in duration-300">
                            <div
                                style={{ backgroundColor: overlay.color }}
                                className="px-8 py-4 rounded-2xl shadow-2xl text-white text-center min-w-[300px]"
                            >
                                <h2 className="text-3xl font-bold mb-1 font-cairo">{overlay.title}</h2>
                                <p className="text-lg opacity-90 font-cairo">{overlay.subtitle}</p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Clock Overlay (Top Left) */}
                <div className="absolute top-6 left-6 bg-black/50 backdrop-blur-md px-4 py-2 rounded-lg text-white border border-white/10">
                    <div className="flex items-center space-x-2">
                        <Clock className="w-5 h-5 text-blue-400" />
                        <span className="text-xl font-mono font-bold">
                            {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1 uppercase tracking-wider">
                        {currentTime.toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' })}
                    </div>
                </div>

                {/* Watermark (Top Right) */}
                <div className="absolute top-6 right-6 opacity-50 text-white/80 font-semibold tracking-widest text-xs md:text-sm z-20 pointer-events-none shadow-black drop-shadow-md">
                    Powered by <span className="text-blue-400 font-bold">AIRBAND</span>
                </div>

                {/* Confidence Score (Top Center) */}
                {currentResults.length > 0 && currentResults[0].confidence > 0 && (
                    <div className={`absolute top-6 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-white font-bold text-sm md:text-base shadow-lg transition-colors duration-300 ${currentResults[0].confidence < 0.70 ? 'bg-red-500' :
                            currentResults[0].confidence < 0.80 ? 'bg-orange-500' :
                                currentResults[0].confidence < 0.85 ? 'bg-blue-500' :
                                    'bg-green-500'
                        }`}>
                        {(currentResults[0].confidence * 100).toFixed(1)}%
                    </div>
                )}
            </div>

            {/* --- RIGHT: PIN PANEL (30%) --- */}
            <div className="h-[40vh] md:h-full md:w-[350px] lg:w-[400px] border-t md:border-t-0 md:border-l border-gray-800 z-10">
                <PinPanel
                    onAuthSuccess={(result) => {
                        playAttendanceSound(result.type);
                        // Optional: Show success in video overlay too?
                    }}
                />
            </div>
        </div>
    );
};

export default Kiosk;
