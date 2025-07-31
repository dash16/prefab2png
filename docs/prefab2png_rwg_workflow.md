
# 🧭 prefab2png Workflow: Generating a Fully Labeled Map of an RWG World

> This guide outlines the official step-by-step workflow for generating terrain maps with overlaid prefab stickers, POI dots, labels, and a searchable legend using the `prefab2png` toolset.

---

## 🔹 Step 1: Prepare Your Files

Collect the following files from your 7DTD RWG world directory:

| File | Description |
|------|-------------|
| `dtm_processed.raw` | 16-bit terrain heightmap (6144×6144) |
| `biomes.png` | RGB biome map |
| `splat3_processed.png` | Road data (optional but recommended) |
| `prefabs.xml` | Contains POI names and coordinates |
| `Localization.txt` | Maps internal prefab names to display names |
| `*.xml` (Prefabs) | Metadata for prefab size and difficulty |
| `*.tts` (Prefabs) | Block layout for top-down rendering |
| `*.blocks.nim` | Block ID → Name mappings per prefab |
| `mask.gif` (optional) | Red/blue zone placement guide |

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

## 🔹 Step 3: Render Prefab Stickers from .tts Files

```bash
python3 tts_decode.py --batch --verbose-csv
```

- Converts all `.tts` files into colored top-down PNGs
- Matches `.blocks.nim` to assign semantic colors
- Produces:
  ```
  output_stickers_<timestamp>/
  ├── trader_rekt.png
  ├── house_old_01.png
  ├── ...
  └── *_blockmap_named.csv
  ```

---

## 🔹 Step 4: Overlay Stickers onto the Terrain

```bash
python3 place_stickers.py
```

- Loads `terrain_biome_shaded_final.png` and pastes prefab renders
- Centers each prefab based on size and coordinates
- Produces:
  ```
  output--<version>--.../
  └── sticker_overlay.png
  ```

---

## 🔹 Step 5: Render POI Dots, Labels, and Legend

```bash
python3 main.py --mask --with-player-starts --combined --verbose
```

**Optional flags:**

| Flag | Description |
|------|-------------|
| `--numbered-dots` | Show POI_IDs instead of names |
| `--log-missing` | Log prefabs without display names |
| `--only-biomes desert snow` | Limit to selected biomes |
| `--no-mask` | Use green zone fallback (ignore `mask.gif`) |

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

Use this workflow for **RWG or modded worlds**. Run once with `--no-mask` to visualize raw placement, then iterate with `mask.gif` to refine.

