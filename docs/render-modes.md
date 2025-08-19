# Render Modes

This doc explains **what** each mode draws, **how** it draws, and the **CLI flags** to reach it.  
Examples use `prefab2pngdev.py` (dev workflow) and assume macOS paths.

---

## Overview

Prefab2png can render multiple visual “modes,” each controlling **what** we draw (POI dots, wedge labels, numbered boxes, RWG tile stickers, etc.) and **how** we layer + style them. You can render any mode as separate PNG layers and optionally output a combined image.

---

## Quick Reference (What each mode draws)

| Mode | What you see | Typical Use |
|---|---|---|
| **POI Map (default)** | POI dots + wedge labels (if placeable), legend for skips | General map with readable names |
| **Numbered Dots (`--numbered-dots`)** | Every POI as a **POI_ID** box; legend lists **all** POI_ID → Display Name | Dense maps, print-friendly index |
| **Stickers (RWG Tiles)** | Tile/POI **stickers** aligned to splatmaps; pixel-perfect rotation | Satellite/terrain-style context layer |
| **Combined (`--combined`)** | One flattened image after all layers | Quick share/export |
| **Player Starts (`--with-player-starts`)** | Adds player starts layer | Spawn planning, docs |

---

## Common Flags

- `--xml <path>` – Path to `prefabs.xml` (world).
- `--biomes <path>` – Biome PNG (e.g., Navezgane `biomes.png`).
- `--localization <path>` – `Localization.txt` (POI display names).
- `--prefab-dir <path>` – Folder where prefab `.tts/.xml` live (for size/aux data).
- `--numbered-dots` – Switch to POI_ID rendering mode.
- `--with-player-starts` – Include player spawn markers.
- `--combined` – Save a merged final output.
- `--verbose` – Emit richer debug logs in the output directory.

---

## Default: POI Map (Dots + Wedge Labels)

### What it draws
- **POI dot layers** (by category/biome as configured).
- **Wedge labels** for POIs that can be placed legally.
- **Legend** for any labels that were skipped.

### Label placement summary
- **Default path (no `mask.gif`)** → **Green zone** logic only.
- **With `mask.gif`** → Try **Blue zone** first, then **Green zone**.
- **Green zone passes**: vertical → horizontal → diagonal → **retry all at 2×**. If still blocked, label is skipped and listed in the legend.

### Example
```bash
python3 prefab2pngdev.py   --xml "/path/to/prefabs.xml"   --localization "/path/to/Localization.txt"   --biomes "/path/to/biomes.png"
```

---

## Numbered Dots Mode (`--numbered-dots`)

### What it draws
- Every POI renders as a **POI_ID box** on the map (boxes follow the same placement-avoidance rules, prioritizing legibility).
- The **legend includes every POI_ID → Display Name** (all POIs, not just skipped items).
- Useful for **dense cities**.

### Notes
- Keeps label sizes consistent.
- Current legend layout uses **4 columns** (2 left, 2 right).

### Example
```bash
python3 prefab2pngdev.py   --xml "/path/to/prefabs.xml"   --localization "/path/to/Localization.txt"   --biomes "/path/to/biomes.png"   --numbered-dots   --combined
```

---

## RWG Tile Stickers (Terrain Context)

### What it draws
- Renders **stickers** for RWG tiles (and tile-placed POIs) with **pixel-perfect rotation**:
  - Correctly detects RWG **tile slots**.
  - Applies **rotation_to_north** and tile orientation.
  - Aligns with **splatmaps** (roads, sidewalks, terrain) exactly.

### Use cases
- **Background context** layer under labels.
- Verifying **rotation fidelity** and alignment.

> **Placement anchor for stickers**: horizontally centered on the POI and **bottom-aligned** to the POI position (center-bottom anchor).

### Example
```bash
python3 place_stickers.py   --xml "/path/to/prefabs.xml"   --prefab-dir "/path/to/Prefabs"
```

---

## Player Starts (`--with-player-starts`)

Adds a “player starts” layer to the output.  

```bash
python3 prefab2pngdev.py   --xml "/path/to/prefabs.xml"   --with-player-starts
```

---

## Combined Output (`--combined`)

Saves a **flattened** final image after all layers.  
Good for quickly sharing a single file, while separate layers remain available.

```bash
python3 prefab2pngdev.py   --xml "/path/to/prefabs.xml"   --combined
```

---

## Mask Behavior

- Default behavior (off):  
  - **Green zone** logic only.  
  - No blue zone snapping.  
- **`mask.gif` present**:  
  - Try **Blue zone** first (snap-left + vertical wrap if needed).  
  - Fall back to **Green zone** passes.  
  - **Red zones** are always respected (never place labels here).

```bash
python3 prefab2pngdev.py --xml "/path/to/prefabs.xml"
```

---

## Exclusions & Layering Notes

- Exclusions reduce noise (wilderness fillers, street lights, rubble, craters, roadblocks, etc.).  
  Special allowlist keeps `sign_260*` and `sign_73*` in **streets**.
- Traders are treated **like any other POI** (no special emphasis).
- Draw order ensures **text is on top** of wedges (wedge pass first, text pass second).

---

## Output Folder & Logging

- Output folder names include flags and a timestamp (e.g., `output--verbose__YYYY-MM-DD_hhmm`).
- Verbose runs write supplemental logs (e.g., **green zone** and **blue zone** diagnostics).

```bash
python3 prefab2pngdev.py --xml "/path/to/prefabs.xml" --verbose
```

---

## Roadmap / Planned Enhancements

- **Wedge aesthetics**: refined shaded wedges + rounded label boxes.
- **Bounds & Heatmap**: POI bounds logging + independent density heatmap (`heatmap.py`).
- **CLI polish**: stricter arg validation + `--help`.

---
