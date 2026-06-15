#!/usr/bin/env python3
"""
Spike script to validate player path extraction.
Extracts and prints player coordinates over time for a given Steam64.

Usage:
    python spike_extract_player_path.py path/to/demo.dem <steam64>
"""

import sys
import argparse
from pathlib import Path

try:
    import awpy
except ImportError:
    print("Error: awpy is not installed. Install with: pip install awpy")
    sys.exit(1)


def extract_player_path(demo_path: str, steam64: str) -> None:
    """Extract and print player path data."""
    demo_file = Path(demo_path)
    
    if not demo_file.exists():
        print(f"Error: Demo file not found: {demo_path}")
        sys.exit(1)
    
    print(f"Extracting path for Steam64: {steam64}")
    print(f"Demo: {demo_file.name}")
    print("-" * 80)
    
    try:
        # Load the demo
        demo = awpy.Demo(str(demo_file))
        
        # Find player by steam64
        target_player = None
        player_name = None
        
        if hasattr(demo, "players"):
            for player in demo.players:
                if player is not None and player.get("steam64") == steam64:
                    target_player = player
                    player_name = player.get("name", "Unknown")
                    break
        
        if target_player is None:
            print(f"Error: Player with Steam64 {steam64} not found in demo")
            print("\nAvailable players:")
            if hasattr(demo, "players"):
                for player in demo.players:
                    if player is not None:
                        print(f"  {player.get('name', 'Unknown'):20} | {player.get('steam64', 'Unknown')}")
            sys.exit(1)
        
        print(f"Found player: {player_name}")
        print()
        
        # Extract frames and build path data
        path_data = []
        tick_rate = demo.tick_rate if hasattr(demo, "tick_rate") else 64
        tick_duration = 1.0 / tick_rate
        
        if hasattr(demo, "frames"):
            print(f"Processing {len(demo.frames)} frames...")
            print()
            
            round_num = 0
            last_round = -1
            freeze_end_ticks_per_round = {}  # Will store freeze end tick for each round
            
            for frame_idx, frame in enumerate(demo.frames):
                if frame is None:
                    continue
                
                tick = frame.get("tick", frame_idx) if hasattr(frame, "get") else frame_idx
                
                # Track round changes
                current_round = frame.get("roundNum") if hasattr(frame, "get") else 0
                if current_round != last_round:
                    round_num = current_round
                    last_round = current_round
                
                # Extract player position if available
                if hasattr(frame, "player_states"):
                    for player_state in frame.player_states:
                        if player_state is not None:
                            player_steam64 = player_state.get("steamID") or player_state.get("steam64")
                            
                            if player_steam64 == steam64:
                                pos_x = player_state.get("x")
                                pos_y = player_state.get("y")
                                pos_z = player_state.get("z")
                                alive = player_state.get("alive", True)
                                velocity = player_state.get("velocity")
                                
                                if pos_x is not None and pos_y is not None:
                                    time_seconds = tick * tick_duration
                                    path_data.append({
                                        "tick": tick,
                                        "round": round_num,
                                        "time": time_seconds,
                                        "x": pos_x,
                                        "y": pos_y,
                                        "z": pos_z,
                                        "alive": alive,
                                        "velocity": velocity,
                                    })
        
        # Print results
        if path_data:
            print(f"Extracted {len(path_data)} position samples")
            print()
            print("First 20 path samples:")
            print(f"{'Tick':<8} {'Round':<6} {'Time':<10} {'X':<12} {'Y':<12} {'Z':<10} {'Alive':<8} {'Velocity':<10}")
            print("-" * 80)
            
            for entry in path_data[:20]:
                print(
                    f"{entry['tick']:<8} {entry['round']:<6} {entry['time']:<10.2f} "
                    f"{entry['x']:<12.1f} {entry['y']:<12.1f} {entry['z']:<10.1f} "
                    f"{str(entry['alive']):<8} {str(entry.get('velocity', 'N/A')):<10}"
                )
            
            if len(path_data) > 20:
                print(f"... and {len(path_data) - 20} more samples")
            
            print()
            print(f"✓ Path extraction successful!")
            print(f"Total samples: {len(path_data)}")
            print(f"X range: {min(p['x'] for p in path_data):.1f} to {max(p['x'] for p in path_data):.1f}")
            print(f"Y range: {min(p['y'] for p in path_data):.1f} to {max(p['y'] for p in path_data):.1f}")
            
        else:
            print("Warning: No path data found. Check if player was active in demo.")
        
    except Exception as e:
        print(f"Error extracting path: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Spike script to extract player path data"
    )
    parser.add_argument("demo_path", help="Path to CS2 .dem file")
    parser.add_argument("steam64", help="Steam64 ID of target player")
    
    args = parser.parse_args()
    extract_player_path(args.demo_path, args.steam64)


if __name__ == "__main__":
    main()
