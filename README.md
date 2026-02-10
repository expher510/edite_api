# 🎬 Cliber - Video Clipping API

A powerful, high-performance FastAPI service designed to slice, dice, and format videos programmatically. Built with **FastAPI** and **MoviePy**, Cliber allows you to extract specific clips from a video and automatically format them for various platforms (YouTube Shorts, Instagram Reels, Cinema, etc.).

## ✨ Features

- **🚀 High Performance**: Built on FastAPI for speed and easy integration.
- **✂️ Smart Clipping**: Extract multiple clips in a single request using precise timestamps.
- **🎨 Auto-Formatting**: Intelligent cropping and resizing engine that supports:
  - `Shorts (9:16)` - Perfect for TikTok/Reels.
  - `Video (16:9)` - Standard HD format.
  - `Square (1:1)` - Ideal for Instagram posts.
  - `Cinema (21:9)` - Ultra-wide cinematic look.
  - `Film (2.35:1)` - Classic anamorphic format (Default).
- **🛡️ Windows Ready**: Robust file handling logic designed to work flawlessly on Windows without file locking issues.
- **🐳 Docker Ready**: Comes with standard `requirements.txt` for easy containerization.

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/cliber.git
   cd cliber
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   python main.py
   ```
   The API will start at `http://localhost:8000`.

## 📖 Usage

### Swager UI
Explore the API interactively at:
`http://localhost:8000/docs`

### Example Request (Python)
```python
import requests

url = "http://localhost:8000/process"
files = {'video': open('my_video.mp4', 'rb')}
data = {
    'format': 'Shorts (9:16)',
    'timestamps': '[{"start_time": 10, "end_time": 20}, {"start_time": 45, "end_time": 50}]'
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

## 🏗️ Project Structure

- `main.py`: The FastAPI application entry point.
- `video_processor.py`: Core logic for video manipulation using MoviePy.
- `ffmpeg_init.py`: Global FFmpeg initialization module for stability.
- `schemas.py`: Pydantic models for data validation.

## 📝 License

MIT License - feel free to use this in your own projects!
