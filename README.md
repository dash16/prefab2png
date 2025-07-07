# prefab2png

![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)
![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)
![Release](https://img.shields.io/badge/release-v0.4-green.svg)
![Pillow](https://img.shields.io/badge/made%20with-Pillow-yellow.svg)
![GitHub issues](https://img.shields.io/github/issues/dash16/prefab2png)

This Python script renders layered map images from game files used by the game **7 Days to Die**. It creates layers of labeled points of interest (POIs) using in-game data, suitable for editing or display.

**Version:** 0.4.2
**Author:** Dustin Newell  
**License:** AGPL-3.0

---

## Overview

This script converts the `prefabs.xml` file from a 7 Days to Die world into layered `.png` maps. Each layer shows a category of prefabs—organized by biome, street, or player start location.  This script focuses on Navezgane, but could be easily adapted for any world map.

Prefab POIs with in-game names are included. Decorations, filler assets, and unnamed POIs are excluded. `player_start` and named street sign locations are also included.

Prefab difficulty tiers (0–5) are color-coded based on an optional `diff.csv` file.

---

## 🔧 Features

- 🧩 Modular codebase: easier to extend, test, and debug
- ⚡ Up to 10× faster rendering due to placement optimizations
- 🗺️ Renders 6145x6145 PNG layers
- 🎨 Color-coded prefab difficulty dot, label and line (via `diff.csv`)
- 📍 Text labels showing Display Names for each prefab, with overlap avoidance and connector lines
  - 🧼 Legend only shows skipped labels (not all POIs)
- 🧹 Prefab filtering with built-in exclusions and biome categorization
- ✍️ Smart label placement with blue zone targeting
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

Contents:
- `biome_forest_points.png`, etc. – Prefab dots per biome
- `..._labels.png` – Label overlays
- `combined/` – Optional combined PNG per category and all layers

---

## Changelog

See [changelog.md](changelog.md) for version history and notes.

---

## License

This project is licensed under the [GNU AGPL v3](LICENSE).  It is not affiliated with or endorsed by The Fun Pimps.

---

Enjoy mapping the apocalypse! 🧟🗺️
