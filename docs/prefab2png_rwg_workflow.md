
# 🧭 prefab2png Workflow: Generating a Fully Labeled Map of an RWG World

> This guide outlines a step-by-step workflow for generating terrain maps with overlaid prefab stickers, POI dots, labels, and legend using the `prefab2png` toolset.

---

## 🔹 Step 1: Prepare Your Files

Collect the following files locations from your 7DTD RWG world directory:

| File | Description | Location |
|------|-------------|----------|
| `dtm_processed.raw` | 16-bit terrain heightmap (6144×6144) | Savegames > World directory |
| `biomes.png` | RGB biome map | Savegames > World directory |
| `splat3_processed.png` | Road data |  Savegames > World directory |
| `prefabs.xml` | Contains POI names and coordinates |  Savegames > World directory |
| `blocks.xml` | Contains map.color and tintcolor values used to draw accurate pixels in prefabs | ../Data/Config directory |
| `Localization.txt` | Maps internal prefab names to display names | ../Data/Config directory |
| `*.xml` (Prefabs) | Metadata for prefab size and difficulty | ../Data/Prefabs directory |
| `*.tts` (Prefabs) | Block layout for top-down rendering | ../Data/Prefabs directory |
| `*.blocks.nim` | Block ID → Name mappings per prefab | ../Data/Prefabs directory |
| `mask.gif` (optional) | Red/blue zone placement guide | Navezgane example included in this repository |

---

## 🔹 Step 2: Render Terrain Background

```bash
python3 generate_terrain_map.py
```

- Applies biome shading, hillshade, contours, and road overlays
- Produces:
  ```
  output_terrain_<timestamp>/
  └── terrain_biome_shaded_final.png
  ```

---

## 🔹 Step 3: Make Prefab Stickers

```bash
python3 make_stickers.py --prefab-dir /path/to/prefabs
```

- Uses `.tts` and `.blocks.nim` files into colored top-down PNGs with the assistance of `blocks.xml` and some default color categories for blocks who don't have color defined.
- Produces:
  ```
  output_stickers_<timestamp>/
  ├── trader_rekt.png
  ├── house_old_01.png
  └── ...
  ```

---

## 🔹 Step 4: Overlay Stickers onto the Terrain

```bash
python3 place_stickers.py --xml /path/to/xml --biomes /path/to/biomes --prefab-dir /path/to/prefabs
```

- Loads `terrain_biome_shaded_final.png` from `output_terrain_*` and pastes prefab renders
- Centers each prefab based on size and coordinates
- Rotates correctly to align with splatmap
- Produces:
  ```
  output--<version>--.../
  ├── sticker_rwg_tiles_only.png
  ├── stickers_only.png
  └── sticker_overlay.png
  ```

---

## 🔹 Step 5: Render POI Dots, Labels, and Legend

```bash
python3 main.py --xml /path/to/prefabs.xml --biomes /path/to/biomes.png
```

**Optional flags:**

| Flag | Description |
|------|-------------|
| `--numbered-dots` | Show POI_IDs instead of names, render legend |
| `--log-missing` | Log prefabs without display names |
| `--only-biomes desert snow` | Limit to selected biomes |

- Produces:
  ```
  output--<version>--<flags>__<timestamp>/
  ├── biome_desert_labels.png
  ├── combined/map_all_layers_combined.png
  ├── poi_legend.png
  ├── sticker_overlay.png
  └── logs/
      ├── verbose_log.csv
      └── missing_display_names.txt
  ```

---

## ✅ Summary

### Final Outputs:
- `map_all_layers_combined.png`: labeled dots and wedge boxes
- `sticker_overlay.png`: prefab visuals on terrain
- `poi_legend.png`: searchable display names and POI IDs
- Full set of layer images and logs

Use this workflow for **RWG worlds**.

