# Round Detection Logic - Quick Reference

## Timer Reading Analysis

The system now detects round boundaries based on:

### Round Start Detection
- **Trigger**: Timer shows `1:39` to `1:30` (whichever appears first)
- **Action**: Mark as start of new round

### Spike Plant Detection
- **Indicator**: Red triangle visible in timer region
- **Action**: Record spike plant timestamp

### Round End Detection

Three scenarios:

1. **Next Round Started**
   - **Trigger**: New round start detected (1:39-1:30)
   - **Action**: End previous round 10 seconds before new start
   - **Reason**: `next_round_started`

2. **Spike Timeout**
   - **Trigger**: 35 seconds elapsed since spike plant
   - **Action**: End round at timeout
   - **Reason**: `spike_timeout`
   - **Note**: Used when spike doesn't count down to 0:00

3. **VOD Ended**
   - **Trigger**: End of VOD reached
   - **Action**: End round at last reading
   - **Reason**: `vod_ended`

## Usage

### Automatic Round Detection (Integrated)
```bash
# Process VOD with automatic round detection
python process_vods.py --match-id 580237
```

Output includes:
- `timer_readings.json` - Raw timer values
- `rounds.json` - Detected round boundaries
- `round_clips.json` - Timestamps for creating clips

### Manual Round Detection (On Existing Data)
```bash
# Run round detection on existing timer readings
python round_detector.py path/to/timer_readings.json
```

## Output Format

### rounds.json
```json
[
  {
    "round_number": 1,
    "start_timestamp": 120.5,
    "start_timer": "1:39",
    "end_timestamp": 180.0,
    "end_reason": "next_round_started",
    "spike_planted": true,
    "spike_plant_timestamp": 155.0,
    "duration": 59.5
  }
]
```

### round_clips.json
```json
[
  {
    "round_number": 1,
    "start_time": 120.5,
    "end_time": 180.0,
    "duration": 59.5,
    "spike_planted": true
  }
]
```

## Implementation Details

### Files Modified
- `vision_to_data.py` - Now detects both timer value AND red triangle
- `process_vods.py` - Integrated round detection into pipeline

### Files Created
- `round_detector.py` - Core round detection logic
- `ROUND_DETECTION.md` - This documentation

## Testing

Test with a single match:
```bash
python process_vods.py --match-id 580237
```

Check output:
```bash
# View detected rounds
cat vod_data/match_580237/map_0/rounds.json

# View clip timestamps
cat vod_data/match_580237/map_0/round_clips.json
```
