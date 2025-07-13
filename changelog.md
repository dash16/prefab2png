# Changelog

## [v0.6.2] - 2025-07-13
**Release Date:** 2025-07-13

### Added
- POI dots now use accurate prefab center positions based on size metadata from `.xml` files.
- Difficulty tiers now parsed directly from individual prefab XMLs (`<property name="DifficultyTier" ...>`).
- Legend rendering now supports complete POI ID → Display Name listings, especially in `--numbered-dots` mode.

### Fixed
- Duplicate POI_IDs in `legend_entries` no longer overwrite each other (now uses list, not dict).
- `--numbered-dots` mode now renders correct POI_IDs in the legend.
- Removed leftover bounding box debug layer.
- Patched unbound variable error in `render_category_layer`.

### Removed
- Deprecated `diff.csv` difficulty mapping. All difficulty data is now sourced from prefab XMLs in the game directory!

## [0.6.1] - Green for launch
**Release Date:** 2025-07-12
### Added
- New `--mask` CLI flag to enable red/blue label zone logic.

### Changed
- Green zone logic is now default (formerly behind `--no-mask`).
- Red zone behavior only triggers when `--mask` is set.

### Fixed
- POI_ID fallback rendering now matches green zone logic.
- Bounding box debug CSV output is now optional (can be commented out cleanly).

### Deferred
- Wedge label styling (bubble/pin)
- Legend code refactor
- Bounding box visualizer

## v0.6 – "Legendary"
**Release Date:** 2025-07-10

### ✨ New Features
- Updated visuals on Legend, added title, shaded bounding box that snaps to the labels written
- Automatic legend layout with 4-column support and overflow handling
- All log files now include the version number inline
- Output folder names now include all relevant flags (`--no-mask`, `--skip-layers`, etc.)
- Render time displayed at end of run (`🕒 Render completed in X.XX seconds`)
- `Config` class moved into `helper.py` for clean modular CLI parsing

### ✅ Bug Fixes
- Fixed `output/` folder duplication due to hardcoded path
- Fixed `--skip-layers` logic and output naming
- Fixed legend entries overlapping the `"Legend"` title

### 🛠 Improvements
- `bounding_boxes.csv` and `excluded_prefabs.txt` now include version headers
- Legend entries are sorted by POI_ID for better readability

### ✨ Added
- **Bounding box tracker** for every successfully placed label
  - Captures POI ID, layer, and bounding box dimensions
  - Outputs to `output/bounding_boxes.csv` after render
- New red zone awareness groundwork:
  - Future label placements can avoid overlap using this data
  - Enables automatic `mask.gif` generation without heatmap
- Label exclusions:
  - `player_starts` and `streets` no longer influence green zone logic or collision checks

### 🧰 Internal
- `labeler.py`: tracks and exposes `placed_bounding_boxes`
- `render.py`: appends bounding box data for successful placements
- `main.py`: handles CSV export at end of render

## [v0.5.5] - 2025-07-09

### 🛠️ Internal Cleanup

- Finalized centralization of all verbose-mode logs to `logs/` subdirectory
- Fixed `AttributeError` from missing `verbose_log_file` after refactor
- Log file initialization and version tagging now handled in `main.py`
- Removed stale path assignments from `parse.py` that could lead to incorrect log locations
- Added `prefab2png version` metadata line to `verbose_log.csv` for traceability

## [v0.5.4] - 2025-07-09

### 🐛 Fixed
- **Wedge labels no longer render redundant POI dots** — the dot is now drawn only on the `_points.png` layer
- **Green zone debug log file only generated when `--verbose` is enabled**, preventing empty file clutter
- **All successfully placed wedge labels are now logged to `verbose_log.csv`**, not just fallbacks or special cases
- **Output directory name is now dynamically constructed** based on CLI flags and timestamp	 
  (e.g., `output----no-mask--verbose__2025-07-09_1221`)

### 📁 Output Directory Behavior
- New folders are named based on flags used, preserving full CLI-style names
- Example: `main.py --numbered-dots --no-mask` → `output----numbered-dots--no-mask__2025-07-09_1221`
- Prior folders are untouched, making test comparisons easier

### 📊 Logging Behavior
- `verbose_log.csv` includes every POI with a successfully placed wedge label, restoring previous behavior
- Skipped POIs and legend fallbacks remain logged as before
- `player_starts` still receive special-case logging if included

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
