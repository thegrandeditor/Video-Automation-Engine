import yt_dlp
import os
import sys
import database
import analyzer

ASSETS_DIR = 'raw_assets'

def download_videos(urls):
    """Downloads videos using yt-dlp and logs metadata to SQLite."""
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
        
    # Ensure database is initialized
    database.init_db()
        
    ydl_opts = {
        'outtmpl': os.path.join(ASSETS_DIR, '%(id)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'nopart': True,
        'continuedl': False,
        'socket_timeout': 60,
        'retries': 3,
        'fragment_retries': 3,
        'quiet': False,
        'no_warnings': True,
        # 'cookiesfrombrowser': ('edge',), # Uncomment if you still get 403s or JS challenge freezes
    }
    
    # Moving the yt-dlp instance inside the loop allows Python to garbage 
    # collect the heavy JS interpreter memory after every single video.
    for url in urls:
        if 'tiktok.com' in url and '/photo/' in url:
            url = url.replace('/photo/', '/video/')
            
        print(f"Processing URL: {url}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info dict without downloading first to get metadata
                info_dict = ydl.extract_info(url, download=True)
                
                title = info_dict.get('title', 'Unknown Title')
                creator = info_dict.get('uploader', info_dict.get('channel', 'Unknown Creator'))
                duration = info_dict.get('duration', 0)
                
                # Log metadata to the database
                database.log_video(title, creator, duration, url)
                print(f"Successfully downloaded and logged: {title} by {creator}")
                
                # ---- AI Content Analysis Hook (Purely Local) ----
                filepath = ydl.prepare_filename(info_dict)
                if os.path.exists(filepath):
                    print("Queuing video for purely local offline AI analysis...")
                    try:
                        analysis_result = analyzer.analyze_video(filepath)
                        database.log_analysis(
                            video_url=url, 
                            transcript=analysis_result["transcript"], 
                            flagged_data=analysis_result["flagged"], 
                            dead_air_data=analysis_result["silences"]
                        )
                        print("AI Analysis logged to database successfully.")
                    except Exception as eval_e:
                        print(f"Offline Content Analysis failed for {filepath}: {eval_e}")
                else:
                    print(f"File {filepath} not found for analysis.")
                
        except Exception as e:
            print(f"Failed to process {url}: {e}")

if __name__ == '__main__':
    # You can pass URLs as command line arguments
    if len(sys.argv) > 1:
        # Use a list comprehension to avoid strict IDE type checking errors with slice objects
        urls_to_download = [sys.argv[i] for i in range(1, len(sys.argv))]
        download_videos(urls_to_download)
    else:
        print("Usage: python downloader.py <url1> <url2> ...")
        # For testing purposes, you can uncomment and run with a default URL
        # download_videos(["https://www.youtube.com/shorts/SOME_ID"])
