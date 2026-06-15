# CS2 Opening Radar

CS2 Opening Radar is a demo analysis tool for extracting and visualizing a target player's opening behavior from CS2 demo files.

For the MVP, users manually provide a demo file, map name, and target Steam64 ID. The tool parses the demo, extracts the player's movement route and grenade usage within the first 30 seconds after freeze time ends, and visualizes the result on a 2D map radar.

## MVP Features

- Parse a single CS2 demo file
- Locate a target player by Steam64 ID
- Extract movement routes after freeze time ends
- Extract grenade throws, landing positions, and trajectories
- Visualize player routes on a 2D map
- Show a player summary card with round and grenade statistics

## Planned Features

- Multi-demo aggregation
- Opponent opening habit comparison
- Round type filters: pistol, eco, force buy, half buy, full buy
- Perfect World demo download integration
- Five-opponent pre-match scouting dashboard
