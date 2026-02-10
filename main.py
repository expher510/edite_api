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
    timestamps_json: str = Form(
        ..., 
        alias="timestamps",
        description='JSON list of timestamps, e.g. [{"start_time": 0, "end_time": 10}]'
    )
):
    temp_path = None
    try:
        # Parse timestamps from JSON string
        try:
            timestamps_data = json.loads(timestamps_json)
            if not isinstance(timestamps_data, list):
                raise ValueError("Timestamps must be a list")
            timestamps = [Timestamp(**ts) for ts in timestamps_data]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid timestamps format: {str(e)}")
        
        if not timestamps:
            raise HTTPException(status_code=400, detail="At least one timestamp is required")

        # Save uploaded file
        temp_path = os.path.join(UPLOAD_DIR, video.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # Process clips
        try:
            clip_paths = process_video_clips(temp_path, timestamps, format)
        finally:
            # Cleanup source file safely
            pass
        
        safe_remove(temp_path)

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
