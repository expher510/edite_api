from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

UPLOAD_DIR = "temp_videos"

@router.get("/get-clip/{filename}", summary="Download/Play Video Clip", tags=["File Retrieval"])
async def get_clip(filename: str):
    """
    Retrieves a processed video clip by its filename.
    Returns the file as a video/mp4 stream.
    """
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        return FileResponse(path, media_type="video/mp4", filename=filename)
    raise HTTPException(status_code=404, detail="Clip not found")
