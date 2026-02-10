import requests
import os
import time
from moviepy import ColorClip, AudioClip
import numpy as np

def create_assets():
    print("Generating assets...")
    # 1. Video (5 seconds)
    if not os.path.exists("test_music_video.mp4"):
        clip = ColorClip(size=(640, 480), color=(0, 255, 0), duration=5)
        clip.write_videofile("test_music_video.mp4", fps=24, logger=None)

def test_music_upload():
    url = "http://localhost:8000/process"
    
    video_file = 'ChronoTrigger_456_part01_512kb.mp4'
    audio_file = 'kakaist-cinematic-hit-3-317170.mp3'

    if not os.path.exists(video_file):
        print(f"Error: Video file {video_file} not found!")
        return
    if not os.path.exists(audio_file):
        print(f"Error: Audio file {audio_file} not found!")
        return

    files = {
        'video': open(video_file, 'rb'),
        'background_music': open(audio_file, 'rb')
    }
    
    data = {
        'format': 'Original (No Resize)',
        'timestamps': '[{"start_time": 0, "end_time": 5}]',
        'video_volume': 0.5,
        'music_volume': 0.8,
        'loop_music': True
    }

    print("\nTesting Background Music Upload...")
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response:", result)
            clips = result.get("full_paths", [])
            if clips and os.path.exists(clips[0]):
                print("SUCCESS: Clip created with music!")
            else:
                print("FAILURE: Clip file missing.")
        else:
            print("FAILURE: API Error", response.text)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        files['video'].close()
        files['background_music'].close()

if __name__ == "__main__":
    # Wait for server to definitely be up
    time.sleep(2)
    create_assets()
    test_music_upload()
