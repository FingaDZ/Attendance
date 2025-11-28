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

            <div className="mt-2 md:mt-8 text-center text-gray-600 text-[10px] md:text-xs">
                Mode Kiosque Sécurisé v2.1.0
            </div>
        </div>
    );
};

export default PinPanel;
