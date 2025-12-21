# Valorant VOD Processing System

This system processes Valorant match VODs from YouTube to extract timer readings for round detection.

## Overview

The `process_vods.py` script orchestrates the complete pipeline:

1. **Download VODs** - Uses yt-dlp to download YouTube VODs
2. **Extract Frames** - Captures frames every 5 seconds (configurable)
3. **Crop Timer** - Uses `crop_timer.py` to isolate the timer region
4. **Read Timer** - Uses `vision_to_data.py` with Ollama vision models to read timer values
5. **Store Results** - Saves all timer readings with timestamps for round detection analysis

## Prerequisites

1. **Python packages**:
   ```bash
   pip install opencv-python requests yt-dlp
   ```

2. **Ollama** with a vision model:
   ```bash
   # Install Ollama: https://ollama.ai
   ollama pull moondream  # Fast, lightweight model (recommended)
   # or
   ollama pull qwen2-vl   # More accurate but larger
   ```

3. **yt-dlp** (for downloading YouTube videos):
   ```bash
   pip install yt-dlp
   ```

## Usage

### Process a Specific Match

```bash
# Process all VODs for match ID 580237
python process_vods.py --match-id 580237
```

### Process Multiple Matches

```bash
# Process all matches (can take a long time!)
python process_vods.py --all

# Process first 3 matches only (for testing)
python process_vods.py --all --limit 3
```

### Custom Options

```bash
# Change frame extraction interval to 10 seconds
python process_vods.py --match-id 580237 --interval 10

# Use custom output directory
python process_vods.py --match-id 580237 --output-dir my_vod_data

# Use custom VODs JSON file
python process_vods.py --match-id 580237 --vods-file custom_vods.json
```

## Output Structure

```
vod_data/
├── match_580237/
│   ├── map_0/
│   │   ├── video/
│   │   │   └── Vse2jubhSU0.mp4
│   │   ├── frames/
│   │   │   ├── frame_0.0s.jpg
│   │   │   ├── frame_5.0s.jpg
│   │   │   ├── frame_10.0s.jpg
│   │   │   └── ...
│   │   ├── cropped_timers/
│   │   │   ├── timer_0.0s.jpg
│   │   │   ├── timer_5.0s.jpg
│   │   │   └── ...
│   │   └── timer_readings.json
│   ├── map_1/
│   │   └── ...
│   └── map_2/
│       └── ...
└── processing_summary.json
```

## Timer Readings Output

Each `timer_readings.json` contains:

```json
[
  {
    "timestamp": 0.0,
    "frame_path": "vod_data/match_580237/map_0/frames/frame_0.0s.jpg",
    "cropped_path": "vod_data/match_580237/map_0/cropped_timers/timer_0.0s.jpg",
    "timer_value": "1:40"
  },
  {
    "timestamp": 5.0,
    "frame_path": "vod_data/match_580237/map_0/frames/frame_5.0s.jpg",
    "cropped_path": "vod_data/match_580237/map_0/cropped_timers/timer_5.0s.jpg",
    "timer_value": "1:35"
  }
]
```

## Next Steps - Round Detection

Once you have the timer readings, you can analyze them to detect round start/end:

- **Round Start**: Timer shows `1:40` (buy phase start) or `1:39` (first tick)
- **Round End**: Timer shows very low values (e.g., `0:05`) or specific patterns

You mentioned you'll provide guidance on how to use these timer readings for round detection. The output format is designed to make this easy - you have:
- Exact timestamps in the video
- Corresponding timer values
- Paths to both original frames and cropped timer images for verification

## Individual Components

The script uses these existing components:

- **`crop_timer.py`** - `TimerCropper` class to crop timer region from frames
- **`vision_to_data.py`** - `summarize_png()` function to read timer values using Ollama
- **`vlr_vods.json`** - Source data with match IDs and YouTube VOD links

## Troubleshooting

**Issue**: `yt-dlp not found`
- **Solution**: `pip install yt-dlp`

**Issue**: Vision model errors
- **Solution**: Make sure Ollama is running and you've pulled a vision model:
  ```bash
  ollama pull moondream
  ```

**Issue**: Timer cropping is inaccurate
- **Solution**: Adjust the timer region parameters in `crop_timer.py`:
  - Lines 163-165: `timer_width`, `timer_height`, `timer_y`
