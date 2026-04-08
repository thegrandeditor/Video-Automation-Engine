import sqlite3
import os

DB_PATH = 'videos.db'

def get_connection():
    """Returns a SQLite connection."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create the videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_title TEXT,
            creator_handle TEXT,
            duration INTEGER,
            url TEXT,
            download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create the analysis table for purely local AI results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_url TEXT,
            transcript TEXT,
            flagged_data TEXT,
            dead_air_data TEXT,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def log_video(original_title, creator_handle, duration, url):
    """Logs a downloaded video's metadata to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO videos (original_title, creator_handle, duration, url)
        VALUES (?, ?, ?, ?)
    ''', (original_title, creator_handle, duration, url))
    
    conn.commit()
    conn.close()

def log_analysis(video_url, transcript, flagged_data, dead_air_data):
    """Logs the purely local AI analysis results to the database."""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO analysis (video_url, transcript, flagged_data, dead_air_data)
        VALUES (?, ?, ?, ?)
    ''', (video_url, transcript, json.dumps(flagged_data), json.dumps(dead_air_data)))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # Initialize the database when run directly
    init_db()
    print("Database initialized successfully.")
