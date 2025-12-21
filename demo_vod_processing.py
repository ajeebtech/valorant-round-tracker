#!/usr/bin/env python3
"""
Test bench for VOD processing and round clipping.
This script sets up a "smart" pipeline that skips already completed steps (download, extract)
so you can iterate quickly on the vision processing and round detection logic.
"""

import os
import json
from pathlib import Path
from process_vods import VODProcessor

def setup_demo(match_id="demo_test", youtube_url="https://www.youtube.com/watch?v=F2N6YC69OUQ&t=4s"):
    """
    Setup a demo environment for iterative testing.
    """
    output_base = "demo_output"
    processor = VODProcessor(output_base_dir=output_base)
    processor.frame_interval = 10  # 5 or 10 seconds
    
    match_dir = Path(output_base) / f"match_{match_id}" / "map_0"
    match_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🧪 TEST BENCH: Match {match_id}")
    print(f"📂 Output Dir: {match_dir}")
    
    # --- Step 1: Download Video ---
    video_dir = match_dir / "video"
    # Check if any video exists
    existing_videos = list(video_dir.glob("*.mp4"))
    if existing_videos:
        video_path = existing_videos[0]
        print(f"✅ Video found: {video_path.name} (Skipping download)")
    else:
        print("⬇️  Downloading video...")
        video_path = processor.download_vod(youtube_url, video_dir)
        if not video_path:
            print("❌ Download failed")
            return

    # --- Step 2: Extract Frames ---
    frames_dir = match_dir / "frames"
    existing_frames = list(frames_dir.glob("*.jpg"))
    if len(existing_frames) > 10: # Arbitrary threshold to assume success
        print(f"✅ Frames found: {len(existing_frames)} frames (Skipping extraction)")
        # collect paths
        frame_paths = sorted(list(frames_dir.glob("*.jpg")), key=lambda p: float(p.stem.split('_')[1].replace('s', '')))
    else:
        print("🎞️  Extracting frames...")
        frame_paths = processor.extract_frames(video_path, frames_dir, processor.frame_interval)

    # For fast testing iteration, limit to first 100 frames (covers ~16 mins)
    frame_paths = frame_paths[:100]

    # --- Step 3: Vision Processing (Timer Reading) ---
    # We might want to re-run this if we are tweaking the vision code
    # For now, let's load it if it exists, but you can set force_vision=True to re-run
    force_vision = False 
    
    results_file = match_dir / "timer_readings.json"
    timer_results = []
    
    if results_file.exists() and not force_vision:
        print(f"✅ Timer readings found (Skipping vision processing)")
        print(f"   To re-run vision, delete {results_file.name} or edit script")
        with open(results_file, 'r') as f:
            timer_results = json.load(f)
    else:
        print("👁️  Running Vision Model (Timer Reading)...")
        timer_results = processor.process_frames(frame_paths, match_dir)
        processor.save_results(timer_results, results_file)

    # --- Step 4: Round Detection Logic ---
    # This is likely what we want to iterate on most?
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
    # You can change this URL to whatever video you want to test with
    setup_demo(
        match_id="582604", 
        youtube_url="https://youtu.be/xsKo9EEtqO8"
    )
