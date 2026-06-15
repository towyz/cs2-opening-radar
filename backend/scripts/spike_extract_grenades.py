#!/usr/bin/env python3
"""
Spike script to validate grenade extraction.
Extracts and prints grenade throws for a given Steam64.

Usage:
    python spike_extract_grenades.py path/to/demo.dem <steam64>
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

try:
    import awpy
except ImportError:
    print("Error: awpy is not installed. Install with: pip install awpy")
    sys.exit(1)


def classify_grenade_type(weapon_name: Optional[str]) -> str:
    """Classify grenade type from weapon name."""
    if weapon_name is None:
        return "unknown"
    
    weapon_lower = weapon_name.lower()
    
    if "smoke" in weapon_lower:
        return "smoke"
    elif "flash" in weapon_lower or "flashbang" in weapon_lower:
        return "flash"
    elif "hegrenade" in weapon_lower or "he" in weapon_lower:
        return "he"
    elif "molotov" in weapon_lower:
        return "molotov"
    elif "incendiary" in weapon_lower:
        return "incendiary"
    else:
        return "unknown"


def extract_grenades(demo_path: str, steam64: str) -> None:
    """Extract and print grenade data."""
    demo_file = Path(demo_path)
    
    if not demo_file.exists():
        print(f"Error: Demo file not found: {demo_path}")
        sys.exit(1)
    
    print(f"Extracting grenades for Steam64: {steam64}")
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
        
        # Extract grenades
        grenades = []
        tick_rate = demo.tick_rate if hasattr(demo, "tick_rate") else 64
        tick_duration = 1.0 / tick_rate
        
        # Try to extract from grenades if available
        if hasattr(demo, "grenades"):
            grenades_list = demo.grenades if isinstance(demo.grenades, list) else []
            print(f"Processing grenades from demo data...")
            
            for grenade in grenades_list:
                if grenade is None:
                    continue
                
                thrower_steam64 = grenade.get("throwerSteamID") or grenade.get("thrower_steam64")
                
                if thrower_steam64 == steam64:
                    grenade_type = classify_grenade_type(grenade.get("weapon"))
                    throw_tick = grenade.get("tick")
                    
                    throw_x = grenade.get("throwX") or grenade.get("x")
                    throw_y = grenade.get("throwY") or grenade.get("y")
                    throw_z = grenade.get("throwZ") or grenade.get("z")
                    
                    detonate_x = grenade.get("detonateX") or grenade.get("detonX")
                    detonate_y = grenade.get("detonateY") or grenade.get("detonY")
                    detonate_z = grenade.get("detonateZ") or grenade.get("detonZ")
                    
                    grenades.append({
                        "type": grenade_type,
                        "tick": throw_tick,
                        "time": throw_tick * tick_duration if throw_tick else None,
                        "throw_x": throw_x,
                        "throw_y": throw_y,
                        "throw_z": throw_z,
                        "detonate_x": detonate_x,
                        "detonate_y": detonate_y,
                        "detonate_z": detonate_z,
                        "weapon": grenade.get("weapon"),
                    })
        
        # Print results
        if grenades:
            print(f"Found {len(grenades)} grenades thrown by player")
            print()
            print("Grenade data:")
            print(f"{'Type':<12} {'Tick':<10} {'Time':<10} {'Throw X':<12} {'Throw Y':<12} {'Detonate X':<12} {'Detonate Y':<12}")
            print("-" * 100)
            
            for grenade in grenades:
                throw_x = grenade.get("throw_x")
                throw_y = grenade.get("throw_y")
                det_x = grenade.get("detonate_x")
                det_y = grenade.get("detonate_y")
                
                time_str = f"{grenade.get('time', 0):.2f}" if grenade.get('time') else "N/A"
                throw_x_str = f"{throw_x:.1f}" if throw_x is not None else "N/A"
                throw_y_str = f"{throw_y:.1f}" if throw_y is not None else "N/A"
                det_x_str = f"{det_x:.1f}" if det_x is not None else "N/A"
                det_y_str = f"{det_y:.1f}" if det_y is not None else "N/A"
                
                print(
                    f"{grenade.get('type'):<12} {grenade.get('tick', 'N/A'):<10} {time_str:<10} "
                    f"{throw_x_str:<12} {throw_y_str:<12} {det_x_str:<12} {det_y_str:<12}"
                )
            
            print()
            print("✓ Grenade extraction successful!")
            
            # Print statistics
            type_counts = {}
            for g in grenades:
                gtype = g.get("type", "unknown")
                type_counts[gtype] = type_counts.get(gtype, 0) + 1
            
            print(f"\nGrenade statistics:")
            for gtype, count in sorted(type_counts.items()):
                print(f"  {gtype}: {count}")
        
        else:
            print("Warning: No grenades found. Player may not have thrown any grenades.")
        
    except Exception as e:
        print(f"Error extracting grenades: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Spike script to extract grenade data"
    )
    parser.add_argument("demo_path", help="Path to CS2 .dem file")
    parser.add_argument("steam64", help="Steam64 ID of target player")
    
    args = parser.parse_args()
    extract_grenades(args.demo_path, args.steam64)


if __name__ == "__main__":
    main()
