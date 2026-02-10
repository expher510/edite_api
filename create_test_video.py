from moviepy import ColorClip
import os

def create_test_video():
    # Create a 20-second red video clip
    clip = ColorClip(size=(640, 480), color=(255, 0, 0), duration=20)
    clip.write_videofile("test_input.mp4", fps=24)
    print("Created test_input.mp4")

if __name__ == "__main__":
    create_test_video()
