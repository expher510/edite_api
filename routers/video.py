from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
import json
import uuid
from schemas import VideoFormat, Timestamp, ClipRequest, Dimensions
from video_processor import process_video_clips, safe_remove

router = APIRouter()

UPLOAD_DIR = "temp_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/process", tags=["Video Processing"])
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
        description='JSON list of timestamps. Recommended duration for weak devices: < 60 seconds per clip.'
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

# Future Implementation:
# @router.post("/extract-audio", tags=["Audio Extraction"])
# async def extract_audio_track(...):
#     ... logic to extract audio without touching video ...
