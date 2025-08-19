
# 📦 prefab2png Project Documentation

### Version: `v0.7.2`  
**Author:** Dustin Newell  
**Purpose:** Generate visual, labeled, and customizable map outputs from 7 Days to Die prefab, terrain, and biome data.

---

## 🧭 Overview

`prefab2png` is a modular map rendering pipeline for 7DTD that:

- Renders terrain from RAW biome and splat data
- Draws prefab POI dots, wedge-style labels, and legends
- Supports prefab difficulty tiers, prefab exclusions, label zones (red/blue/green)
- Overlays prefab previews rendered from `.tts` binary files

---

## 🧰 Modules

| File | Role |
|------|------|
| `main.py` | Central CLI + map rendering controller |
| `render.py` | Draws dots, labels, wedges for each POI |
| `labeler.py` | Places labels intelligently (green/blue zone logic) |
| `helper.py` | CLI args, font loading, paths, utility logic |
| `parse.py` | Loads display names, tiers, biome RGBs, prefab size/difficulty |
| `filters.py` | Filters out prefabs based on allow/deny rules.  Sets color palette on decoded voxel arrays. |
| `block_parser.py` | Decodes .blocks.nim and .tts files into usable structures |
| `block_analysis.py` | Analyzes prefab voxel data to identify visible blocks and group them into semantic categories |
| `make_stickers.py` | Parses /Data/Prefabs directory and renders "stickers" of all prefabs as viewed directly from above |
| `place_stickers.py` | Pastes prefab tiles onto terrain map, including RWG Tiles, Parts, and POIs |
| `generate_terrain_map.py` | Creates base terrain map with biomes, contours, and hillshade |

---

## 🧩 Module Descriptions

### `main.py`
- Loads input data and CLI arguments
- Parses prefabs, assigns POI IDs, filters exclusions
- Renders each category layer via `render.py`
- Applies blue/green/red zone logic via `labeler.py`
- Builds `poi_legend.png`, `combined/` output, and CSV logs

### `render.py`
- Draws dots by prefab tier (color-coded)
- Places labels using blue or green zone placement
- Renders wedge connectors and text boxes
- Handles Pass 4 fallback search (extended placement)

### `labeler.py`
- Smart label positioning with collision and mask logic
- Label wrapping, nudging (vertical, horizontal, diagonal)
- Blue zone label stacking + POI ID fallback

### `helper.py`
- Shared config and setup
- Resolves file paths (OS-aware)
- Loads fonts and image settings
- Implements CLI flags (e.g. `--combined`, `--with-player-starts`)

### `parse.py`
- Loads:
  - Display names from `Localization.txt`
  - Difficulty tiers for color
  - Biome image and RGB mapping
- Categorizes POIs into layers (`biome_*`, `streets`, etc.)
- Extracts prefab size and difficulty from prefab `.xml` files
- Detects blue zones from `mask.gif`

### `filters.py`
- Implements `should_exclude(name)` logic:
  - Denylist substrings: `"bridge"`, `"rwg_tile_"`, etc.
  - Skips noisy or dev/test prefabs
  - Allowlist override for `sign_260`, `sign_73`

### `block_parser.py`
- Reads `.blocks.nim` and `.tts` prefab data to create a labeled block map of prefab constructions.  `.blocks.nim` contains the mapping of block ID to block name.  `.tts` contains the physical layout of every block (including air) inside that prefab.
	- `.blocks.nim` binaries contain an 8-byte header, 4-byte block ID, 1-byte name length, followed by a UTF-8 string containing the name.  This pattern repeats until end of file.
	- `.tts` binaries contain a header, xyz values detailing the bounds of the prefab, and 32-bit block data (ID, flags)
- Expected file paths: ../Data/Prefabs
	
### `block_analysis.py`
- Sorts the data extracted from `block_parser.py`  A top-down view of the prefab is assembled.  Blocks are labeled and categorized for color mappings at render time.

### `place_stickers.py`
- Loads terrain from `terrain_biome_shaded_final.png`
- Loads prefab locations from `prefabs.xml`
- Loads `.png` stickers for each prefab
- Pastes onto terrain based on prefab center
- Logs missing prefab PNGs

### `generate_terrain_map.py`
- Reads:
  - `dtm_processed.raw` (heightmap)
  - `biomes.png` (biome type map)
  - `splat3_processed.png` (road overlay)
- Applies shading, elevation curves, contour lines
- Outputs:
  - `terrain_biome_shaded_final.png` (base for overlays)

---

## 📁 Expected Input Files

| Input Type | Location / Pattern |
|------------|--------------------|
| Heightmap | `dtm_processed.raw` |
| Biomes | `biomes.png` |
| Roads | `splat3_processed.png` |
| Prefab XML | `prefabs.xml` |
| Localization | `Localization.txt` |
| Prefab blocks | `.tts`, `.blocks.nim` |
| Label mask (opt) | `mask.gif` |

---

## 📤 Output Overview

| Type | Example Filename |
|------|------------------|
| Terrain | `terrain_biome_shaded_final.png` |
| POI layers | `biome_desert_points.png`, `streets_labels.png` |
| Combined | `map_all_layers_combined.png` |
| Prefab tiles | `trader_rekt.png` |
| CSV logs | `trader_rekt_blockmap_named.csv` |
| Legend | `poi_legend.png` |
| Logs | `excluded_prefabs.txt`, `verbose_log.csv` |
