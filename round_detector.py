"""
Valorant Round Detection Module

Detects round boundaries from timer readings based on game logic:
- Round starts when timer shows 1:39-1:30
- Spike plant indicated by red triangle
- Round ends based on spike timer or next round start
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class RoundDetector:
    """Detects round boundaries from timer readings."""
    
    # Timer values that indicate round start (buy phase end / gameplay start)
    # We include 1:40 because that's the exact start of a standard round
    ROUND_START_TIMES = ['1:40', '1:39', '1:38', '1:37', '1:36', '1:35', '1:34', '1:33', '1:32', '1:31', '1:30']
    
    # Spike defuse/explosion countdown range
    SPIKE_COUNTDOWN_START = '0:45'  # Spike timer starts at 45 seconds
    SPIKE_COUNTDOWN_END = '0:00'
    
    # Time limits
    SPIKE_TIMEOUT_SECONDS = 35  # Max duration after spike plant
    ROUND_END_BUFFER_SECONDS = 10  # Cut previous round 10s before next starts
    STANDARD_ROUND_DURATION_SECONDS = 100 # 1:40 is 100 seconds
    
    # Consecutive "nothing" readings required to confirm round end
    ROUND_END_NOTHING_THRESHOLD = 2
    
    def __init__(self):
        """Initialize the round detector."""
        pass
    
    @staticmethod
    def parse_timer(timer_str: Optional[str]) -> Optional[int]:
        """
        Convert timer string (M:SS) to seconds.
        
        Args:
            timer_str: Timer string like "1:40", "0:45"
            
        Returns:
            Total seconds, or None if invalid
        """
        if not timer_str or not isinstance(timer_str, str):
            return None
        
        try:
            parts = timer_str.split(':')
            if len(parts) != 2:
                return None
            minutes, seconds = int(parts[0]), int(parts[1])
            return minutes * 60 + seconds
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def is_round_start_timer(timer_str: Optional[str]) -> bool:
        """Check if timer value indicates round start."""
        if not timer_str:
            return False
        return timer_str in RoundDetector.ROUND_START_TIMES
    
    def calculate_round_start_timestamp(self, observed_timestamp: float, timer_str: str) -> float:
        """
        Calculate the refined round start timestamp.
        Since we might sample the timer at 1:35 (5s into the round),
        we want to adjust the start time back to when it was 1:40.
        """
        timer_seconds = self.parse_timer(timer_str)
        if timer_seconds is None:
            return observed_timestamp
            
        # How many seconds have passed since 1:40?
        # e.g. timer is 1:35 (95s). Standard starts at 1:40 (100s).
        # elapsed = 100 - 95 = 5s.
        elapsed_since_start = self.STANDARD_ROUND_DURATION_SECONDS - timer_seconds
        
        # If result is negative (timer > 1:40), it means we are in some weird state
        # or maybe Buy Phase extensions? Just clip to 0 for safety.
        elapsed_since_start = max(0, elapsed_since_start)
        
        return observed_timestamp - elapsed_since_start

    @staticmethod
    def seconds_to_fmt(seconds: float) -> str:
        """Convert total seconds to M:SS format string."""
        if seconds is None:
            return None
        m = int(seconds // 60)
        s = int(round(seconds % 60))
        if s == 60:
            m += 1
            s = 0
        return f"{m}:{s:02d}"

    def detect_rounds(self, timer_readings: List[Dict]) -> List[Dict]:
        """
        Detect round boundaries from timer readings.
        
        Args:
            timer_readings: List of dicts with 'timestamp', 'timer_value', etc.
            
        Returns:
            List of detected rounds with start/end timestamps
        """
        rounds = []
        current_round = None
        spike_plant_time = None
        
        # State for tracking "nothing" sequence
        consecutive_nothings = 0
        first_nothing_timestamp = None
        
        # Sort readings by timestamp
        sorted_readings = sorted(timer_readings, key=lambda x: x['timestamp'])
        
        for i, reading in enumerate(sorted_readings):
            timestamp = reading['timestamp']
            
            # Handle dict or string timer value
            if isinstance(reading.get('timer_value'), dict):
                timer_str = reading['timer_value'].get('timer')
                has_red_triangle = reading['timer_value'].get('red_triangle', False)
            else:
                timer_str = reading.get('timer_value')
                has_red_triangle = False
            
            # --- Check for "nothing" sequence ---
            
            # Filter out broadcast replays that appear as random mid-round times after "nothing"
            # If we see a time like 1:29-0:31 immediately after "nothing", it's likely a replay
            if consecutive_nothings > 0 and timer_str != "nothing":
                t_secs = self.parse_timer(timer_str)
                # 1:29 is 89s, 0:31 is 31s
                if t_secs is not None and 31 <= t_secs <= 89:
                    timer_str = "nothing"

            if timer_str == "nothing":
                if consecutive_nothings == 0:
                    first_nothing_timestamp = timestamp
                consecutive_nothings += 1
                
                # If we have seen "nothing" consistently and a round is active, end it
                if current_round and consecutive_nothings >= self.ROUND_END_NOTHING_THRESHOLD:
                    # End the round at the START of the "nothing" sequence
                    current_round['end_timestamp'] = first_nothing_timestamp
                    current_round['end_time_fmt'] = self.seconds_to_fmt(first_nothing_timestamp)
                    current_round['end_reason'] = 'timer_disappeared'
                    rounds.append(current_round)
                    current_round = None
                    spike_plant_time = None
                    # We don't continue looking for start/spike in this reading
                continue # Skip the rest of processing for this "nothing" frame
                
            else:
                # Valid timer or spike planted -> reset "nothing" tracker
                consecutive_nothings = 0
                first_nothing_timestamp = None

            
            # Check for round start
            if self.is_round_start_timer(timer_str):
                # Calculate refined start time
                refined_start_time = self.calculate_round_start_timestamp(timestamp, timer_str)
                
                # If there's a current round, end it
                # We interpret a new round start detection as a hard boundary
                if current_round:
                    # Enforce that new round starts AFTER previous round ends?
                    # Or just cut the previous round.
                    end_time = max(
                        current_round['start_timestamp'],
                        refined_start_time - self.ROUND_END_BUFFER_SECONDS
                    )
                    current_round['end_timestamp'] = end_time
                    current_round['end_time_fmt'] = self.seconds_to_fmt(end_time)
                    current_round['end_reason'] = 'next_round_started'
                    rounds.append(current_round)
                
                # Start new round
                current_round = {
                    'round_number': len(rounds) + 1,
                    'start_timestamp': refined_start_time,
                    'start_time_fmt': self.seconds_to_fmt(refined_start_time),
                    'observed_start_timestamp': timestamp,
                    'start_timer': timer_str,
                    'end_timestamp': None,
                    'end_time_fmt': None,
                    'end_reason': None,
                    'spike_planted': False,
                    'spike_plant_timestamp': None
                }
                spike_plant_time = None
            
            # Check for spike plant (red triangle or text "spike planted")
            # Note: parse_vision_response might return "spike planted" string
            is_spike_text = (timer_str == "spike planted")
            
            if current_round and (has_red_triangle or is_spike_text) and not current_round['spike_planted']:
                current_round['spike_planted'] = True
                current_round['spike_plant_timestamp'] = timestamp
                spike_plant_time = timestamp
            
            # Check if spike timer expired (35 seconds after plant)
            if current_round and spike_plant_time:
                time_since_plant = timestamp - spike_plant_time
                
                # If 35 seconds passed since spike plant, end the round
                if time_since_plant >= self.SPIKE_TIMEOUT_SECONDS:
                    current_round['end_timestamp'] = timestamp
                    current_round['end_time_fmt'] = self.seconds_to_fmt(timestamp)
                    current_round['end_reason'] = 'spike_timeout'
                    rounds.append(current_round)
                    current_round = None
                    spike_plant_time = None
        
        # Close any remaining round
        if current_round:
            # Use last reading timestamp as end
            last_timestamp = sorted_readings[-1]['timestamp']
            current_round['end_timestamp'] = last_timestamp
            current_round['end_time_fmt'] = self.seconds_to_fmt(last_timestamp)
            current_round['end_reason'] = 'vod_ended'
            rounds.append(current_round)
        
        # Calculate durations
        for round_data in rounds:
            if round_data['end_timestamp']:
                round_data['duration'] = round_data['end_timestamp'] - round_data['start_timestamp']
        
        return rounds
    
    def save_rounds(self, rounds: List[Dict], output_file: Path):
        """Save detected rounds to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(rounds, f, indent=2)
        print(f"💾 Saved {len(rounds)} detected rounds to: {output_file}")
    
    def generate_round_clips(self, rounds: List[Dict], output_file: Path):
        """
        Generate clip timestamps for each round (for creating YouTube clips).
        
        Args:
            rounds: List of detected rounds
            output_file: Path to save clip data
        """
        clips = []
        
        for round_data in rounds:
            clip = {
                'round_number': round_data['round_number'],
                'start_time': round_data['start_timestamp'],
                'start_time_fmt': round_data.get('start_time_fmt'),
                'end_time': round_data['end_timestamp'],
                'end_time_fmt': round_data.get('end_time_fmt'),
                'duration': round_data.get('duration', 0),
                'spike_planted': round_data['spike_planted']
            }
            clips.append(clip)
        
        with open(output_file, 'w') as f:
            json.dump(clips, f, indent=2)
        
        print(f"🎬 Generated {len(clips)} round clips")
        return clips
    
    def print_round_summary(self, rounds: List[Dict]):
        """Print a human-readable summary of detected rounds."""
        print("\n" + "="*80)
        print(f"ROUND DETECTION SUMMARY - {len(rounds)} Rounds Detected")
        print("="*80 + "\n")
        
        for round_data in rounds:
            print(f"Round {round_data['round_number']}:")
            print(f"  Start: {round_data['start_timestamp']:.1f}s (Timer: {round_data['start_timer']})")
            print(f"  End:   {round_data['end_timestamp']:.1f}s (Reason: {round_data['end_reason']})")
            print(f"  Duration: {round_data.get('duration', 0):.1f}s")
            
            if round_data['spike_planted']:
                print(f"  Spike: Planted at {round_data['spike_plant_timestamp']:.1f}s")
            else:
                print(f"  Spike: Not planted")
            print()


def main():
    """CLI for testing round detection on existing timer readings."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Detect Valorant round boundaries from timer readings'
    )
    parser.add_argument(
        'timer_readings',
        type=str,
        help='Path to timer_readings.json file'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output file for detected rounds (default: rounds.json in same dir)'
    )
    
    args = parser.parse_args()
    
    # Load timer readings
    with open(args.timer_readings, 'r') as f:
        timer_readings = json.load(f)
    
    print(f"📊 Loaded {len(timer_readings)} timer readings")
    
    # Detect rounds
    detector = RoundDetector()
    rounds = detector.detect_rounds(timer_readings)
    
    # Print summary
    detector.print_round_summary(rounds)
    
    # Save results
    if args.output:
        output_path = Path(args.output)
    else:
        input_path = Path(args.timer_readings)
        output_path = input_path.parent / "rounds.json"
    
    detector.save_rounds(rounds, output_path)
    
    # Generate clips
    clips_path = output_path.parent / "round_clips.json"
    detector.generate_round_clips(rounds, clips_path)


if __name__ == '__main__':
    main()
