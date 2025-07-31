# prefab2png

![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)
![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)
![Release](https://img.shields.io/badge/release-v0.5-green.svg)
![Pillow](https://img.shields.io/badge/made%20with-Pillow-yellow.svg)
![GitHub issues](https://img.shields.io/github/issues/dash16/prefab2png)

This Python script renders layered map images from game files used by the game **7 Days to Die**. It creates layers of labeled points of interest (POIs) using in-game data, suitable for editing or display.

**Version:** v0.6.2
**Author:** Dustin Newell  
**License:** AGPL-3.0

---

## Overview

This script converts the `prefabs.xml` file from a 7 Days to Die world into layered `.png` maps. Each layer shows a category of prefabs—organized by biome, street, or player start location.  This script focuses on Navezgane, but could be easily adapted for any world map.

Prefab POIs with in-game names are included. Decorations, filler assets, and unnamed POIs are excluded. `player_start` and named street sign locations are also included.

prefab2png now uses **difficulty tier values from prefab metadata** directly. No external CSV is required.

Each POI dot is color-coded:
- Tier 0: Brown
- Tier 1: Orange
- Tier 2: Yellow
- Tier 3: Green
- Tier 4: Blue
- Tier 5: Purple

Untiered POIs default to red.

## New in v0.6.2
-📍 Accurate POI Centering! POI dot placement is based on the prefab’s actual size (via the `Extents` value in `.xml`). This ensures center-aligned dot rendering even on large prefabs like Trader compounds or cities.

---

## New in v0.6
- 🎨 Improved POI legend with tier-based color coding
- 🧱 Cleaner CLI and dynamic output folders
- 📄 Logs now include prefab2png version info
- 🚀 Renders now complete in ~10 seconds with better placement logic


## 🔧 Features

- 🧩 Modular codebase: easier to extend, test, and debug
- ⚡ Up to 10× faster rendering due to placement optimizations
- 🗺️ Renders 6145x6145 PNG layers
- 🎨 Color-coded prefab difficulty dot, label and line (via `diff.csv`)
- 📍 Text labels showing Display Names for each prefab, with overlap avoidance and connector lines
  - 🧼 Legend only shows skipped labels (not all POIs)
- 🧹 Prefab filtering with built-in exclusions and biome categorization
- ✍️ Smart green zone placement with vertical, horizontal, and diagonal fallback (default)
  - Smart label placement with red zone prohibition, blue zone targeting with green zone > legend fallback(--mask CLI flag)
- 🔎 Verbose logging and display name fallback
- 📍Unique `POI_ID` markers rendered on the map (optional via `--numbered-dots`)
- 📁 Output directory includes points, labels, and optionally combined layers
- 📝 Logs POI_ID, prefab name, display name, tier, color, and placement status in `verbose_log.txt`

---

## 🚀 Usage

```bash
python3 prefab2png.py \
  --xml /path/to/prefabs.xml \
  --localization /path/to/Localization.txt \
  --biomes /path/to/biomes.png \
  --combined \
  --with-player-starts \
  --log-missing \
  --verbose \
  --skip-layers \
  --no-mask \ 
  --only-biomes \

```
## 🖥️ Requirements

- Python 3.7+
- Pillow

### Required Files:
- `diff.csv` – Optional, maps prefab names to difficulty tiers

These files are part of the 7 Days to Die default installation, however you may need to specify their path if you are using a non-standard install path.
- `prefabs.xml` – From the world directory (e.g., Navezgane)
- `Localization.txt` – From game data path
- `biomes.png` – Used to identify biome per prefab

---

## 📦 Output

Default output directory: `output/`

### Output Directory Naming

The script now generates unique output folders automatically based on the CLI flags you use.

Examples:
- `main.py --no-mask` → `output--no-mask__2025-07-09_1030`
- `main.py --numbered-dots --combined` → `output--numbered-dots--combined__2025-07-09_1115`

This makes it easier to track test renders and compare variants.

Contents:
- `biome_forest_points.png`, etc. – Prefab dots per biome
- `..._labels.png` – Label overlays
- `combined/` – Optional combined PNG per category and all layers

### 🔍 Verbose Logging Output

When you run the script with the `--verbose` flag, additional debug files are written to the output directory:

| File						   | Description |
|------------------------------|-------------|
| `verbose_log.csv`			   | Logs every POI with its `POI_ID`, prefab name, display name, tier (if available), color, and placement status. Includes both rendered and skipped labels. Useful for reviewing what was drawn and why. |
| `green_zone_debug.txt`	   | Diagnostics related to green zone label placement. Shows attempted positions and rejection reasons. Helpful for troubleshooting why a label was placed far from a dot or skipped entirely. Only generated if `--verbose` is used. |
| `excluded_prefabs.txt`	   | Logs any prefabs filtered out by name/category logic, useful for debugging exclusions. |
| `missing_display_names.txt`  | *(optional)* List of prefab names that had no corresponding display name in `Localization.txt`. Generated if `--log-missing` is enabled. |

These logs can be used to analyze placement behavior, inspect rejected POIs, or verify that difficulty tiers and display names are correctly applied.

---

## Changelog

See [changelog.md](changelog.md) for version history and notes.

---

## License

This project is licensed under the [GNU AGPL v3](LICENSE).	It is not affiliated with or endorsed by The Fun Pimps.

---

Enjoy mapping the apocalypse! 🧟🗺️
