import React, { useState, useEffect } from 'react';
import { Delete, Check, AlertTriangle, User } from 'lucide-react';
import api from '../api';
import { parseAttendanceResponse } from '../utils/attendanceUtils';

const PinPanel = ({ onAuthSuccess }) => {
    const [pin, setPin] = useState('');
    const [empId, setEmpId] = useState('');
    const [step, setStep] = useState('ID'); // 'ID' or 'PIN'
    const [status, setStatus] = useState('idle'); // idle, loading, success, error, blocked
    const [feedback, setFeedback] = useState(null); // { reason, subtext, color }

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

    const handleEnter = async () => {
        if (step === 'ID') {
            if (empId.length > 0) setStep('PIN');
        } else {
            if (pin.length > 0) {
                await submitPin();
            }
        }
    };

    const submitPin = async () => {
        setStatus('loading');
        try {
            const formData = new FormData();
            formData.append('pin', pin);

            // Note: The backend endpoint for PIN auth is /verify_pin/ (based on api.py analysis)
            // Or we might need to check how it's implemented. 
            // Let's assume /verify_pin/ exists or use the logic from Dashboard.
            // Dashboard uses: api.post('/verify_pin/', formData)

            const response = await api.post(`/verify_pin/${empId}`, formData);
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
            } else {
                // Should not happen with parseAttendanceResponse for verified/blocked
                // But handles unexpected cases
                setStatus('error');
                setFeedback({ reason: 'Erreur', subtext: 'Réponse inattendue', color: '#EF4444' });
            }

        } catch (err) {
            console.error("PIN Auth Error:", err);
            setStatus('error');
            const msg = err.response?.data?.detail || "Erreur de connexion";

            if (msg === "Invalid PIN") {
                setFeedback({ reason: 'PIN Incorrect', subtext: 'Veuillez réessayer', color: '#EF4444' });
            } else if (msg === "Employee not found") {
                setFeedback({ reason: 'ID Inconnu', subtext: 'Employé non trouvé', color: '#EF4444' });
            } else {
                setFeedback({ reason: 'Erreur', subtext: msg, color: '#EF4444' });
            }
        }
    };

    // Render Logic
    const isBlocked = status === 'blocked';
    const isSuccess = status === 'success';
    const isError = status === 'error';

    return (
        <div className="flex flex-col h-full bg-gray-900 text-white p-6 shadow-2xl">
            {/* Header / Display Area */}
            <div className="flex-1 flex flex-col justify-center items-center mb-6 min-h-[160px]">
                {status === 'idle' || status === 'loading' ? (
                    <>
                        <h2 className="text-gray-400 text-sm uppercase tracking-wider mb-2">
                            {step === 'ID' ? 'Entrez votre ID' : 'Entrez votre PIN'}
                        </h2>
                        <div className="text-4xl font-mono font-bold tracking-widest text-white border-b-2 border-blue-500 pb-2 px-4 min-w-[120px] text-center">
                            {step === 'ID' ? (empId || '_') : (pin.replace(/./g, '•') || '_')}
                        </div>
                        {status === 'loading' && <div className="mt-4 text-blue-400 animate-pulse">Vérification...</div>}
                    </>
                ) : (
                    <div
                        className={`flex flex-col items-center justify-center p-6 rounded-xl w-full animate-in fade-in zoom-in duration-300`}
                        style={{ backgroundColor: feedback?.color }}
                    >
                        {isSuccess ? <User className="w-12 h-12 mb-2" /> : <AlertTriangle className="w-12 h-12 mb-2" />}
                        <h3 className="text-xl font-bold text-center leading-tight">{feedback?.reason}</h3>
                        <p className="text-sm opacity-90 mt-1 text-center">{feedback?.subtext}</p>
                    </div>
                )}
            </div>

            {/* Numpad */}
            <div className="grid grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
                    <button
                        key={num}
                        onClick={() => handleNumberClick(num.toString())}
                        className="h-16 bg-gray-800 rounded-xl text-2xl font-semibold hover:bg-gray-700 active:bg-gray-600 transition-colors shadow-lg border-b-4 border-gray-950 active:border-b-0 active:translate-y-1"
                    >
                        {num}
                    </button>
                ))}
                <button
                    onClick={handleClear}
                    className="h-16 bg-red-900/30 text-red-400 rounded-xl flex items-center justify-center hover:bg-red-900/50 transition-colors"
                >
                    <Delete className="w-6 h-6" />
                </button>
                <button
                    onClick={() => handleNumberClick('0')}
                    className="h-16 bg-gray-800 rounded-xl text-2xl font-semibold hover:bg-gray-700 active:bg-gray-600 transition-colors shadow-lg border-b-4 border-gray-950 active:border-b-0 active:translate-y-1"
                >
                    0
                </button>
                <button
                    onClick={handleEnter}
                    className="h-16 bg-blue-600 text-white rounded-xl flex items-center justify-center hover:bg-blue-500 active:bg-blue-700 transition-colors shadow-lg border-b-4 border-blue-800 active:border-b-0 active:translate-y-1"
                >
                    <Check className="w-8 h-8" />
                </button>
            </div>

            <div className="mt-8 text-center text-gray-600 text-xs">
                Mode Kiosque Sécurisé v2.1.0
            </div>
        </div>
    );
};

export default PinPanel;
