# 📜 Changelog

This file tracks version history for `prefab2png`.  Previous Changelog in docs/

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