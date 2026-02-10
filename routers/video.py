from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import shutil
import os
import json
import uuid
import requests
from schemas import VideoFormat, Timestamp, ClipRequest, Dimensions
from video_processor import process_video_clips, safe_remove, create_zip_archive

router = APIRouter()

UPLOAD_DIR = "temp_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def background_processing(
    task_id: str,
    temp_path: str, 
    timestamps: list, 
    format: VideoFormat, 
    dims: Dimensions, 
    export_audio: bool, 
    audio_path: str = None, 
    webhook_url: str = None,
    host_url: str = ""
):
    """
    Executes the video processing logic. 
    If webhook_url is provided, sends the result via POST.
    """
    response_data = {}
    files_to_cleanup = [temp_path]
    if audio_path: files_to_cleanup.append(audio_path)

    try:
        # Process clips
        clip_paths, audio_clip_paths = process_video_clips(temp_path, timestamps, format, custom_dims=dims, export_audio=export_audio)
        
        # Prepare result
        clips_filenames = [os.path.basename(p) for p in clip_paths]
        full_clip_paths = clip_paths

        if export_audio and not webhook_url:
            # Create ZIP ONLY if it's a direct synchronous request (User waiting in browser)
            # For Webhooks, we send individual links as requested
            all_files = clip_paths + [p for p in audio_clip_paths if p]
            zip_filename = f"clips_{task_id}.zip"
            zip_path = create_zip_archive(all_files, zip_filename)
            
            if zip_path:
                download_url = f"{host_url}get-clip/{os.path.basename(zip_path)}"
                response_data = {
                    "status": "success",
                    "task_id": task_id,
                    "message": "Processing complete",
                    "archive_url": download_url,
                    "archive_filename": os.path.basename(zip_path)
                }
            else:
                 response_data = {"status": "error", "message": "Failed to create zip archive"}
        else:
            # For Webhooks OR Normal JSON response without export_audio
            # We return the LIST of URLs so n8n can loop over them
            clip_urls = [f"{host_url}get-clip/{name}" for name in clips_filenames]
            
            audio_urls = []
            if export_audio:
                audio_urls = [f"{host_url}get-clip/{os.path.basename(p)}" if p else None for p in audio_clip_paths]

            response_data = {
                "status": "success",
                "task_id": task_id,
                "message": "Clips processed successfully",
                "clips_urls": clip_urls,
                "audio_urls": audio_urls
            }

        # Send Webhook if requested
        if webhook_url:
            try:
                requests.post(webhook_url, json=response_data)
            except Exception as e:
                print(f"Failed to send webhook: {e}")
        
        return response_data

    except Exception as e:
        error_data = {"status": "error", "task_id": task_id, "error": str(e)}
        if webhook_url:
            try:
                requests.post(webhook_url, json=error_data)
            except: pass
        if not webhook_url: raise e # Re-raise if synchronous

    finally:
        for f in files_to_cleanup:
            safe_remove(f)

@router.post("/process", tags=["Video Processing"])
async def process_video(
    request: Request,
    background_tasks: BackgroundTasks,
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
    ),
    export_audio: bool = Form(False, description="Export separate audio files for each clip (original audio). Returns a ZIP if True."),
    webhook_url: str = Form(None, description="Optional URL to receive processing results via POST.")
):
    task_id = uuid.uuid4().hex[:8]
    temp_path = None
    audio_path = None
    
    # Base URL for download links
    host_url = str(request.base_url)

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
        temp_path = os.path.join(UPLOAD_DIR, f"{task_id}_{video.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # Handle Background Music
        if background_music:
            audio_path = os.path.join(UPLOAD_DIR, f"bg_{task_id}_{background_music.filename}")
            with open(audio_path, "wb") as buffer:
                shutil.copyfileobj(background_music.file, buffer)
        elif music_url:
            # Download audio from URL
            try:
                response = requests.get(music_url, stream=True)
                response.raise_for_status()
                audio_filename = f"bg_url_{task_id}.mp3"
                audio_path = os.path.join(UPLOAD_DIR, audio_filename)
                with open(audio_path, "wb") as buffer:
                    for chunk in response.iter_content(chunk_size=8192):
                        buffer.write(chunk)
            except Exception as e:
                print(f"Failed to download music: {e}")
        
        # Prepare dimensions
        dims = Dimensions(
            width=0, 
            height=0, 
            audio_path=audio_path,
            video_volume=video_volume,
            music_volume=music_volume,
            loop_music=loop_music
        )

        # Dispatch
        if webhook_url:
            background_tasks.add_task(
                background_processing,
                task_id, temp_path, timestamps, format, dims, export_audio, audio_path, webhook_url, host_url
            )
            return {"status": "processing", "task_id": task_id, "message": "Processing started. Results will be sent to webhook."}
        else:
            # Synchronous execution
            return background_processing(
                task_id, temp_path, timestamps, format, dims, export_audio, audio_path, None, host_url
            )

    except Exception as e:
        if temp_path: safe_remove(temp_path)
        if audio_path: safe_remove(audio_path)
        if isinstance(e, HTTPException): raise e
        return JSONResponse(status_code=500, content={"error": str(e)})
