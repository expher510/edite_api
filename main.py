import ffmpeg_init
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers import video, files

app = FastAPI(title="Video Clipping API")

# Add CORS middleware for Hugging Face Spaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(video.router)
app.include_router(files.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
