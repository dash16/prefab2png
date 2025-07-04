# Changelog

## v0.4.1

- ✨ **POI ID Badges**  
  Every prefab now receives a unique ID (e.g. `P0123`) which is rendered directly on the map when `--numbered-dots` is used. IDs also appear in verbose logging to aid reference and analysis.
- 🧾 **Map-Based POI Legend**  
  A legend panel is dynamically rendered on the map's unused margins (left + right) showing every `POI_ID → Display Name` mapping. Automatically activated with `--numbered-dots`.
- 🔎 **Better Label Placement (v3-style fallback)**  
  Label collision detection now spirals outward to find open space before falling back to the default position. Cleaner labeling in dense prefab clusters.

## v0.4
- Full script modularization (Config, loader, parser, renderer)
- All global state moved into structured components
- Final output and logging logic isolated into helper functions
- Trader POIs are no longer treated with special attention — no more green dots, mega-fonts, or inflated egos. They're just red dots like everyone else who hasn't been assigned a difficulty tier. All it cost was Trader Joel’s hat… it was delicious.
- Ready for scalable development, testing, or CLI integration

## v0.3.3
- Restored label placement logic with overlap avoidance and connector lines
- Labels now appear offset from prefab dots with a connecting gray line
- Fixed issue where labels were overlapping or sitting directly on top of dots

## v0.3.2
- Fixed bug where `player_start` POIs were incorrectly rendered in biome layers when `--with-player-starts` was not set

## v0.3.1
- Fixed logic to categorize `sign_260` and `sign_73` under the `streets` layer
- Ensured tier 0 values from `diff.csv` are logged as `0`, not `None`
- Enhanced `verbose_log.txt` with a CSV header and new `layer` column for prefab layer tracking

## v0.3
- Initial public release.
- Licensed under AGPL-3.0
- Output folder simplified to `output/`
- Added biome-based prefab categorization
- Introduced color-coded difficulty from `diff.csv`
- Display name fallback + logging for missing names
- Optional player start and signage support
- Combined PNG rendering support
