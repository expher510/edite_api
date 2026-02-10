---
title: Video Processing API
emoji: 🎬
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Video Processing API

A FastAPI-based video processing service that provides video clipping and audio extraction capabilities.

## Features

- **Video Clipping**: Extract specific segments from videos
- **Audio Extraction**: Extract audio tracks from video files
- **Multiple Format Support**: Support for various video and audio formats
- **RESTful API**: Easy-to-use HTTP endpoints

## API Endpoints

### Video Clipping
```
POST /video/clip
```
Clip a video segment between start and end times.

### Audio Extraction
```
POST /video/extract-audio
```
Extract audio from video files.

### File Upload
```
POST /files/upload
```
Upload video files for processing.

## Usage

1. Upload your video file using the `/files/upload` endpoint
2. Use the returned file path to process the video
3. Download the processed result

## Supported Formats

- **Video**: MP4, AVI, MOV, WebM
- **Audio**: MP3, WAV, AAC

## Technical Details

Built with:
- FastAPI for the web framework
- MoviePy for video processing
- FFmpeg for media handling
- Docker for containerization

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

The API will be available at `http://localhost:8000`