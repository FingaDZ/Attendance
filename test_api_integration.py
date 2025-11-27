import requests
import os

# Path to a sample image provided by insightface
image_path = r"backend\venv\insightface\data\images\t1.jpg"

if not os.path.exists(image_path):
    print(f"Error: Image not found at {image_path}")
    # Try alternate path
    image_path = r"backend\venv\insightface\data\images\Tom_Hanks_54745.png"
    if not os.path.exists(image_path):
        print(f"Error: Alternate image not found at {image_path}")
        exit(1)

print(f"Testing API with image: {image_path}")

url = "http://localhost:8000/api/recognize/"
files = {'file': open(image_path, 'rb')}

try:
    response = requests.post(url, files=files)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ API Response Success:")
        print(f"Name: {data.get('name')}")
        print(f"Confidence: {data.get('confidence')}")
        print(f"Liveness Score: {data.get('liveness_score')}")
        print(f"Landmarks Count: {data.get('landmarks_count')}")
        
        # Verify landmarks count
        count = data.get('landmarks_count')
        if count == 468:
            print("✅ MediaPipe 468 landmarks detected!")
        elif count == 68:
            print("⚠️ InsightFace 68 landmarks detected (Fallback active)")
        elif count == 5:
            print("⚠️ InsightFace 5 landmarks detected (Fallback active)")
        else:
            print(f"⚠️ Unexpected landmark count: {count}")
            
    else:
        print(f"\n❌ API Error {response.status_code}:")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
    print("Make sure the backend server is running on port 8000")
