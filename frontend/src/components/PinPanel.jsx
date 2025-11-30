import React, { useState, useEffect, useRef } from 'react';
import { Delete, Check, AlertTriangle, User } from 'lucide-react';
import api from '../api';
import { parseAttendanceResponse } from '../utils/attendanceUtils';

const PinPanel = ({ onAuthSuccess }) => {
    const [pin, setPin] = useState('');
    const [empId, setEmpId] = useState('');
    const [step, setStep] = useState('ID'); // 'ID' or 'PIN'
    const [status, setStatus] = useState('idle'); // idle, loading, success, error, blocked
    const [feedback, setFeedback] = useState(null); // { reason, subtext, color }

    // v2.11.0: Camera for photo capture
    const videoRef = useRef(null);
    const [stream, setStream] = useState(null);
    const [cameraReady, setCameraReady] = useState(false);

    // v2.11.0: Initialize camera (silent, background)
    useEffect(() => {
        const startCamera = async () => {
            try {
                const mediaStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 640, height: 480 }
                });
                setStream(mediaStream);
                if (videoRef.current) {
                    videoRef.current.srcObject = mediaStream;
                    videoRef.current.play();
                }
                setCameraReady(true);
            } catch (err) {
                console.warn('Camera not available for photo capture:', err);
                setCameraReady(false);
            }
        };

        startCamera();

        return () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    // Auto-reset after inactivity or success
    useEffect(() => {
        let timer;
        if (status !== 'idle' && status !== 'loading') {
            timer = setTimeout(() => {
                resetState();
            }, 5000); // 5s display time
        }
        return () => clearTimeout(timer);
    }, [status]);

    const resetState = () => {
        setPin('');
        setEmpId('');
        setStep('ID');
        setStatus('idle');
        setFeedback(null);
    };

    // v2.11.0: Capture photo from video stream
    const capturePhoto = () => {
        if (!cameraReady || !videoRef.current) return null;

        try {
            const canvas = document.createElement('canvas');
            canvas.width = 640;
            canvas.height = 480;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(videoRef.current, 0, 0, 640, 480);
            return canvas.toDataURL('image/jpeg', 0.8);
        } catch (err) {
            console.error('Photo capture failed:', err);
            return null;
        }
    };

    const handleNumberClick = (num) => {
        if (status === 'success' || status === 'blocked') return;

        if (step === 'ID') {
            if (empId.length < 6) setEmpId(prev => prev + num);
        } else {
            if (pin.length < 4) setPin(prev => prev + num);
        }
    };

    const handleClear = () => {
        if (step === 'PIN' && pin.length === 0) {
            setStep('ID');
        } else if (step === 'PIN') {
            setPin('');
        } else {
            setEmpId('');
        }
    };

    const playAttentionBeep = () => {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.type = 'sine';
            osc.frequency.value = 880; // A5 (High pitch for attention)

            const now = ctx.currentTime;

            // 3 bips de 500ms avec courte pause
            // Beep 1
            gain.gain.setValueAtTime(0.1, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);

            // Beep 2
            gain.gain.setValueAtTime(0.1, now + 0.6);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 1.1);

            // Beep 3
            gain.gain.setValueAtTime(0.1, now + 1.2);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 1.7);

            osc.start(now);
            osc.stop(now + 1.8);
        } catch (e) {
            console.error("AudioContext error:", e);
        }
    };

    const handleEnter = async () => {
        if (step === 'ID') {
            if (empId.length > 0) {
                playAttentionBeep(); // Signal sonore pour attirer l'attention
                setStep('PIN');
            }
        } else {
            if (pin.length > 0) {
                await submitPin();
            }
        }
    };

    const submitPin = async () => {
        setStatus('loading');
        try {
            // v2.11.0: Capture photo before sending
            const photoBase64 = capturePhoto();

            const formData = new FormData();
            formData.append('pin', pin);
            formData.append('employee_id', empId);

            // v2.11.0: Add photo if captured
            if (photoBase64) {
                const photoBlob = await fetch(photoBase64).then(r => r.blob());
                formData.append('photo', photoBlob, 'capture.jpg');
            }

            // Correct endpoint: /verify-pin/ (POST)
            const response = await api.post('/verify-pin/', formData);
            const result = parseAttendanceResponse(response.data);

            if (result.success) {
                setStatus('success');
                setFeedback({
                    reason: result.user,
                    subtext: result.type === 'ENTRY' ? 'Entrée Enregistrée' : 'Sortie Enregistrée',
                    color: '#10B981' // Green
                });
                if (onAuthSuccess) onAuthSuccess(result);
            } else if (result.blocked) {
                setStatus('blocked');
                setFeedback({
                    reason: result.reason,
                    subtext: result.subtext,
                    color: result.color
                });
                // Play sound for blocked cases if handler provided
                if (onAuthSuccess) onAuthSuccess(result);
            } else {
                // Should not happen with parseAttendanceResponse for verified/blocked
                // But handles unexpected cases
                setStatus('error');
                setFeedback({
                    reason: 'Erreur',
                    subtext: 'Erreur inconnue',
                    color: '#FF0000'
                });
            }
        } catch (error) {
            console.error('PIN Auth Error:', error);
            setStatus('error');
            setFeedback({
                reason: 'Erreur',
                subtext: error.response?.data?.detail || 'Erreur de connexion',
                color: '#FF0000'
            });
        }
    };

    // Render Logic
    const isBlocked = status === 'blocked';
    const isSuccess = status === 'success';
    const isError = status === 'error';

    return (
        <div className="flex flex-col h-full bg-gray-900 text-white p-4 shadow-2xl overflow-hidden">
            {/* Header / Display Area */}
            <div className="flex-shrink-0 flex flex-col justify-center items-center mb-4 min-h-[100px] md:min-h-[160px]">
                {status === 'idle' || status === 'loading' ? (
                    <>
                        <h2 className="text-gray-400 text-xs md:text-sm uppercase tracking-wider mb-1 md:mb-2">
                            {step === 'ID' ? 'Entrez votre ID' : 'Entrez votre PIN'}
                        </h2>
                        <div className="text-3xl md:text-4xl font-mono font-bold tracking-widest text-white border-b-2 border-blue-500 pb-1 md:pb-2 px-4 min-w-[100px] md:min-w-[120px] text-center">
                            {step === 'ID' ? (empId || '_') : (pin.replace(/./g, '•') || '_')}
                        </div>
                        {status === 'loading' && <div className="mt-2 text-blue-400 animate-pulse text-sm">Vérification...</div>}
                    </>
                ) : (
                    <div
                        className={`flex flex-col items-center justify-center p-4 rounded-xl w-full animate-in fade-in zoom-in duration-300 h-full`}
                        style={{ backgroundColor: feedback?.color }}
                    >
                        {isSuccess ? <User className="w-8 h-8 md:w-12 md:h-12 mb-1 md:mb-2" /> : <AlertTriangle className="w-8 h-8 md:w-12 md:h-12 mb-1 md:mb-2" />}
                        <h3 className="text-lg md:text-xl font-bold text-center leading-tight">{feedback?.reason}</h3>
                        <p className="text-xs md:text-sm opacity-90 mt-1 text-center">{feedback?.subtext}</p>
                    </div>
                )}
            </div>

            {/* Numpad - Flex Grow to fill space */}
            <div className="flex-1 grid grid-cols-3 gap-2 md:gap-4 min-h-0">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
                    <button
                        key={num}
                        onClick={() => handleNumberClick(num.toString())}
                        className="bg-gray-800 rounded-lg md:rounded-xl text-xl md:text-2xl font-semibold hover:bg-gray-700 active:bg-gray-600 transition-colors shadow-sm md:shadow-lg border-b-2 md:border-b-4 border-gray-950 active:border-b-0 active:translate-y-1 flex items-center justify-center"
                    >
                        {num}
                    </button>
                ))}
                <button
                    onClick={handleClear}
                    className="bg-red-900/30 text-red-400 rounded-lg md:rounded-xl flex items-center justify-center hover:bg-red-900/50 transition-colors"
                >
                    <Delete className="w-5 h-5 md:w-6 md:h-6" />
                </button>
                <button
                    onClick={() => handleNumberClick('0')}
                    className="bg-gray-800 rounded-lg md:rounded-xl text-xl md:text-2xl font-semibold hover:bg-gray-700 active:bg-gray-600 transition-colors shadow-sm md:shadow-lg border-b-2 md:border-b-4 border-gray-950 active:border-b-0 active:translate-y-1 flex items-center justify-center"
                >
                    0
                </button>
                <button
                    onClick={handleEnter}
                    className="bg-blue-600 text-white rounded-lg md:rounded-xl flex items-center justify-center hover:bg-blue-500 active:bg-blue-700 transition-colors shadow-sm md:shadow-lg border-b-2 md:border-b-4 border-blue-800 active:border-b-0 active:translate-y-1"
                >
                    <Check className="w-6 h-6 md:w-8 md:h-8" />
                </button>
            </div>



            {/* v2.11.0: Hidden video for photo capture */}
            <video
                ref={videoRef}
                style={{ display: 'none' }}
                autoPlay
                playsInline
                muted
            />

            <div className="mt-2 md:mt-8 text-center text-gray-600 text-[10px] md:text-xs">
                Mode Kiosque Sécurisé v2.11.0
            </div>
        </div >
    );
};

export default PinPanel;
