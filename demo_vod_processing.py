#!/usr/bin/env python3
"""
Quick demo of the VOD processing pipeline.
This shows how to use the process_vods.py script programmatically.
"""

from process_vods import VODProcessor

def demo():
    """Demonstrate processing a single VOD."""
    
    # Initialize processor
    processor = VODProcessor(output_base_dir="demo_output")
    processor.frame_interval = 10  # Use 10 seconds for faster demo
    
    # Example: Process first VOD from match 580237
    # URL: https://youtu.be/Vse2jubhSU0?t=11863
    
    print("\n" + "="*80)
    print("DEMO: Processing a Valorant VOD")
    print("="*80 + "\n")
    
    # Process the VOD
    result = processor.process_vod(
        youtube_url="https://youtu.be/Vse2jubhSU0?t=11863",
        match_id="580237",
        map_index=0
    )
    
    if result:
        print("\n" + "="*80)
        print("✨ DEMO COMPLETE!")
        print("="*80)
        print(f"\nResults saved to: {result['output_dir']}")
        print(f"Timer readings: {result['results_file']}")
        print(f"\nExtracted {result['num_readings']} timer readings from {result['num_frames']} frames")
    else:
        print("\n❌ Demo failed")


if __name__ == '__main__':
    demo()
