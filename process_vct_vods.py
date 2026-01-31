#!/usr/bin/env python3
import os
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from process_vods import VODProcessor

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

def process_vct_matches(limit=None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase credentials not found in .env")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🔍 Fetching VCT 2026 matches with missing timestamps...")
    # Query for VCT 2026 matches where timestamps is NULL
    query = supabase.table("replays").select("*").ilike("tournament", "%VCT 2026%")
    
    # Filter for NULL or empty timestamps (jsonb)
    # Note: In Supabase, we can use is_.null() for NULL or we can filter in python if needed
    response = query.execute()
    
    matches = response.data
    # Post-filter for empty timestamps and specific regions
    target_regions = ["EMEA", "Americas"]
    matches_to_process = [
        m for m in matches 
        if not m.get("timestamps") and any(region in m.get("tournament", "") for region in target_regions)
    ]
    
    if not matches_to_process:
        print("✅ No pending VCT 2026 matches found.")
        return

    if limit and limit > 0:
        matches_to_process = matches_to_process[:limit]
        print(f"🧪 Testing with {limit} match(es).")
    else:
        print(f"🚀 Processing all {len(matches_to_process)} matches found.")

    processor = VODProcessor(output_base_dir="vct_vod_processing")
    processor.frame_interval = 10
    
    for match in matches_to_process:
        match_id = match.get("id") or match.get("match_id") # Use whatever unique ID is in the table
        tournament = match.get("tournament")
        vod_links = match.get("vod_links", [])
        
        print(f"\n🎬 Processing Match: {match_id} | {tournament}")
        print(f"🔗 VOD Links: {len(vod_links)}")

        all_map_rounds = []
        
        # Determine base URLs for all links to detect segments
        base_urls = [url.split('&t=')[0].split('?t=')[0] for url in vod_links]

        for i, url in enumerate(vod_links):
            print(f"\n   📹 Map {i+1}/{len(vod_links)}: {url}")
            
            # Check if this link shares a base URL with any other link in this match
            base_url = base_urls[i]
            is_shared_vod = base_urls.count(base_url) > 1
            
            # If shared VOD, limit to 60 minutes (3600 seconds)
            max_duration = 3600 if is_shared_vod else None
            
            # User said "if 15 times nothing is seen, call it closed" only for share live stream links
            stop_after_nothings = 15 if is_shared_vod else 0
            
            if is_shared_vod:
                print(f"   ℹ️ Detected as VOD segment. Max duration: 60m, Early stop after {stop_after_nothings} 'nothings'.")
            else:
                print(f"   ℹ️ Standalone VOD. Processing entire video (no early stop).")

            # Create output directory structure to check for existing results
            match_dir = processor.output_base_dir / f"match_{match_id}" / f"map_{i}"
            clips_path = match_dir / "round_clips.json"
            
            if clips_path.exists():
                print(f"   ✅ Existing results found for Map {i+1}, skipping processing.")
                with open(clips_path, 'r') as f:
                    map_clips = json.load(f)
                    all_map_rounds.append(map_clips)
                continue

            # Process VOD - limit frames for faster run if testing
            result = processor.process_vod(
                url, 
                str(match_id), 
                map_index=i, 
                max_frames=2000, 
                max_duration=max_duration,
                stop_after_nothings=stop_after_nothings
            )
            
            if result and 'clips_file' in result:
                clips_path = Path(result['clips_file'])
                if clips_path.exists():
                    with open(clips_path, 'r') as f:
                        map_clips = json.load(f)
                        all_map_rounds.append(map_clips)
                
                # Cleanup: Delete cropped timers as requested
                match_dir = Path(result['output_dir'])
                cropped_dir = match_dir / "cropped_timers"
                if cropped_dir.exists():
                    print(f"   🧹 Cleaning up {cropped_dir}")
                    shutil.rmtree(cropped_dir)
            else:
                print(f"   ⚠️ Failed to process Map {i+1}")
                all_map_rounds.append([]) # Keep indexing consistent

        if all_map_rounds:
            print(f"⬆️ Updating Supabase for match {match_id}...")
            update_data = {"timestamps": all_map_rounds}
            
            # Update by whatever the primary key is. Assuming 'id' or 'match_id'
            # Based on common patterns in this codebase
            try:
                update_query = supabase.table("replays").update(update_data)
                if 'id' in match:
                    update_query = update_query.eq("id", match['id'])
                else:
                    update_query = update_query.eq("match_id", match['match_id'])
                
                update_response = update_query.execute()
                print(f"✅ Successfully updated match {match_id}")
            except Exception as e:
                print(f"❌ Failed to update Supabase: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process VCT 2026 VODs from Supabase")
    parser.add_argument("--limit", type=int, default=1, help="Limit number of matches (default: 1 for testing)")
    args = parser.parse_args()
    
    process_vct_matches(limit=args.limit)
