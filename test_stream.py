
import cv2
import subprocess
import time
import os

def get_stream_url(youtube_url):
    print(f"🔗 Getting stream URL for {youtube_url}...")
    cmd = [
        "yt-dlp",
        "-g", 
        "-f", "bestvideo[height<=360][ext=mp4]/best[height<=360]",  # 360p is enough
        youtube_url
    ]
    try:
        url = subprocess.check_output(cmd).decode("utf-8").strip()
        return url
    except subprocess.CalledProcessError as e:
        print(f"Error getting stream URL: {e}")
        return None

def extract_frames_from_stream(stream_url, num_frames=5):
    print(f"📹 Opening stream (this might take a few seconds)...")
    cap = cv2.VideoCapture(stream_url)
    
    if not cap.isOpened():
        print("❌ Failed to open stream")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"✅ Stream opened! FPS: {fps}, Duration: {duration/60:.1f} mins")
    
    # Try to grab a few frames at intervals
    for i in range(num_frames):
        target_time = (i + 1) * 60  # Every 1 minute
        
        # Seek to timestamp (in milliseconds)
        # Note: Seeking in streams can be slow depending on keyframes
        cap.set(cv2.CAP_PROP_POS_MSEC, target_time * 1000)
        
        ret, frame = cap.read()
        if ret:
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            filename = f"stream_frame_{timestamp:.1f}s.jpg"
            cv2.imwrite(filename, frame)
            print(f"   📸 Saved {filename} at {timestamp:.1f}s")
        else:
            print(f"   ❌ Failed to read frame at {target_time}s")

    cap.release()

if __name__ == "__main__":
    # Use one of the VODs we know
    url = "https://www.youtube.com/watch?v=F2N6YC69OUQ" 
    stream_url = get_stream_url(url)
    if stream_url:
        extract_frames_from_stream(stream_url)
