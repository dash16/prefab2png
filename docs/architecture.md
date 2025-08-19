# Architecture

## Overview

Prefab2png is organized into modular scripts and helpers that work together to:
1. Parse world and prefab data.
2. Apply filters, categorization, and label placement rules.
3. Render PNG map layers and composites.

Two main execution paths:
- **Main POI Render (`main.py`)**  
  Generates layered PNG outputs for Points of Interest, with optional composite map.
- **Sticker Render (`make_stickers.py`)**  
  Generates top-down "satellite" PNGs for each prefab from `.tts` + `.blocks.nim`.

---
## Architecture Overview (ASCII)

                         ┌────────────────────────────────────────────────────────┐
                         │                      DATA SOURCES                      │
                         │  • prefabs.xml             • LocalizationPOIs.txt      │
                         │  • biomes.png              • dtm.raw                   │
                         │  • splat3.png              • Prefabs dir (.tts, .xml,  │ 
                         │										.blocks.nim, ...) │
                         └───────────────┬──────────────────────────┬─────────────┘
                                         │                          │
                                  (A) Terrain Base              (B) Sticker Renderer
                                   generate_terrain_map.py       make_stickers.py
                                         │                          │
                                         ▼                          ▼
                         ┌────────────────────────────────┐   ┌─────────────────────────────┐
                         │  generate_terrain_map.py       │   │  make_stickers.py           │
                         │  - load biomes.png             │   │  - scan Prefabs dir         │
                         │  - read dtm.raw → hillshade    │   │  - parse .tts/.blocks.nim   │
                         │  - read splat3.png → surface   │   │  - block parsing/classify   │
                         │  - compose terrain_base.png    │   │  - render per‑prefab PNGs   │
                         └─────────────────┬──────────────┘   └───────────────┬─────────────┘
                                           │                                  │
                                           │                                  ▼
                                           │                      /stickers__YYYY‑MM‑DD_HHMM/*
                                           │                                  │
                                           ▼                                  │
                               ┌────────────────────┐                         │
                               │   terrain_base.png │◄────────────────────────┘
                               └─────────┬──────────┘
                                         │
                              (C) POI Label Map Pipeline
                                         │
                                      main.py
                                         │
                                         ▼
                           ┌─────────────────────────────┐
                           │          parse.py           │
                           │  - read prefabs.xml         │
                           │  - coords/rotation fixes    │
                           └───────────┬─────────────────┘
                                       │
                           ┌───────────▼───────────┐
                           │       filters.py      │   (LABEL SCOPE ONLY)
                           │  - should_exclude()   │   *does not affect stickers/texture*
                           │  - layer/category     │
                           └───────────┬───────────┘
                                       │
                           ┌───────────▼───────────┐
                           │       labeler.py      │
                           │  - green/blue/red     │
                           │  - nudge & wedges     │
                           └───────────┬───────────┘
                                       │
                           ┌───────────▼───────────┐
                           │       render.py       │
                           │  - per‑layer PNGs     │
                           │  - optional composite │
                           └───────────┬───────────┘
                                       │
                     ┌─────────────────▼──────────────────┐
                     │  place_stickers.py                 │
                     │  - load terrain_base.png           │
                     │  - place/rotate prefab stickers    │
                     │  - merge with label layers         │
                     └───────────────┬────────────────────┘
                                     │
                   ┌─────────────────▼────────────────────────┐
                   │        FINAL OUTPUTS                     │
                   │  • /layers/* (labeled map layers)        │
                   │  • combined.png (terrain/stickers/labels)│
                   └──────────────────────────────────────────┘

### Support modules
- **helper.py**: path resolution (macOS/Windows), coord transforms, RWG rotation helpers.
- **block_parser.py / block_analysis.py**: prefab block parsing & classification used by the sticker renderer.

---

## Module Reference

### `main.py`
- **Purpose:** Entry point for generating labeled POI maps from `prefabs.xml` + supporting data.
- **Inputs:**  
  - `prefabs.xml` (world)  
  - `LocalizationPOIs.txt` (display names)  
  - `biomes.png` (background + categorization)  
  - Optional: `mask.gif` for label placement zones
- **Outputs:**  
  - One PNG per layer (e.g., traders, streets, biome-specific)  
  - Optional combined composite PNG
- **Notes:** Handles CLI parsing, config setup, and orchestrates the render pipeline.

### `make_stickers.py`
- **Purpose:** Render top-down prefab images (“stickers”) for use in map overlays.
- **Inputs:**  
  - `.tts` + `.blocks.nim` (Prefab data) from prefab directory  
  - Optional: `--blocks` / `--prefab-dir` to override auto path
- **Outputs:**  
  - PNGs saved to `stickers__{YYYY-MM-DD_HHMM}` (pipeline expects `/stickers*`)
- **Notes:** Uses block classification and color mapping; can be verbose.

### `parse.py`
- **Purpose:** Parse `prefabs.xml` into prefab objects with name, coordinates, rotation, and size.
- **Outputs:** Structured prefab list for rendering.
- **Notes:** Calls `should_exclude()` to skip unwanted prefabs.

### `filters.py`
- **Purpose:** Categorize prefabs into layers (e.g., `streets`, `traders`, biome-specific).
- **Notes:** Uses prefab names, biomes, and denylist patterns.
- **Scope:** All exclusion and categorization rules in filters.py (e.g., should_exclude) apply to labels and named POIs only. These rules do not remove or hide visual “texture” content. The sticker renderer exists to add richness (detritus, parts, tiles) and should not be constrained by label-focused filters.

### `labeler.py`
- **Purpose:** Place labels for POIs without overlap, using green/blue/red zone logic.
- **Notes:**  
  - Green-zone logic uses vertical/horizontal/diagonal nudging.  
  - Blue/red zones loaded from `mask.gif` if provided.  
  - Connector “wedge” style available for labels.

### `render.py`
- **Purpose:** Draw dots, labels, connector wedges, and output PNGs.
- **Notes:** Handles both per-layer and composite renders; legend generation in `main.py`.

### `helper.py`
- **Purpose:** Shared utilities for path resolution, coordinate transforms, exclusion rules, etc.
- **Notable:**  
  - `rotation_to_north` logic for aligning prefabs in RWG tiles.  
  - `should_exclude()` patterns for bridges, clutter, etc.  
  - Auto path resolution for macOS/Windows.

## generate_terrain_map.py

**Purpose:** Build the **base terrain/biome layer** used under stickers and labels by combining:
- biome coloring (`biomes.png`),
- terrain relief from a **processed height field** (`dtm_processed.raw`),
- road/surface accents from a **processed splatmap** (`splat3_processed.png`).

**Inputs:**
- **`biomes.png`** — categorical biome image (Navezgane auto‑path; **RWG must be provided via `--biomes`**).
- **`dtm_processed.raw`** — pre‑normalized height field for hillshading/relief.
  - Intended as a processed form of the game’s `dtm.raw` (orientation/scale normalized for our render grid).
  - Parsed as a grayscale height map and normalized to the map’s resolution (e.g. project grid: **6145×6145**).
- **`splat3_processed.png`** — pre‑processed splat/paint map for surface accents.
  - Derived from the game’s `splat3.png` (reprojected to our grid and cleaned).
  - RGBA channels represent relative coverage of terrain paints (e.g., asphalt/road, gravel, dirt, sand/snow); we use these to draw subtle surface features and especially **roads**.

**Outputs:**
- A single **terrain base PNG** with:
  - biome color as the base,
  - hillshade/relief from `dtm_processed.raw` applied (subtle multiply/overlay),
  - road/surface accents from `splat3_processed.png` (low‑alpha compositing).

**Processing (high level):**
1. **Load & scale** `biomes.png` to the canonical map resolution (upscale is OK; dimensions must match the render grid).
2. **Load `dtm_processed.raw`** and normalize heights to 0–1; compute a lightweight **hillshade** (gradient magnitude and/or azimuthal lighting), then blend it over the biome base to add terrain relief.
3. **Load `splat3_processed.png`**; decode channel intensities and composite **surface cues**:
   - A small, dark stroke for **roads/asphalt** where the relevant channel is strong.
   - Very light texture cues for paths/soil/sand where appropriate channels are present.
   - Keep opacity conservative so labels remain legible.
4. **Write** the final terrain PNG for use beneath **stickers** and **labels**.

**Notes & conventions:**
- **Processed assets:** We intentionally consume **`dtm_processed.raw`** and **`splat3_processed.png`** so that orientation, resolution, and dynamic range are already aligned to the map grid.
- **Resolution:** The terrain layer must match the main render canvas (**6145×6145**) so that prefab/sticker and POI coordinates line up.

### `block_analysis.py`
- **Purpose:** Classify block names into categories for coloring in sticker renders.
- **Notes:** Produces verbose `[CLASSIFY]` output; gated in future.

## block_parser.py
**Purpose:** Provide **safe, local** parsing utilities around prefab block data for sticker rendering—without assuming global block IDs.

**Why it exists:**  
`blocks.xml` **does not appear to contain block IDs**. IDs are prefab‑local (e.g., inside `.tts` / `.xml` / `.ins`).

**Inputs:**
- `.tts` (prefab top‑down slice definitions, with local block references)
- Optional prefab‑local `.xml` / `.ins` for name and extra metadata
- Global palette mapping block names → textures/colors

**Outputs:**
- Data structures used by the sticker renderer (e.g., a 2D top layer of block “tops”)
- Resolved **names** (not IDs) when assigning colors/textures

**Key behaviors & rules:**
- **No global ID inference:** Never derive `block_id → name` from `blocks.xml` index.
- Prefer **name‑based** matching (prefix/category patterns) when mapping to textures/colors.
- When `.blocks.nim` is present alongside `.tts`, use it only for **attributes/names**, not for assigning global numeric IDs.

**Typical flow (used by the sticker pipeline):**
1. Open `.tts`, read topmost layer’s blocks.
2. Resolve block names (locally) for those entries.
3. Map names to colors/textures (palette rules).
4. Return a 2D array of “block tops” for rendering.

**Notes / future work:**
- Tighten name→texture mapping against a curated CSV (prefix patterns).
- Surface mis‑matches as warnings (opt‑in verbosity).

## place_stickers.py

**Purpose:** Compose the “visual texture” layer by placing prefab **stickers** (top‑down renders) on the map at their world locations and rotations.

**Inputs:**
- `prefabs.xml` (world placements; name, position, rotation)
- Stickers from `/stickers__{YYYY-MM-DD_HHMM}/*` (generated by `make_stickers.py`)
- `LocalizationPOIs.txt` (for display names if labeling overlays are enabled)
- `biomes.png` (for background/base alignment)
- `--prefab-dir` (auto‑detected if omitted; alias `--blocks` is deprecated)

**Outputs:**
- A composited PNG (or layer set) with all prefab stickers placed in‑world
- Optional logs (paths resolved, counts, any missing sticker warnings)

**Key behaviors & rules:**
- **Anchor logic (stable baseline):**
  - Stickers are placed with **horizontal center** aligned to the POI, and their **bottom edge** aligned to the POI (so tall stickers “grow upward”)
  - Rotation: Uses rotation_to_north and RWG tile/slot orientation helpers (from helper.py) so RWG‑placed POIs match the game’s rotation.
  - Sticker discovery: Finds a matching PNG by prefab name (case/extension normalized). If missing, logs a warning and continues.
Label filters do NOT apply: This pipeline is texture-focused. Exclusions in `filters.py` are for labels/named POIs only and must not hide visual detritus/parts/tiles.

---

## Pipeline Highlights
- **POI flow:** `main.py` → `parse.py` → `filters.py` → `labeler.py` → `render.py`
- **Sticker flow:** `make_stickers.py` → `block_analysis.py` → PNGs in `/stickers*`
- **Shared:** `helper.py` functions for paths, transforms, exclusions, rotation correction.
