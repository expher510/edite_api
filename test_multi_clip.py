
import requests
import time
import os
from moviepy import ColorClip

def create_long_video():
    print("Generating 20s video...")
    if not os.path.exists("long_video.mp4"):
        clip = ColorClip(size=(640, 480), color=(0, 0, 255), duration=20)
        clip.write_videofile("long_video.mp4", fps=24, logger=None)

def test_multi_clip():
    url = "http://localhost:8000/process"
    video_file = "long_video.mp4"
    
    if not os.path.exists(video_file):
        create_long_video()

    files = {
        'video': open(video_file, 'rb'),
    }
    
    # Requesting two clips: 0-5s and 10-15s
    # Providing webhook_url to trigger background processing logic causing the potential issue
    # But for local test without real webhook, we can omit it to test the sync path first, 
    # OR we can mock it. The user issue happens in webhook mode? 
    # The user used curl with webhook_url.
    # Let's test standard sync first to see if logic holds.
    
    data = {
        'format': 'Original (No Resize)',
        'timestamps': '[{"start_time": 0, "end_time": 5}, {"start_time": 10, "end_time": 15}]',
        'export_audio': True
    }

    print("\nTesting Multi-Clip Processing...")
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        files['video'].close()

if __name__ == "__main__":
    test_multi_clip()
