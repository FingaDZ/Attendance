import React, { useEffect, useState, useRef } from 'react';
import api from '../api';
import { UserPlus, Trash2, User, Camera, X, Check, RefreshCw, Edit, Eye } from 'lucide-react';

const Employees = () => {
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);

    // Modals
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showViewModal, setShowViewModal] = useState(false);

    // Form State
    const [selectedEmpId, setSelectedEmpId] = useState(null);
    const [empName, setEmpName] = useState('');
    const [empDept, setEmpDept] = useState('');
    const [empPin, setEmpPin] = useState('');
    const [selectedFiles, setSelectedFiles] = useState([null, null, null, null, null, null]); // v1.6.5: 6 photos
    const [currentPhotoUrls, setCurrentPhotoUrls] = useState([null, null, null, null, null, null]); // v1.6.5
    const [currentPhotoStep, setCurrentPhotoStep] = useState(0); // 0-5 for photo 1-6 (v1.6.5)

    // Camera states
    const [showCamera, setShowCamera] = useState(false);
    const [stream, setStream] = useState(null);
    const [capturedImages, setCapturedImages] = useState([null, null, null, null, null, null]); // v1.6.5
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const overlayCanvasRef = useRef(null); // New overlay canvas
    const [faceDetected, setFaceDetected] = useState(false); // Validation state
    const [currentResults, setCurrentResults] = useState([]); // For landmarks

    const fetchEmployees = async () => {
        try {
            const response = await api.get('/employees/');
            setEmployees(response.data);
        } catch (err) {
            console.error("Failed to fetch employees", err);
            setEmployees([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchEmployees();
        return () => {
            stopCamera();
        };
    }, []);

    // Draw landmarks
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
    }, [currentResults]);

    const handleFileChange = (e, photoIndex) => {
        const newFiles = [...selectedFiles];
        newFiles[photoIndex] = e.target.files[0];
        setSelectedFiles(newFiles);
        const newCaptured = [...capturedImages];
        newCaptured[photoIndex] = null;
        setCapturedImages(newCaptured);
    };

    const startCamera = async (photoIndex = 0) => {
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
    };

    // Recognition Loop for Landmarks & Validation
    const startRecognitionLoop = () => {
        let isProcessing = false;
        const interval = setInterval(async () => {
            if (isProcessing) return;
            if (videoRef.current && canvasRef.current && !videoRef.current.paused && !videoRef.current.ended) {
                isProcessing = true;

                // Use a temporary canvas for capture to avoid messing with the main one? 
                // Actually we can reuse canvasRef but we need to be careful not to draw over it if it's used for display.
                // In this component, canvasRef is hidden (className="hidden"), so it's safe to use for processing.

                const context = canvasRef.current.getContext('2d');
                canvasRef.current.width = videoRef.current.videoWidth;
                canvasRef.current.height = videoRef.current.videoHeight;
                context.drawImage(videoRef.current, 0, 0);

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
        }, 500); // Check every 500ms

        // Store interval ID on the video element or a ref to clear it later?
        // Since we don't have a ref for the interval, we'll attach it to the videoRef.current for now or use a separate ref.
        // Better: use a ref.
        videoRef.current._recognitionInterval = interval;
    };

    const stopCamera = () => {
        if (videoRef.current && videoRef.current._recognitionInterval) {
            clearInterval(videoRef.current._recognitionInterval);
        }
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
        setFaceDetected(false);
        setCurrentResults([]);
    };

    const takePhoto = () => {
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
    };

    const retakePhoto = () => {
        const newCaptured = [...capturedImages];
        newCaptured[currentPhotoStep] = null;
        setCapturedImages(newCaptured);
    };
    onClick = {() => { setShowAddModal(false); setShowEditModal(false); resetForm(); }}
className = "px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
    >
    Cancel
                                    </button >
    <button
        type="submit"
        disabled={showAddModal && (!selectedFiles[0] || !selectedFiles[1] || !selectedFiles[2])}
        className={`px-4 py-2 rounded-lg text-white ${showAddModal && (!selectedFiles[0] || !selectedFiles[1] || !selectedFiles[2]) ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
    >
        {showAddModal ? 'Register' : 'Update'}
    </button>
                                </div >
                            </form >
                        ) : (
    // Camera UI
    <div className="flex flex-col items-center">
        <div className="mb-3 text-center">
            <p className="text-lg font-semibold text-gray-800">
                {currentPhotoStep === 0 && "Step 1: Far / Full Face"}
                {currentPhotoStep === 1 && "Step 2: Close / Black & White"}
                {currentPhotoStep === 2 && "Step 3: Close / High Precision"}
            </p>
            <p className="text-sm text-gray-500">
                {currentPhotoStep === 0 && "Position your entire face in the circle."}
                {currentPhotoStep === 1 && "Move closer. Photo will be Black & White."}
                {currentPhotoStep === 2 && "Move closer for high-detail color capture."}
            </p>
        </div>
        <div className="relative w-full bg-black rounded-lg overflow-hidden aspect-video mb-4">
            {!capturedImages[currentPhotoStep] ? (
                <>
                    <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        className={`w-full h-full object-contain ${currentPhotoStep === 1 ? 'grayscale' : ''}`}
                    />
                    <canvas
                        ref={overlayCanvasRef}
                        className="absolute inset-0 w-full h-full pointer-events-none"
                    />
                    <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                        <svg viewBox="0 0 100 100" className="w-full h-full">
                            <ellipse
                                cx="50"
                                cy="50"
                                rx={currentPhotoStep === 0 ? "21" : "28"}
                                ry={currentPhotoStep === 0 ? "28" : "38"}
                                fill="none"
                                stroke={faceDetected ? "#00FF00" : "white"}
                                strokeWidth="0.5"
                                strokeDasharray="2,1"
                                opacity="0.7"
                            />
                        </svg>
                    </div>
                </>
            ) : (
                <img src={capturedImages[currentPhotoStep]} alt="Captured" className="w-full h-full object-contain" />
            )}
            <canvas ref={canvasRef} width="640" height="480" className="hidden" />
        </div>
        <div className="flex gap-4 w-full">
            {!capturedImages[currentPhotoStep] ? (
                <>
                    <button onClick={cancelCamera} className="flex-1 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg border border-gray-300">Cancel</button>
                    <button
                        onClick={takePhoto}
                        disabled={!faceDetected}
                        className={`flex-1 px-4 py-2 text-white rounded-lg flex items-center justify-center ${faceDetected ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}`}
                    >
                        <Camera className="w-5 h-5 mr-2" />
                        {faceDetected ? 'Capture' : 'No Face Detected'}
                    </button>
                </>
            ) : (
                <>
                    <button onClick={retakePhoto} className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center justify-center"><RefreshCw className="w-5 h-5 mr-2" /> Retake</button>
                    <button onClick={confirmPhoto} className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center"><Check className="w-5 h-5 mr-2" /> Use Photo</button>
                </>
            )}
        </div>
    </div>
)}
                    </div >
                </div >
            )}

{/* View Details Modal */ }
{
    showViewModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 w-full max-w-sm">
                <div className="flex justify-between items-start mb-4">
                    <h2 className="text-xl font-bold">Employee Details</h2>
                    <button onClick={() => setShowViewModal(false)} className="text-gray-400 hover:text-gray-600">
                        <X size={20} />
                    </button>
                </div>

                <div className="flex flex-col items-center mb-6">
                    <div className="grid grid-cols-3 gap-2 mb-4 w-full">
                        {[0, 1, 2].map((photoIndex) => (
                            <div key={photoIndex} className="relative">
                                <div className="w-full h-24 bg-gray-100 rounded-lg overflow-hidden border-2 border-gray-300">
                                    <img
                                        src={currentPhotoUrls[photoIndex]}
                                        onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }}
                                        className="w-full h-full object-cover"
                                        alt={`${empName} - Photo ${photoIndex + 1}`}
                                    />
                                    <div className="hidden w-full h-full items-center justify-center bg-gray-100 text-gray-400">
                                        <User size={24} />
                                    </div>
                                </div>
                                <p className="text-xs text-center mt-1 text-gray-500">Photo {photoIndex + 1}</p>
                            </div>
                        ))}
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800">{empName}</h3>
                    <p className="text-gray-500">{empDept || 'No Position'}</p>
                </div>

                <div className="space-y-3 border-t border-gray-100 pt-4">
                    <div className="flex justify-between">
                        <span className="text-gray-500">ID</span>
                        <span className="font-medium">{selectedEmpId}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-gray-500">PIN Code</span>
                        <span className="font-medium">{empPin ? '****' : 'Not Set'}</span>
                    </div>
                </div>

                <div className="mt-6">
                    <button
                        onClick={() => setShowViewModal(false)}
                        className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    )
}
{/* Processing Overlay */ }
{
    processing && (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex flex-col items-center justify-center z-[60]">
            <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500 mb-4"></div>
            <h3 className="text-white text-xl font-semibold">Processing...</h3>
            <p className="text-gray-300">Analyzing face and generating embeddings.</p>
        </div>
    )
}
        </div >
    );
};

export default Employees;
