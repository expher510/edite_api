from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class VideoFormat(str, Enum):
    SHORTS = "Shorts (9:16)"
    VIDEO = "Video (16:9)"
    SQUARE = "Square (1:1)"
    CINEMA = "Cinema (21:9)"
    FILM = "Film (2.35:1)"
    CUSTOM = "Custom"

class Timestamp(BaseModel):
    start_time: float
    end_time: float

class Dimensions(BaseModel):
    width: int
    height: int
    audio_path: Optional[str] = None
    video_volume: float = 1.0
    music_volume: float = 0.2
    loop_music: bool = True

class ClipRequest(BaseModel):
    video_url: Optional[str] = None
    format: VideoFormat = VideoFormat.FILM
    custom_dimensions: Optional[Dimensions] = None
    timestamps: List[Timestamp]
