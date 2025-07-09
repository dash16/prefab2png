# Changelog

## [v0.5.3] - 2025-07-08

### ✨ Added
- Legend layout now supports 4 columns (2 left, 2 right) to accommodate large POI counts

### 🐛 Fixed
- `--numbered-dots` mode:
  - Suppresses display name labels and wedges
  - Renders POI_IDs directly on the map with white roundrects
  - Ensures full 1:1 POI_ID → Display Name mapping in the legend
  - Correctly applies tier-based color styling to each legend entry
- `--with-player-starts` now correctly suppresses the `player_starts` layer unless explicitly enabled
- Empty PNGs for prefab categories with 0 POIs are no longer written to disk
- Duplicate biome filtering logic removed from the render loop

### 🎨 Improved
- Legend entries are styled with tier-colored text and rounded white backgrounds
- Top/bottom wedge widths are clamped to avoid oversized connector triangles

## 📦 v0.5.2 — Green Zone Labeling Overhaul (2025-07-07)

### ✨ Added
- Full support for **green zone wedge labels** with white shaded connector logic
- Smart **nudge-based label placement** for green zones:
  - Vertical → Horizontal → Diagonal fallback
  - Skips avoided in most scenarios
- Labels now **avoid overlapping POI dots** (dot radius + stroke buffer respected)
- Labels skew slightly when placed via green zone, creating space for visible wedges
- Logging pipeline added:
  - `--verbose` writes label placement logs to `output/green_zone_debug.txt`
  - Easily extendable for future `--label-debug` flag

### 🎨 Improved
- Wedge drawing now integrated for both green and blue zone labels
- Label box padding now consistent and visually aligned
- Label collision logic restored and improved after regression in v0.5.1
- `dot_centers` now passed through to assist in POI-aware label placement
- Refactored logging to remove global state (`debug_log`) and inject `log()` cleanly

### 🐛 Fixed
- Fixed regression where wedge padding was misaligned
- Restored label box width and height accuracy after font bbox tuning
- Resolved duplicate label artifacts in overlapping POIs

### 🧩 Known Issues (To be resolved in v0.6)
- `--with-player-starts` flag not respected
- `--numbered-dots` does not render POI_IDs
- Green zone labels can occasionally spill into blue zone regions in ultra-dense areas
- Wedge shape becomes too wide for top/bottom placements
- POI dot still placed at prefab’s lower-left corner instead of center

## v0.5.1
- Improved green zone label placement:
  - Introduced vertical-first nudging with red/blue zone avoidance
  - Added horizontal fallback if vertical fails
  - Added diagonal fallback if both vertical and horizontal fail
- Reduced skipped labels from 118 → 14 with negligible performance impact
- Labels now avoid overlapping each other and red zones more reliably
- POI_ID fallback labels (for skipped entries) now use green zone logic
- POI_ID fallback boxes include background + connector line to dot
- Added `--no-mask` flag to bypass label mask for modded/RNG worlds
- Updated `verbose_log.txt` to save as `.csv`
- Refined logic to exclude `player_starts` and `streets` from label constraints and legend

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
