from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

UPLOAD_DIR = "temp_videos"

@router.get("/get-clip/{filename}", summary="Download/Play Video Clip", tags=["File Retrieval"])
async def get_clip(filename: str):
    """
    Retrieves a processed video clip, audio file, or zip by its filename.
    """
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        media_type = "application/octet-stream"
        if filename.endswith(".mp4"):
            media_type = "video/mp4"
        elif filename.endswith(".mp3"):
            media_type = "audio/mpeg"
        elif filename.endswith(".zip"):
            media_type = "application/zip"
            
        return FileResponse(path, media_type=media_type, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")
