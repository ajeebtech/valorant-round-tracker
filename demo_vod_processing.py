#!/usr/bin/env python3
"""
Test bench for VOD processing and round clipping.
This script sets up a "smart" pipeline that skips already completed steps (download, extract)
so you can iterate quickly on the vision processing and round detection logic.
"""

import os
import json
import urllib.parse
from pathlib import Path
from process_vods import VODProcessor

def parse_youtube_url(url):
    """Parses video ID and start time from YouTube URL."""
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    
    video_id = query.get('v', [None])[0]
    t_param = query.get('t', ['0s'])[0]
    
    # helper to parse '352s' or '1h2m3s'
    start_time = 0
    if t_param.endswith('s'):
        try:
            start_time = float(t_param[:-1])
        except ValueError:
            start_time = 0
    else:
        try:
            start_time = float(t_param)
        except ValueError:
            start_time = 0
            
    return video_id, start_time

def setup_demo(match_id="demo_test", youtube_url="https://www.youtube.com/watch?v=te42xAzwqjg&t=352s", use_stream=True):
    """
    Setup a demo environment for iterative testing.
    """
    output_base = "demo_output"
    processor = VODProcessor(output_base_dir=output_base)
    processor.frame_interval = 10  # 5 or 10 seconds
    
    vid_id, start_time = parse_youtube_url(youtube_url)
    
    match_dir = Path(output_base) / f"match_{match_id}" / "map_0"
    match_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🧪 TEST BENCH: Match {match_id}")
    print(f"📂 Output Dir: {match_dir}")
    print(f"⏱️  Start Time Offset: {start_time}s")
    
    # --- Step 1: Video Source (Stream or File) ---
    video_source = None
    
    if use_stream:
        print("🌐 Resolving Stream URL...")
        video_source = processor.get_stream_url(youtube_url)
        if not video_source:
            print("❌ Failed to get stream URL, falling back to download logic")
            use_stream = False
        else:
            print(f"✅ Using Stream URL")

    if not use_stream:
        # Fallback to download or local file
        video_dir = match_dir / "video"
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for local manual override
        manual_vod_path = Path("2.mp4")
        
        # Check if any video already exists in the target dir
        existing_videos = list(video_dir.glob("*.mp4"))
        
        if manual_vod_path.exists():
            print(f"📦 Found local manual VOD: {manual_vod_path}")
            # Use shutil to copy if it's not already in place
            import shutil
            target_path = video_dir / manual_vod_path.name
            if not target_path.exists():
                print(f"   Copying to {target_path}...")
                shutil.copy(manual_vod_path, target_path)
            video_source = target_path
            print(f"✅ Using local video: {video_source.name}")
            
        elif existing_videos:
            video_source = existing_videos[0]
            print(f"✅ Video found in cache: {video_source.name} (Skipping download)")
        else:
            print("⬇️  Downloading video...")
            video_source = processor.download_vod(youtube_url, video_dir)
            if not video_source:
                print("❌ Download failed")
                return

    # --- Step 2: Extract Frames (Fast: Crop Immediately) ---
    # We save directly to cropped_timers because we skip full frames
    cropped_dir = match_dir / "cropped_timers"
    cropped_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for existing cropped timers
    existing_crops = list(cropped_dir.glob("timer_*.jpg"))
    
    # Filter crops that are >= start_time to avoid using old cache from different start times if same match_id
    existing_crops = [p for p in existing_crops if float(p.stem.replace('timer_', '').replace('s', '')) >= start_time]
    
    if len(existing_crops) > 10: 
        print(f"✅ Cropped timers found: {len(existing_crops)} (Skipping extraction)")
        frame_paths = sorted(existing_crops, key=lambda p: float(p.stem.replace('timer_', '').replace('s', '')))
    else:
        print("🎞️  Extracting & Cropping frames...")
        frame_paths = processor.extract_frames(
            video_source, 
            cropped_dir, 
            processor.frame_interval,
            cropper=processor.timer_cropper,
            start_time=start_time,
            max_frames=500
        )

    # For fast testing iteration, limit to first 500 frames if streaming to avoid long wait
    frame_paths = frame_paths[:500]

    # --- Step 3: Vision Processing (Timer Reading) ---
    force_vision = False 
    
    results_file = match_dir / "timer_readings.json"
    timer_results = []
    
    if results_file.exists() and not force_vision:
        print(f"✅ Timer readings found (Skipping vision processing)")
        with open(results_file, 'r') as f:
            timer_results = json.load(f)
    else:
        print("👁️  Running Vision Model (Timer Reading)...")
        # Added early stopping after 30 consecutive "nothing" readings
        timer_results = processor.process_frames(frame_paths, match_dir, stop_after_nothings=30)
        processor.save_results(timer_results, results_file)

    # --- Step 4: Round Detection Logic ---
    print("\n🧠 Running Round Detection Logic...")
    rounds = processor.round_detector.detect_rounds(timer_results)
    
    # Print a nice summary for debugging
    processor.round_detector.print_round_summary(rounds)
    
    # Save results
    rounds_file = match_dir / "rounds.json"
    processor.round_detector.save_rounds(rounds, rounds_file)
    
    clips_file = match_dir / "round_clips.json"
    processor.round_detector.generate_round_clips(rounds, clips_file)
    
    print("\n✨ Test Run Complete!")
    print(f"   Check {match_dir} for results.")

if __name__ == '__main__':
    setup_demo(
        match_id="te42xAzwqjg", 
        youtube_url="https://www.youtube.com/watch?v=wx6KecG3N50",
        use_stream=True
    )
