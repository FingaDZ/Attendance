#!/usr/bin/env python3
"""
Script to fix the corrupted camera UI section in Employees.jsx
"""

def fix_camera_ui():
    filepath = r"f:\Code\attendance\frontend\src\pages\Employees.jsx"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the corrupted section (around line 728-750)
    # We need to replace from the camera container div to the canvas
    
    corrupted_start_pattern = "                                <div className=\"relative w-full bg-black rounded-lg overflow-hidden aspect-video mb-4\">\r\n"
    
    # Find the start index
    start_idx = None
    for i, line in enumerate(lines):
        if line == corrupted_start_pattern:
            start_idx = i
            break
    
    if start_idx is None:
        print("❌ Could not find corrupted section")
        return
    
    # Find the end (the canvas line)
    end_idx = None
    for i in range(start_idx, min(start_idx + 30, len(lines))):
        if "<canvas ref={canvasRef}" in lines[i]:
            end_idx = i + 1  # Include the canvas line and the closing div after it
            break
    
    if end_idx is None:
        print("❌ Could not find end of corrupted section")
        return
    
    print(f"Found corrupted section from line {start_idx+1} to {end_idx+1}")
    
    # The correct replacement
    correct_ui = """                                <div className="relative w-full bg-black rounded-lg overflow-hidden aspect-video mb-4">
                                    {!capturedImages[currentPhotoStep] ? (
                                        <>
                                            {selectedCamera?.source === '0' ? (
                                                <video
                                                    ref={videoRef}
                                                    autoPlay
                                                    playsInline
                                                    className={`w-full h-full object-contain ${currentPhotoStep === 1 ? 'grayscale' : ''}`}
                                                />
                                            ) : (
                                                <img
                                                    ref={imgRef}
                                                    src={`/api/stream/${selectedCamera?.id}/clean`}
                                                    className={`w-full h-full object-contain ${currentPhotoStep === 1 ? 'grayscale' : ''}`}
                                                    alt="RTSP Stream"
                                                    crossOrigin="anonymous"
                                                />
                                            )}
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
"""
    
    # Replace the corrupted section
    new_lines = lines[:start_idx] + [correct_ui] + lines[end_idx:]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Fixed camera UI section")

if __name__ == "__main__":
    fix_camera_ui()
