# Changelog

## v0.5

- Modularized project structure:
  - `main.py`, `render.py`, `labeler.py`, `filters.py`, `parse.py`
- Improved label placement logic:
  - Prefers blue zones, avoids red, snaps to left edge
  - Stacks labels without overlap
- Accurate legend behavior:
  - Skipped POIs only appear in `poi_legend.png`
  - Debug mode (`--skip-layers`) shows placeholder entry
- Removed fallback label placement that violated collision rules
- Full verbose logging: rendered vs. skipped POIs
- Visual improvements:
  - Background shading in legend zones
  - Two-column layout with right overflow
- Performance improvements:
  - Label placement is fast even in large zones
- Cleaned up legacy code and false starts
- Simplified mask file, `prefab_label_mask_optimized.gif` is now `mask.gif`

## v0.4.3
- Overhauled label placement system using a `prefab_label_mask_optimized.gif` mask
- Introduced preferred blue zones for label snapping and stacking
- Labels now snap to the left edge of blue boxes and stack downward
- Labels fallback to POI_ID and appear in a new legend overlay when placement fails
- Connector lines and label text now color-match the POI difficulty tier
- Major performance improvements via blue zone caching
- Removed spiral search logic in favor of direct blue zone targeting
- Added support for `--skip-layers` flag to debug legend rendering independently
- Cleaned up line rendering logic and eliminated redundant draw calls
- Prepared groundwork for further modular code refactor (coming in v0.5)

## v0.4.2

- Introduced red/green label placement mask to reduce visual clutter and avoid map obstructions.
- Labels now avoid red zones during rendering, and skip placement entirely if no safe location can be found.
- Skipped labels are logged in `verbose_log.txt` with coordinates and prefab name.
- Final line in `verbose_log.txt` now includes a summary count of all label placement rejections.
- Cleaned up unused highlight label logic (`highlight_font`, `get_fonts()`).
- Included in this release is the file `prefab_label_mask_optimized.gif`, which defines safe label placement zones. This can be edited to exclude locations you don't want labels drawn in (red) and places it is safe to place a label (green).

### Known Issues
- ~151 POIs are not currently labeled due to red zone overlap and lack of fallback positioning logic.
- This is a temporary limitation; future versions will recover these labels using advanced placement strategies.

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
