import yt_dlp
import os
import sys
import database

ASSETS_DIR = 'raw_assets'

def download_videos(urls):
    """Downloads videos using yt-dlp and logs metadata to SQLite."""
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
        
    # Ensure database is initialized
    database.init_db()
        
    ydl_opts = {
        'outtmpl': os.path.join(ASSETS_DIR, '%(id)s.%(ext)s'),
        'format': 'best',
        'nopart': True,
        'quiet': False,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            if 'tiktok.com' in url and '/photo/' in url:
                url = url.replace('/photo/', '/video/')
                
            print(f"Processing URL: {url}")
            try:
                # Extract info dict without downloading first to get metadata
                info_dict = ydl.extract_info(url, download=True)
                
                title = info_dict.get('title', 'Unknown Title')
                creator = info_dict.get('uploader', info_dict.get('channel', 'Unknown Creator'))
                duration = info_dict.get('duration', 0)
                
                # Log metadata to the database
                database.log_video(title, creator, duration, url)
                print(f"Successfully downloaded and logged: {title} by {creator}")
                
            except Exception as e:
                print(f"Failed to process {url}: {e}")

if __name__ == '__main__':
    # You can pass URLs as command line arguments
    if len(sys.argv) > 1:
        urls_to_download = sys.argv[1:]
        download_videos(urls_to_download)
    else:
        print("Usage: python downloader.py <url1> <url2> ...")
        # For testing purposes, you can uncomment and run with a default URL
        # download_videos(["https://www.youtube.com/shorts/SOME_ID"])
