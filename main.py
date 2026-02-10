import ffmpeg_init
from fastapi import FastAPI
import uvicorn
from routers import video, files

app = FastAPI(title="Video Clipping API")

# Include Routers
app.include_router(video.router)
app.include_router(files.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
