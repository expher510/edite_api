import os
import uuid
from moviepy import VideoFileClip, vfx
from schemas import VideoFormat, Dimensions

def process_video_clips(video_path: str, timestamps, output_format: VideoFormat, custom_dims: Dimensions = None):
    """
    Processes a video file into multiple clips based on timestamps and format.
    """
    clip_paths = []
    
    # Target aspect ratios
    ratios = {
        VideoFormat.SHORTS: 9/16,
        VideoFormat.VIDEO: 16/9,
        VideoFormat.SQUARE: 1/1,
        VideoFormat.CINEMA: 21/9,
        VideoFormat.FILM: 2.35/1
    }

    try:
        for ts in timestamps:
            # Open fresh instance for each clip to avoid handle sharing issues on Windows
            with VideoFileClip(video_path) as video:
                # Basic validation
                if ts.start_time >= video.duration: continue
                end = min(ts.end_time, video.duration)
                
                # Extract subclip
                subclip = video.subclipped(ts.start_time, end)
                
                # Apply formatting
                if output_format != VideoFormat.CUSTOM:
                    target_ratio = ratios.get(output_format, 16/9)
                    subclip = format_clip(subclip, target_ratio)
                elif custom_dims:
                    subclip = subclip.resized(width=custom_dims.width, height=custom_dims.height)
                
                # Generate unique filename
                output_filename = f"clip_{uuid.uuid4().hex[:8]}.mp4"
                output_path = os.path.join(os.path.dirname(video_path), output_filename)
                
                # Write file
                subclip.write_videofile(
                    output_path, 
                    codec="libx264", 
                    audio_codec="aac",
                    temp_audiofile=f"temp-audio-{uuid.uuid4().hex[:8]}.m4a",
                    remove_temp=True,
                    fps=24,
                    threads=4,
                    logger=None
                )
                
                # Explicitly close everything
                if subclip.audio: subclip.audio.close()
                subclip.close()
                clip_paths.append(output_path)
            
        return clip_paths

    except Exception as e:
        print(f"Error processing video: {str(e)}")
        raise e

def format_clip(clip, target_ratio):
    """
    Crops and resizes a clip to a target aspect ratio.
    """
    w, h = clip.size
    current_ratio = w / h
    
    if current_ratio > target_ratio:
        # Source is wider than target, crop sides
        new_w = h * target_ratio
        subclip = clip.cropped(x_center=w/2, width=new_w)
    else:
        # Source is taller than target, crop top/bottom
        new_h = w / target_ratio
        subclip = clip.cropped(y_center=h/2, height=new_h)
        
    # Standardize resolutions for known formats
    if target_ratio == 9/16: # Shorts
        return subclip.resized(height=1920) if subclip.h < 1920 else subclip
    elif target_ratio == 16/9: # Standard
        return subclip.resized(width=1920) if subclip.w < 1920 else subclip
    elif target_ratio == 1/1: # Square
        return subclip.resized(width=1080) if subclip.w < 1080 else subclip
        
    return subclip
