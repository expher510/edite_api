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
    # 2. Audio (5 seconds)
    if not os.path.exists("test_audio.mp3"):
        # Create a silent audio clip for testing if real one missing
        from moviepy import AudioClip
        import numpy as np
        make_frame = lambda t: np.sin(440 * 2 * np.pi * t)
        audio = AudioClip(make_frame, duration=5, fps=44100)
        audio.write_audiofile("test_audio.mp3", fps=44100, logger=None)

def test_music_upload():
    url = "http://localhost:8000/process"
    
    video_file = 'test_music_video.mp4'
    audio_file = 'test_audio.mp3' # Use generated audio

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
        'loop_music': True,
        'export_audio': True
    }

    print("\nTesting Background Music Upload...")
    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Response:", result)
            
            # Check for ZIP archive
            if "archive_url" in result:
                print(f"SUCCESS: Zip archive created! URL: {result['archive_url']}")
                # Validate filename
                if "archive_filename" in result and result['archive_filename'].endswith('.zip'):
                     print("SUCCESS: Filename is valid zip.")
            elif "clips" in result:
                 print("SUCCESS: JSON processed (No Zip requested or generated).")
            else:
                 print("FAILURE: Unexpected response structure.")

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
