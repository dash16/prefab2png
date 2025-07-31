# 📜 Changelog

This file tracks version history for `prefab2png`.  Previous Changelog in docs/

## v0.7.0 — RWG Sticker Support (First Pass)
**Release Date:** 2025-07-31

- Project structure updated
- Documentation moved to `docs/` folder
- Added full support for rendering individual PNG stickers from prefab folders
- make_stickers.py recursively scans subdirectories (e.g. POIs/, RWGTiles/) for .tts + .blocks.nim pairs
- Integrated render_top_blocks() to visualize topmost visible blocks with color from blocks.xml, name prefixes, and material categories earlier in the pipeline to optimize render times
- Introduced category-based color fallback when XML or alias data is missing
- Cleaned up legacy logic in block_analysis.py to focus on visible block IDs only
- Prepared foundation for RWG terrain overlays, prefab terrain stamping, and visual tile compositing in future versions
