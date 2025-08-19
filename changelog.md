# 📜 Changelog

This file tracks version history for `prefab2png`.  Previous Changelog in docs/

# 0.7.3 — Polish and Documentation Pass
**Release Date:** 2025-08-19

### Added
- New documentation files:
  - **architecture.md**  — module structure + data flow diagrams
  - **cli.md** — command-line flags and usage guide
  - **data-sources.md** — required inputs and where to find them
  - **layers-and-styles.md**  — visual layers, styling, and exclusions
  - **placement.md** — full label/POI/tile placement order of operations
  - **render-modes.md** — render modes, flags, and outputs
  
### Changed
- Sticker render is now less noisy — console prints are gated behind `--verbose`.

### Fixed
- Resolved duplicate messages printing to console/logs.

### Removed
 - **sticker_render.py** - deprecated, all rendering performed in `make_stickers.py`.

## 0.7.2 - 2025-08-08
### Added
- Pixel perfect placement for all POI tiles, whether placed directly on map or embedded in an RWG tile.
- ⏱️ Render timer for `place_stickers` (prints total time; also written to verbose log if enabled).

### Changed
- Logging simplified (KISS): removed shared logger; `place_stickers` writes debug to file only.
- “Resolved paths” prints now appear once on startup (no duplicates).

### Fixed
- Killed duplicate path prints from multiple `Config(...)` constructions.
- Gated `sticker_debug_log.csv` so it’s created only with `--verbose`.
- Silenced stray `print` in `get_rotation_to_north` that spammed console.

## v0.7.1 – RWG Tile Sticker Rendering + Rotation Normalization  
**Release Date:** 2025-08-06

### Added
- Support for rendering RWG world tiles (`rwg_tile_*.tts`) as top-down stickers
- Renders are saved as transparent PNGs to `stickers__YYYY-MM-DD_HHMM/` (timestamped)
- PNGs are aligned bottom-center for consistent placement over terrain
- Automatically rotates RWG tile stickers so they face North, based on:
  - `POIMarkerPartRotations` parsing
  - Inferred placement during render pass
  - Global flip rules and authored tile exclusions
- Improved block color parsing for visual fidelity:
  - Prioritizes `Map.Color` from `blocks.xml`
  - Falls back to `TintColor`
  - Uses semantic name-based coloring when no color defined

### Excluded
- POI rotation correction inside RWG tiles (still under active development)