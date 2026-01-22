#!/usr/bin/env python3
"""
Multi-map VOD processing demo.
Handles cases where multiple maps are in a single VOD link with different timestamps.
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
    
    # helper to parse '15778s' or '1h2m3s' (simple 's' check for now)
    start_time = 0
    if t_param.endswith('s'):
        start_time = float(t_param[:-1])
    else:
        # Handle simple integer seconds if no 's' suffix
        try:
            start_time = float(t_param)
        except ValueError:
            print(f"⚠️  Could not parse time parameter: {t_param}, defaulting to 0")
            start_time = 0
            
    return video_id, start_time

def process_map_vod(match_id, map_index, youtube_url, processor, max_frames=500):
    """Processes a single map from a VOD URL."""
    
    video_id, start_time = parse_youtube_url(youtube_url)
    
    print(f"\n{'='*60}")
    print(f"🎮 Processing Match {match_id} - Map {map_index}")
    print(f"🔗 URL: {youtube_url}")
    print(f"⏱️  Start Time: {start_time}s")
    print(f"{'='*60}")
    
    output_base = "demo_output"
    match_dir = Path(output_base) / f"match_{match_id}" / f"map_{map_index}"
    match_dir.mkdir(parents=True, exist_ok=True)
    
    # --- Step 1: Video Source (Stream) ---
    print("🌐 Resolving Stream URL...")
    video_source = processor.get_stream_url(youtube_url)
    if not video_source:
        print("❌ Failed to get stream URL")
        return

    # --- Step 2: Extract Frames (Fast: Crop Immediately) ---
    cropped_dir = match_dir / "cropped_timers"
    cropped_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for existing crops (simple cache check)
    existing_crops = list(cropped_dir.glob("timer_*.jpg"))
    
    # We want to be careful with cache. The timestamps are absolute based on the video 0.
    # So if we processed map 1 (t=15000), filenames will be timer_15000.0s.jpg
    # If we run this again, we should find them.
    
    # For this exercise, let's assume if we have >> 10 frames around the start time, we are good.
    # But simplified: check if directory is populated.
    
    if len(existing_crops) > 50:
        print(f"✅ Cropped timers found: {len(existing_crops)} (Skipping extraction)")
        frame_paths = sorted(existing_crops, key=lambda p: float(p.stem.replace('timer_', '').replace('s', '')))
        # Filter frame paths to be within our range (start_time to start_time + limit)?
        # If we re-run, we might pick up frames from previous runs.
        # Ideally we should filter by start_time.
        
        # Simple filter: take frames >= start_time
        frame_paths = [p for p in frame_paths if float(p.stem.replace('timer_', '').replace('s', '')) >= start_time]
        frame_paths = frame_paths[:max_frames] # limit to max_frames
    else:
        print("🎞️  Extracting & Cropping frames...")
        frame_paths = processor.extract_frames(
            video_source, 
            cropped_dir, 
            processor.frame_interval,
            cropper=processor.timer_cropper,
            start_time=start_time,
            max_frames=max_frames # Limit to strict duration
        )

    # --- Step 3: Vision Processing ---
    results_file = match_dir / "timer_readings.json"
    if results_file.exists():
         print(f"✅ Timer readings found (Skipping vision processing)")
         with open(results_file, 'r') as f:
            timer_results = json.load(f)
    else:
        print("👁️  Running Vision Model (Timer Reading)...")
        # Added early stopping after 30 consecutive "nothing" readings
        timer_results = processor.process_frames(frame_paths, match_dir, stop_after_nothings=30)
        processor.save_results(timer_results, results_file)

    # --- Step 4: Round Detection ---
    print("\n🧠 Running Round Detection Logic...")
    rounds = processor.round_detector.detect_rounds(timer_results)
    
    processor.round_detector.print_round_summary(rounds)
    
    # Save results
    rounds_file = match_dir / "rounds.json"
    processor.round_detector.save_rounds(rounds, rounds_file)
    
    clips_file = match_dir / "round_clips.json"
    processor.round_detector.generate_round_clips(rounds, clips_file)
    
    print(f"✅ Map {map_index} Complete!")


def main():
    # List of VOD links for the match
    # These must be sorted by time, or we will sort them ourselves
    vod_links = [
        "https://www.youtube.com/watch?v=te42xAzwqjg&t=352s"
    ]
    
    match_id = "multi_map_test"
    processor = VODProcessor(output_base_dir="demo_output")
    processor.frame_interval = 10 # 10s for speed
    
    # 1. Parse all links first to get timestamps
    segments = []
    for i, link in enumerate(vod_links):
        vid_id, start_time = parse_youtube_url(link)
        segments.append({
            'index': i,
            'link': link,
            'video_id': vid_id,
            'start_time': start_time
        })
    
    # 2. Sort by video_id and then start_time
    # This ensures we handle multiple videos correctly and sequential maps correctly
    segments.sort(key=lambda x: (x['video_id'], x['start_time']))
    
    # 3. Process each segment with a dynamic limit
    for i, seg in enumerate(segments):
        current_start = seg['start_time']
        
        # Determine strict end time based on next segment
        # Default safety limit: 90 minutes (5400s) if it's the last map
        duration_limit = 5400 
        
        # Check if there is a next segment in the SAME video
        if i + 1 < len(segments):
            next_seg = segments[i+1]
            if next_seg['video_id'] == seg['video_id']:
                # The gap constitutes the max duration for this map
                gap = next_seg['start_time'] - current_start
                if gap > 0:
                    duration_limit = gap
                    print(f"ℹ️  Map {seg['index']} duration limited to {gap:.1f}s (until next map starts)")
        
        # Convert duration to max_frames
        # Add a large buffer (10 mins = 600s) before next map to avoid overlap and intro
        # But ensure we don't go negative
        safe_duration = max(0, duration_limit - 600)
        max_frames = int(safe_duration / processor.frame_interval)
        
        print(f"🎯 Setting limit: {max_frames} frames ({safe_duration/60:.1f} mins)")
        
        # Pass explicit max_frames to our processing function
        # We need to modify process_map_vod to accept max_frames override
        process_map_vod(match_id, seg['index'], seg['link'], processor, max_frames=max_frames)

if __name__ == "__main__":
    main()
