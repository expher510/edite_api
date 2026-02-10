import ffmpeg_init
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import shutil
import os
import uvicorn
from schemas import ClipRequest, VideoFormat, Timestamp
from video_processor import process_video_clips
import json
from typing import List

app = FastAPI(title="Video Clipping API")

UPLOAD_DIR = "temp_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process")
async def process_video(
    video: UploadFile = File(...),
    format: VideoFormat = Form(VideoFormat.FILM, description="Select the output video format"),
    background_music: UploadFile = File(None, description="Upload an audio file for background music"),
    music_url: str = Form(None, description="URL of an audio file for background music"),
    video_volume: float = Form(1.0, description="Volume of original video (0.0 to 1.0+)"),
    music_volume: float = Form(0.2, description="Volume of background music (0.0 to 1.0+)"),
    loop_music: bool = Form(True, description="Loop background music if shorter than video"),
    timestamps_json: str = Form(
        ..., 
        alias="timestamps",
        description='JSON list of timestamps, e.g. [{"start_time": 0, "end_time": 10}]'
    )
):
    temp_path = None
    audio_path = None
    try:
        # Parse timestamps
        try:
            timestamps_data = json.loads(timestamps_json)
            if not isinstance(timestamps_data, list):
                raise ValueError("Timestamps must be a list")
            timestamps = [Timestamp(**ts) for ts in timestamps_data]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid timestamps format: {str(e)}")
        
        if not timestamps:
            raise HTTPException(status_code=400, detail="At least one timestamp is required")

        # Save uploaded video
        temp_path = os.path.join(UPLOAD_DIR, video.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # Handle Background Music
        if background_music:
            audio_path = os.path.join(UPLOAD_DIR, f"bg_music_{background_music.filename}")
            with open(audio_path, "wb") as buffer:
                shutil.copyfileobj(background_music.file, buffer)
        elif music_url:
            # Download audio from URL
            import requests
            try:
                response = requests.get(music_url, stream=True)
                response.raise_for_status()
                audio_filename = f"bg_music_url_{abs(hash(music_url))}.mp3"
                audio_path = os.path.join(UPLOAD_DIR, audio_filename)
                with open(audio_path, "wb") as buffer:
                    for chunk in response.iter_content(chunk_size=8192):
                        buffer.write(chunk)
            except Exception as e:
                print(f"Failed to download music: {e}")
                # We continue without music if download fails, or you could raise HTTPException
        
        # Prepare dimensions object to pass audio path and options
        from schemas import Dimensions
        dims = Dimensions(
            width=0, 
            height=0, 
            audio_path=audio_path,
            video_volume=video_volume,
            music_volume=music_volume,
            loop_music=loop_music
        )

        # Process clips
        try:
            clip_paths = process_video_clips(temp_path, timestamps, format, custom_dims=dims)
        finally:
             pass
        
        safe_remove(temp_path)
        if audio_path: safe_remove(audio_path)

        return {
            "message": "Clips processed successfully",
            "format_applied": format,
            "clips": [os.path.basename(p) for p in clip_paths],
            "full_paths": clip_paths
        }

    except Exception as e:
        if temp_path:
            safe_remove(temp_path)
        if isinstance(e, HTTPException):
            raise e
        return JSONResponse(status_code=500, content={"error": str(e)})

def safe_remove(path: str, max_retries: int = 3):
    """Attempt to remove a file with retries for Windows file locking."""
    import time
    for i in range(max_retries):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except PermissionError:
            time.sleep(1) # Wait for handles to clear
    print(f"Warning: Could not delete {path} after {max_retries} attempts.")

@app.get("/get-clip/{filename}", summary="Download/Play Video Clip")
async def get_clip(filename: str):
    """
    Retrieves a processed video clip by its filename.
    Returns the file as a video/mp4 stream.
    """
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename=filename)
    raise HTTPException(status_code=404, detail="Clip not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
