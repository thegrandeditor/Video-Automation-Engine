import os
import subprocess
import shutil

# Handle MoviePy 1.x vs 2.x import structure differences
try:
    # Modern MoviePy 2.x way
    from moviepy import VideoFileClip, concatenate_videoclips
except ImportError:
    try:
        # Legacy MoviePy 1.x way
        from moviepy.editor import VideoFileClip, concatenate_videoclips
    except ImportError:
        print("Error: moviepy is not installed correctly. Please run: py -m pip install moviepy")
        import sys
        sys.exit(1)

ASSETS_DIR = 'raw_assets'
OUTPUTS_DIR = 'outputs'
TEMP_DIR = os.path.join(OUTPUTS_DIR, 'temp')

def gather_clips(target_duration_sec=600):
    """Scans raw_assets for video files and selects them until target duration is reached."""
    if not os.path.exists(ASSETS_DIR):
        print(f"Error: Directory '{ASSETS_DIR}' not found. Please download videos first.")
        return []

    files = [f for f in os.listdir(ASSETS_DIR) if f.endswith('.mp4')]
    selected_files = []
    total_duration = 0.0

    print(f"Scanning '{ASSETS_DIR}' for valid .mp4 clips...")
    for file in files:
        filepath = os.path.join(ASSETS_DIR, file)
        try:
            with VideoFileClip(filepath) as clip:
                duration = clip.duration
                
            selected_files.append(filepath)
            total_duration += duration
            print(f"Selected: {file} ({duration:.2f}s) | Total Time: {total_duration:.2f}s / {target_duration_sec}s")
            
            if total_duration >= target_duration_sec:
                print("Target duration reached!")
                break
        except Exception as e:
            print(f"Skipping {file} due to read error: {e}")

    return selected_files

def process_clip_ffmpeg(input_path, output_path):
    """Uses raw FFmpeg to powerfully and quickly create a 1920x1080 video with a blurred background."""
    print(f"Applying FFmpeg blur and 16:9 1080p layout to {os.path.basename(input_path)}...")
    
    # 1. Scale background to 1920x1080 covering the screen, then boxblur
    # 2. Scale foreground to fit within 1920x1080 keeping aspect ratio
    # 3. Overlay foreground precisely onto the background
    filter_complex = (
        "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=25:25[bg];"
        "[0:v]scale=1920:1080:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
    )
    
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "0:a?", 
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", # Force exactly 30fps across all clips to ensure smooth appending
        output_path
    ]
    
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed for {input_path}")
        raise e
        
    return output_path

def create_compilation():
    if not os.path.exists(OUTPUTS_DIR):
        os.makedirs(OUTPUTS_DIR)
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        
    clips_to_use = gather_clips(target_duration_sec=600)
    if not clips_to_use:
        print("No valid clips found to orchestrate.")
        return
        
    processed_files = []
    print("\n--- Phase 1: FFmpeg 16:9 Blur Processing ---")
    for i, filepath in enumerate(clips_to_use):
        out_name = f"processed_{i}.mp4"
        out_path = os.path.join(TEMP_DIR, out_name)
        process_clip_ffmpeg(filepath, out_path)
        processed_files.append(out_path)
        
    print(f"\n--- Phase 2: MoviePy Assembly & Crossfades ---")
    
    video_clips = []
    for i, filepath in enumerate(processed_files):
        try:
            clip = VideoFileClip(filepath)
            
            if i > 0:
                # Add a 1.0 second crossfade (graceful fade transition from previous clip)
                clip = clip.crossfadein(1.0)
            
            video_clips.append(clip)
        except Exception as e:
            print(f"Could not load processed clip {filepath}: {e}")
            
    if not video_clips:
        print("No valid processed clips to combine!")
        return

    # padding=-1 tells MoviePy to safely overlap the clips by 1 second for the crossfade
    final_video = concatenate_videoclips(video_clips, padding=-1, method="compose")
    
    final_out_path = os.path.join(OUTPUTS_DIR, "final_compilation.mp4")
    print(f"\n--- Phase 3: Rendering Final Compilation to {final_out_path} ---")
    final_video.write_videofile(
        final_out_path, 
        fps=30, 
        codec="libx264", 
        audio_codec="aac"
    )
    
    # Cleanup memory and temporary directory
    print("\nCleaning up temporary files...")
    for clip in video_clips:
        clip.close()
    final_video.close()
    
    try:
        shutil.rmtree(TEMP_DIR)
    except OSError:
        pass
    
    print("\n✅ --- Orchestration Complete! Compilation is ready in /outputs! ---")

if __name__ == "__main__":
    create_compilation()
