import os
import subprocess
import re
import whisper

DEFAULT_KEYWORDS = ["scam", "violence", "hate", "profanity"]

def detect_silence(video_path, noise_db="-40dB", min_duration=2.0):
    """
    Uses ffmpeg to detect periods of dead air (silence).
    Returns a list of tuples (start_time, end_time).
    """
    command = [
        "ffmpeg", "-i", video_path,
        "-af", f"silencedetect=noise={noise_db}:d={min_duration}",
        "-f", "null", "-"
    ]
    try:
        # ffmpeg outputs silencedetect logs to stderr
        result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, check=True)
        stderr_output = result.stderr
        
        silences = []
        start_pattern = re.compile(r"silence_start: (\d+(\.\d+)?)")
        end_pattern = re.compile(r"silence_end: (\d+(\.\d+)?) \| silence_duration: (\d+(\.\d+)?)")
        
        starts = start_pattern.finditer(stderr_output)
        ends = end_pattern.finditer(stderr_output)
        
        for start_match, end_match in zip(starts, ends):
            start_time = float(start_match.group(1))
            end_time = float(end_match.group(1))
            silences.append((start_time, end_time))
            
        return silences
    except Exception as e:
        print(f"Error detecting silence for {video_path}. Is ffmpeg installed? Error: {e}")
        return []

def transcribe_and_filter(video_path, model_name="base", keywords=None):
    """
    Transcribes video using strict local whisper and flags keywords with timestamps.
    Returns full transcript string and a list of flagged occurrences.
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS
        
    print(f"Loading local Whisper model '{model_name}' (this downloads it once if not present)...")
    # load_model natively falls back to CPU or GPU automatically
    model = whisper.load_model(model_name)
    
    print(f"Transcribing '{os.path.basename(video_path)}' entirely offline...")
    result = model.transcribe(video_path)
    
    flagged_instances = []
    full_text = result["text"]
    
    for segment in result["segments"]:
        text = segment["text"].lower()
        start = segment["start"]
        end = segment["end"]
        
        for kw in keywords:
            if kw.lower() in text:
                flagged_instances.append({
                    "keyword": kw,
                    "start": start,
                    "end": end,
                    "text": segment["text"].strip()
                })
                
    return full_text, flagged_instances

def analyze_video(video_path):
    """Main generic hook to run all analysis on a single video file."""
    print(f"\n--- Starting Content Analysis for {video_path} ---")
    
    # 1. Dead Air / Silence Detection
    print("Detecting dead air...")
    silences = detect_silence(video_path)
    if silences:
        print(f"Found {len(silences)} segments of dead air:")
        for s, e in silences:
            print(f"  - {s:.2f}s to {e:.2f}s (duration: {e-s:.2f}s)")
    else:
        print("No dead air detected.")
        
    # 2. Transcription & Content Filtering
    transcript, flagged = transcribe_and_filter(video_path)
    if flagged:
        print(f"Found {len(flagged)} flagged keyword occurrences:")
        for idx, instance in enumerate(flagged, 1):
            print(f"  {idx}. Keyword '{instance['keyword']}' at {instance['start']:.2f}s - {instance['end']:.2f}s : \"{instance['text']}\"")
    else:
        print("No flagged keywords detected in the transcript.")
        
    print("--- Analysis Complete ---\n")
    
    return {
        "silences": silences,
        "transcript": transcript,
        "flagged": flagged
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        vid_path = sys.argv[1]
        if os.path.exists(vid_path):
            analyze_video(vid_path)
        else:
            print(f"File not found: {vid_path}")
    else:
        print("Usage: python analyzer.py <path_to_video>")
