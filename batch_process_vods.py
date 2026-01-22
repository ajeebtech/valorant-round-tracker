#!/usr/bin/env python3
"""
Batch process multiple Valorant VOD URLs and compile the results.
Usage:
    python batch_process_vods.py url1 url2 url3
    python batch_process_vods.py --file urls.txt
"""

import argparse
import json
from pathlib import Path
from process_vods import VODProcessor

def batch_process(urls: list, output_file: str = "compiled_rounds.json"):
    # Initialize processor
    # We'll use a specific output directory for this batch run
    output_base = "batch_output"
    processor = VODProcessor(output_base_dir=output_base)
    processor.frame_interval = 10 # 10s interval for speed, same as demo
    
    # We will collect the list of rounds for each URL
    # Result format: [[round1, round2], [round1], ...]
    compiled_results = []
    
    print(f"\n📋 Starting Batch Processing of {len(urls)} URLs...")
    print(f"📂 Output Directory: {output_base}")
    
    for i, url in enumerate(urls):
        print(f"\n{'='*80}")
        print(f"🚀 Processing URL {i+1}/{len(urls)}")
        print(f"🔗 {url}")
        print(f"{'='*80}\n")
        
        # We use a single 'match_id' for the batch, and map_index to separate them
        match_id = "batch_run"
        
        try:
            # process_vod handles:
            # 1. Stream/Download
            # 2. Extract/Crop
            # 3. Vision Processing
            # 4. Round Detection
            # 5. Saving individual results
            result_summary = processor.process_vod(
                youtube_url=url, 
                match_id=match_id, 
                map_index=i
            )
            
            if result_summary and 'rounds_file' in result_summary:
                # Load the rounds data that was just saved to append to our master list
                rounds_path = Path(result_summary['rounds_file'])
                if rounds_path.exists():
                    with open(rounds_path, 'r') as f:
                        rounds_data = json.load(f)
                    compiled_results.append(rounds_data)
                    print(f"✅ Successfully added {len(rounds_data)} rounds to compiled results")
                else:
                    print(f"⚠️  Rounds file missing for URL {i+1}")
                    compiled_results.append([])
            else:
                print(f"❌ Processing failed for URL {i+1}")
                compiled_results.append([])
                
        except Exception as e:
            print(f"❌ Critical error processing URL {i+1}: {e}")
            compiled_results.append([])
            
    # Save the fully compiled JSON
    output_path = Path(output_file)
    with open(output_path, 'w') as f:
        json.dump(compiled_results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ BATCH PROCESSING COMPLETE")
    print(f"{'='*80}")
    print(f"📄 Compiled results saved to: {output_path.absolute()}")
    print(f"📊 Processed {len(urls)} URLs")
    print(f"📚 Result structure: List of {len(compiled_results)} lists (one per URL)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch process Valorant VOD URLs')
    parser.add_argument('urls', nargs='*', help='List of YouTube URLs to process')
    parser.add_argument('--file', '-f', help='Path to text file containing URLs (one per line)')
    parser.add_argument('--output', '-o', default='compiled_rounds.json', help='Output JSON file name')
    
    args = parser.parse_args()
    
    urls_to_process = args.urls
    
    if args.file:
        file_path = Path(args.file)
        if file_path.exists():
            with open(file_path, 'r') as f:
                # Filter out empty lines and comments
                file_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                urls_to_process.extend(file_urls)
        else:
            print(f"❌ File not found: {args.file}")
            
    if not urls_to_process:
        print("⚠️  No URLs provided.")
        print("Usage:")
        print("  python batch_process_vods.py https://youtu.be/xxx https://youtu.be/yyy")
        print("  python batch_process_vods.py --file my_urls.txt")
    else:
        batch_process(urls_to_process, args.output)
