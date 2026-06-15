#!/usr/bin/env python3
"""
Spike script to validate basic demo parsing capabilities.
Prints demo metadata, player list, and round information.

Usage:
    python spike_parse_demo.py path/to/demo.dem
"""

import sys
import argparse
from pathlib import Path

try:
    import awpy
except ImportError:
    print("Error: awpy is not installed. Install with: pip install awpy")
    sys.exit(1)


def parse_demo(demo_path: str) -> None:
    """Parse and print demo information."""
    demo_file = Path(demo_path)
    
    if not demo_file.exists():
        print(f"Error: Demo file not found: {demo_path}")
        sys.exit(1)
    
    if not demo_file.suffix.lower() == ".dem":
        print("Error: File must be a .dem file")
        sys.exit(1)
    
    print(f"Parsing demo: {demo_file.name}")
    print("-" * 80)
    
    try:
        # Load the demo
        demo = awpy.Demo(str(demo_file))
        
        # Print metadata
        print("\n[METADATA]")
        print(f"Map: {demo.map}")
        print(f"Tick Rate: {demo.tick_rate if hasattr(demo, 'tick_rate') else 'Unknown'}")
        print(f"Demo File: {demo_file.name}")
        
        # Print game info
        if hasattr(demo, "header"):
            print(f"Protocol: {demo.header.protocol if hasattr(demo.header, 'protocol') else 'Unknown'}")
        
        # Print players
        print("\n[PLAYERS]")
        if hasattr(demo, "players"):
            for player in demo.players:
                if player is not None:
                    name = player.get("name", "Unknown")
                    steam64 = player.get("steam64", "Unknown")
                    team = player.get("team", "Unknown")
                    print(f"  {name:20} | Steam64: {steam64:20} | Team: {team}")
        else:
            print("  No player data available")
        
        # Print rounds summary
        print("\n[ROUNDS]")
        if hasattr(demo, "rounds"):
            print(f"Total Rounds: {len(demo.rounds)}")
            
            # Print first few rounds as sample
            for i, round_data in enumerate(demo.rounds[:min(3, len(demo.rounds))]):
                print(f"\nRound {i + 1}:")
                if round_data is not None:
                    print(f"  Type: {round_data.get('roundType', 'Unknown')}")
                    print(f"  Winner: {round_data.get('winner', 'Unknown')}")
                    if hasattr(round_data, "t_kills"):
                        print(f"  T Kills: {round_data.t_kills}")
                    if hasattr(round_data, "ct_kills"):
                        print(f"  CT Kills: {round_data.ct_kills}")
        else:
            print("  No round data available")
        
        # Print frame sample
        print("\n[FRAME SAMPLE]")
        if hasattr(demo, "frames"):
            frame_count = len(demo.frames) if hasattr(demo.frames, "__len__") else "Unknown"
            print(f"Total Frames: {frame_count}")
            
            # Print first frame info
            if len(demo.frames) > 0:
                first_frame = demo.frames[0]
                print(f"\nFirst Frame:")
                print(f"  Tick: {first_frame.get('tick', 'Unknown') if hasattr(first_frame, 'get') else 'Unknown'}")
        else:
            print("  No frame data available")
        
        print("\n" + "-" * 80)
        print("✓ Demo parsed successfully!")
        print("\nNext steps:")
        print("  1. Use spike_extract_player_path.py to extract player coordinates")
        print("  2. Use spike_extract_grenades.py to extract grenade data")
        
    except Exception as e:
        print(f"Error parsing demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Spike script to validate demo parsing capabilities"
    )
    parser.add_argument("demo_path", help="Path to CS2 .dem file")
    
    args = parser.parse_args()
    parse_demo(args.demo_path)


if __name__ == "__main__":
    main()
