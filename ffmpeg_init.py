import os
import imageio_ffmpeg

def init_ffmpeg():
    """Ensure FFmpeg is configured before MoviePy imports."""
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["FFMPEG_BINARY"] = ffmpeg_exe
    # Also set for other potential lookups
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe
    return ffmpeg_exe

# Run initialization immediately when this module is imported
# This MUST happen before anything else imports moviepy
FFMPEG_PATH = init_ffmpeg()
