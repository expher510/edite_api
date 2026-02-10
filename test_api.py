import requests
import json
import os

def test_clipping():
    url = "http://localhost:8000/process"
    
    # Check if a video file exists in the current directory for testing
    # If not, we'll suggest the user to provide one or I'll try to find one.
    video_files = [f for f in os.listdir('.') if f.endswith(('.mp4', '.mov', '.avi'))]
    
    if not video_files:
        print("No video file found for testing. Please place an mp4 file in the directory.")
        return

    test_video = video_files[0]
    print(f"Testing with: {test_video}")

    payload = {
        "format": "shorts",
        "timestamps": [
            {"start_time": 0, "end_time": 5},
            {"start_time": 10, "end_time": 15}
        ]
    }

    files = [
        ('video', (test_video, open(test_video, 'rb'), 'video/mp4')),
        ('request_data', (None, json.dumps(payload)))
    ]

    try:
        response = requests.post(url, files=files)
        print("Status Code:", response.status_code)
        print("Response:", response.json())
        
        if response.status_code == 200:
            clips = response.json().get("clips", [])
            for clip in clips:
                print(f"Generated clip: {clip}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Note: Server must be running first!
    test_clipping()
