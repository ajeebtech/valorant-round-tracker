#!/usr/bin/env python3
"""
Valorant VOD Processing Pipeline

This script processes Valorant VODs from YouTube URLs:
1. Downloads VODs using yt-dlp
2. Extracts frames every 5 seconds
3. Crops the timer region from each frame
4. Reads the timer value using vision models
5. Stores the timer readings for round detection analysis

Usage:
    python process_vods.py --match-id 580237
    python process_vods.py --all --limit 5
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from crop_timer import TimerCropper
from vision_to_data import summarize_png
from round_detector import RoundDetector


class VODProcessor:
    """Processes Valorant VODs to extract timer readings for round detection."""
    
    def __init__(self, output_base_dir: str = "vod_data"):
        """
        Initialize the VOD processor.
        
        Args:
            output_base_dir: Base directory for all output data
        """
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)
        
        # Initialize timer cropper
        self.timer_cropper = TimerCropper(output_size=(400, 200))
        
        # Initialize round detector
        self.round_detector = RoundDetector()
        
        # Frame extraction interval (seconds)
        self.frame_interval = 5
        
    def load_vods_data(self, vods_file: str = "vlr_vods.json") -> List[Dict]:
        """Load VOD data from JSON file."""
        with open(vods_file, 'r') as f:
            return json.load(f)
    
    def get_match_by_id(self, match_id: str, vods_data: List[Dict]) -> Optional[Dict]:
        """Find a specific match by ID."""
        for match in vods_data:
            if match['match_id'] == match_id:
                return match
        return None
    
    def download_vod(self, youtube_url: str, output_dir: Path) -> Optional[Path]:
        """
        Download a VOD using yt-dlp.
        
        Args:
            youtube_url: YouTube URL to download
            output_dir: Directory to save the video
            
        Returns:
            Path to downloaded video file, or None if failed
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract video ID for filename
        video_id = youtube_url.split('/')[-1].split('?')[0]
        output_template = str(output_dir / f"{video_id}.%(ext)s")
        
        print(f"📥 Downloading VOD: {youtube_url}")
        
        try:
            # Use yt-dlp to download the video
            # Format: 360p video for fast download (timer is still readable at this quality)
            # Added bot avoidance args
            cmd = [
                "yt-dlp",
                "-f", "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]/best",
                "--merge-output-format", "mp4",
                "--extractor-args", "youtube:player_client=android",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "-o", output_template,
                youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Find the downloaded file
            downloaded_files = list(output_dir.glob(f"{video_id}.*"))
            if downloaded_files:
                print(f"✅ Downloaded: {downloaded_files[0]}")
                return downloaded_files[0]
            else:
                print(f"❌ Download failed: No output file found")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Download failed: {e.stderr}")
            return None
        except FileNotFoundError:
            print("❌ yt-dlp not found. Please install it: pip install yt-dlp")
            return None
    
    def extract_frames(self, video_path: Path, output_dir: Path, 
                      interval: int = 5) -> List[Path]:
        """
        Extract frames from video at specified interval.
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save frames
            interval: Time interval in seconds between frames
            
        Returns:
            List of paths to extracted frame images
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🎬 Extracting frames every {interval} seconds from: {video_path.name}")
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"❌ Failed to open video: {video_path}")
            return []
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        print(f"   Video: {duration:.1f}s @ {fps:.1f}fps")
        
        frame_paths = []
        frame_interval = int(fps * interval)
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract frame at interval
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                frame_filename = f"frame_{timestamp:.1f}s.jpg"
                frame_path = output_dir / frame_filename
                
                cv2.imwrite(str(frame_path), frame)
                frame_paths.append(frame_path)
                extracted_count += 1
            
            frame_count += 1
        
        cap.release()
        print(f"✅ Extracted {extracted_count} frames")
        
        return frame_paths
    
    def process_frames(self, frame_paths: List[Path], output_dir: Path) -> List[Dict]:
        """
        Process frames: crop timer and read values.
        
        Args:
            frame_paths: List of frame image paths
            output_dir: Directory to save cropped timers
            
        Returns:
            List of dictionaries with timestamp and timer readings
        """
        cropped_dir = output_dir / "cropped_timers"
        cropped_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"⏱️  Processing {len(frame_paths)} frames...")
        
        results = []
        
        for i, frame_path in enumerate(frame_paths, 1):
            # Extract timestamp from filename
            timestamp_str = frame_path.stem.replace("frame_", "").replace("s", "")
            timestamp = float(timestamp_str)
            
            print(f"  [{i}/{len(frame_paths)}] Processing {timestamp:.1f}s...", end=" ")
            
            # Crop timer region
            cropped_filename = f"timer_{timestamp:.1f}s.jpg"
            cropped_path = cropped_dir / cropped_filename
            
            cropped_img = self.timer_cropper.crop_timer(
                str(frame_path),
                method='heuristic',
                output_path=str(cropped_path)
            )
            
            if cropped_img is None:
                print("❌ Failed to crop")
                continue
            
            # Read timer value
            timer_value = summarize_png(str(cropped_path))
            
            result = {
                'timestamp': timestamp,
                'frame_path': str(frame_path),
                'cropped_path': str(cropped_path),
                'timer_value': timer_value
            }
            
            results.append(result)
            print(f"Timer: {timer_value}")
        
        print(f"✅ Processed {len(results)} frames successfully")
        
        return results
    
    def save_results(self, results: List[Dict], output_file: Path):
        """Save processing results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Saved results to: {output_file}")
    
    def process_vod(self, youtube_url: str, match_id: str, map_index: int = 0) -> Optional[Dict]:
        """
        Process a single VOD through the complete pipeline.
        
        Args:
            youtube_url: YouTube URL of the VOD
            match_id: Match ID for organizing output
            map_index: Index of the map/VOD within the match
            
        Returns:
            Dictionary with processing results and metadata
        """
        print(f"\n{'='*80}")
        print(f"Processing VOD: Match {match_id}, Map {map_index + 1}")
        print(f"URL: {youtube_url}")
        print(f"{'='*80}\n")
        
        # Create output directory structure
        match_dir = self.output_base_dir / f"match_{match_id}" / f"map_{map_index}"
        
        # Step 1: Download VOD
        video_path = self.download_vod(youtube_url, match_dir / "video")
        if not video_path:
            return None
        
        # Step 2: Extract frames
        frames_dir = match_dir / "frames"
        frame_paths = self.extract_frames(video_path, frames_dir, self.frame_interval)
        if not frame_paths:
            return None
        
        # Step 3: Process frames (crop + read timer)
        timer_results = self.process_frames(frame_paths, match_dir)
        
        # Step 4: Save timer results
        results_file = match_dir / "timer_readings.json"
        self.save_results(timer_results, results_file)
        
        # Step 5: Detect rounds from timer readings
        print(f"\n🎯 Detecting round boundaries...")
        rounds = self.round_detector.detect_rounds(timer_results)
        
        # Save detected rounds
        rounds_file = match_dir / "rounds.json"
        self.round_detector.save_rounds(rounds, rounds_file)
        
        # Generate round clips
        clips_file = match_dir / "round_clips.json"
        self.round_detector.generate_round_clips(rounds, clips_file)
        
        # Print summary
        self.round_detector.print_round_summary(rounds)
        
        # Return summary
        return {
            'match_id': match_id,
            'map_index': map_index,
            'youtube_url': youtube_url,
            'video_path': str(video_path),
            'num_frames': len(frame_paths),
            'num_readings': len(timer_results),
            'num_rounds': len(rounds),
            'results_file': str(results_file),
            'rounds_file': str(rounds_file),
            'clips_file': str(clips_file),
            'output_dir': str(match_dir)
        }
    
    def process_match(self, match_data: Dict) -> List[Dict]:
        """
        Process all VODs for a match.
        
        Args:
            match_data: Match data dictionary from vlr_vods.json
            
        Returns:
            List of processing results for each VOD
        """
        match_id = match_data['match_id']
        vod_links = match_data['vod_links']
        
        if not vod_links:
            print(f"⚠️  No VOD links for match {match_id}")
            return []
        
        results = []
        for i, vod_url in enumerate(vod_links):
            result = self.process_vod(vod_url, match_id, map_index=i)
            if result:
                results.append(result)
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='Process Valorant VODs to extract timer readings for round detection'
    )
    
    parser.add_argument(
        '--match-id',
        type=str,
        help='Process a specific match by ID (e.g., 580237)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all matches with VODs'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of matches to process (useful for testing)'
    )
    parser.add_argument(
        '--vods-file',
        type=str,
        default='vlr_vods.json',
        help='Path to VODs JSON file (default: vlr_vods.json)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='vod_data',
        help='Base output directory (default: vod_data)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Frame extraction interval in seconds (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = VODProcessor(output_base_dir=args.output_dir)
    processor.frame_interval = args.interval
    
    # Load VODs data
    print(f"📂 Loading VODs from: {args.vods_file}")
    vods_data = processor.load_vods_data(args.vods_file)
    print(f"   Found {len(vods_data)} matches\n")
    
    # Process based on arguments
    if args.match_id:
        # Process specific match
        match_data = processor.get_match_by_id(args.match_id, vods_data)
        if not match_data:
            print(f"❌ Match ID {args.match_id} not found")
            sys.exit(1)
        
        results = processor.process_match(match_data)
        
    elif args.all:
        # Process all matches with VODs
        matches_with_vods = [m for m in vods_data if m['vod_links']]
        
        if args.limit:
            matches_with_vods = matches_with_vods[:args.limit]
        
        print(f"Processing {len(matches_with_vods)} matches...\n")
        
        all_results = []
        for i, match_data in enumerate(matches_with_vods, 1):
            print(f"\n{'='*80}")
            print(f"Match {i}/{len(matches_with_vods)}: {match_data['match_id']}")
            print(f"{'='*80}")
            
            results = processor.process_match(match_data)
            all_results.extend(results)
        
        # Save overall summary
        summary_file = processor.output_base_dir / "processing_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n📊 Saved processing summary to: {summary_file}")
        
    else:
        parser.print_help()
        print("\n⚠️  Please specify either --match-id or --all")
        sys.exit(1)
    
    print("\n✨ Processing complete!")


if __name__ == '__main__':
    main()
