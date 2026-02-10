import os
import uuid
from moviepy import VideoFileClip, vfx
from schemas import VideoFormat, Dimensions

def process_video_clips(video_path: str, timestamps, output_format: VideoFormat, custom_dims: Dimensions = None, export_audio: bool = False):
    """
    Processes a video file into multiple clips based on timestamps and format.
    If export_audio is True, also saves the original audio track of each clip.
    """
    clip_paths = []
    audio_paths = []
    
    # Target aspect ratios
    ratios = {
        VideoFormat.SHORTS: 9/16,
        VideoFormat.VIDEO: 16/9,
        VideoFormat.SQUARE: 1/1,
        VideoFormat.CINEMA: 21/9,
        VideoFormat.FILM: 2.35/1
    }

    try:
        # Load background music if provided
        bg_music = None
        if custom_dims and hasattr(custom_dims, 'audio_path') and custom_dims.audio_path:
             from moviepy import AudioFileClip, CompositeAudioClip
             import moviepy.audio.fx as afx
             if os.path.exists(custom_dims.audio_path):
                 bg_music = AudioFileClip(custom_dims.audio_path)

        for ts in timestamps:
            # Open fresh instance for each clip to avoid handle sharing issues on Windows
            with VideoFileClip(video_path) as video:
                print(f"DEBUG: Processing clip. Video Duration: {video.duration}, Request: Start={ts.start_time}, End={ts.end_time}")
                
                # Basic validation
                if ts.start_time >= video.duration: 
                    print(f"DEBUG: Skipping clip. Start time {ts.start_time} is beyond video duration {video.duration}.")
                    continue
                end = min(ts.end_time, video.duration)
                print(f"DEBUG: Extracting subclip from {ts.start_time} to {end}")
                
                # Extract subclip
                subclip = video.subclipped(ts.start_time, end)

                # Generate unique ID for this clip operation
                clip_id = uuid.uuid4().hex[:8]
                output_filename = f"clip_{clip_id}.mp4"
                output_path = os.path.join(os.path.dirname(video_path), output_filename)

                # 1. Export Clean Audio (Transcript Source) if requested
                # We do this BEFORE any mixing or effects
                if export_audio and subclip.audio:
                    audio_filename = f"clip_{clip_id}.mp3"
                    audio_output_path = os.path.join(os.path.dirname(video_path), audio_filename)
                    subclip.audio.write_audiofile(
                        audio_output_path,
                        logger=None
                    )
                    audio_paths.append(audio_output_path)
                elif export_audio:
                    audio_paths.append(None) # Keep index sync if no audio
                
                # Apply background music if available
                if bg_music:
                    # Get audio options from custom_dims or defaults
                    loop = True
                    music_vol = 0.2
                    video_vol = 1.0
                    
                    if custom_dims:
                         if hasattr(custom_dims, 'loop_music'): loop = custom_dims.loop_music
                         if hasattr(custom_dims, 'music_volume'): music_vol = custom_dims.music_volume
                         if hasattr(custom_dims, 'video_volume'): video_vol = custom_dims.video_volume

                    # Logic to loop or trim music
                    if loop and bg_music.duration < subclip.duration:
                        # NEW MOVIEPY V2 SYNTAX
                        music_clip = bg_music.with_effects([afx.AudioLoop(duration=subclip.duration)])
                    else:
                        music_clip = bg_music.subclipped(0, min(bg_music.duration, subclip.duration))
                    
                    # Set volumes
                    music_clip = music_clip.with_volume_scaled(music_vol)
                    
                    # Mix with original audio
                    if subclip.audio:
                         original_audio = subclip.audio.with_volume_scaled(video_vol)
                         subclip = subclip.with_audio(CompositeAudioClip([original_audio, music_clip]))
                    else:
                         subclip = subclip.with_audio(music_clip)

                # Apply formatting
                if output_format == VideoFormat.ORIGINAL:
                    pass # Skip resizing, keep original dimensions
                elif output_format != VideoFormat.CUSTOM:
                    target_ratio = ratios.get(output_format, 16/9)
                    subclip = format_clip(subclip, target_ratio)
                elif custom_dims:
                    if hasattr(custom_dims, 'width') and hasattr(custom_dims, 'height'):
                        subclip = subclip.resized(width=custom_dims.width, height=custom_dims.height)
                
                # Write file
                subclip.write_videofile(
                    output_path, 
                    codec="libx264", 
                    audio_codec="aac",
                    temp_audiofile=f"temp-audio-{clip_id}.m4a",
                    remove_temp=True,
                    fps=24,
                    threads=4,
                    preset="ultrafast",   # Significant speedup
                    logger=None
                )
                
                # Explicitly close everything
                if subclip.audio: subclip.audio.close()
                subclip.close()
                if bg_music:
                    # We don't close bg_music here as it's reused, but we should close the loop/trim versions if possible
                    # MoviePy v2 handles composition cleanly usually
                    pass
                clip_paths.append(output_path)
        
        if bg_music: bg_music.close()
        return clip_paths, audio_paths

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

def create_zip_archive(file_paths: list, output_filename: str):
    """
    Creates a ZIP archive containing the specified files.
    """
    import zipfile
    
    # Filter out None values
    file_paths = [f for f in file_paths if f and os.path.exists(f)]
    
    if not file_paths:
        return None

    zip_path = os.path.join(os.path.dirname(file_paths[0]), output_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in file_paths:
            zipf.write(file, os.path.basename(file))
                
    return zip_path
