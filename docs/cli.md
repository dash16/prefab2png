# Command Line Interface Reference

This document lists all CLI arguments available in prefab2png.

## Arguments

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `--xml` | Path to `prefabs.xml` file for a given world, which describes placement and rotation of prefabs. | Auto-resolved to Navezgane path | `--xml /path/to/prefabs.xml` |
| `--blocks` | [DEPRECATED, use `--prefab-dir` instead] Path to .blocks.nim file or folder | Game install locations for Windows and Mac detected | `--blocks /path/to/prefabs/directory` |
| `--localization` | Path to 'Localization.txt', which maps POI names to Display Names | Game install locations for Windows and Mac detected | `--localization /path/to/Localization.txt` |
| `--biomes` | Path to 'biomes.png', which is used to color background map properly | Auto-resolved to Navezgane path, for RWG this must be specified | `--biomes /path/to/biomes.png` |
| `--prefab-dir` | Path to the game Prefabs directory (contains .tts, .blocks.nim, .xml, etc.). | Game install locations for Windows and Mac detected | `--prefab-dir /path/to/prefabs/directory` |
| `--numbered-dots` | Render POI_ID numbers instead of standard dots. | Off, markers are written as dots colored per POI Tier level  | `--numbered-dots` |
| `--verbose` | Enables verbose logging, which may fill console with **tens of thousands of lines** and create debug `.csv` files | Off, console output should be minimal and only necessary files are created | `--verbose` |
| `--combined` | Generate an additional combined PNG layers of map + label + marker | Off, separate layer files are generated | `--combined` | 
| `--with-player-starts` | Include 'player_starts' layer which shows possible spawn locations. | Off, no player_starts layer | `--with-player-starts` |
| `--log-missing` | Log the prefabs placed on the map which are missing a known Display Name. | Off, no log file created| `--log-missing` |
| `--skip-layers` | Skip rendering biome layers and go directly to legend rendering. [DEBUG, consider deprecating] | Off, all layers are rendered | `--skip-layers` |
| `--mask` | Enable red/blue zone label placement from mask.gif ONLY (Green Zone Logic skipped) | Off, green zone placement with red/blue zone fallback. | `--mask` |
| `--only-biomes` | Only render the specified biome layers. Options: pine_forest, desert, snow, burnt_forest, wasteland. | Off, all biomes are rendered. | `--only-biomes snow wasteland` |
| `--version` | Show the current prefab2png version and exit | Off | `--version` |
| `--extended-placement-debug` | Visually highlight labels placed during extended placement (Pass 4) | Off, all labels render with no additional context | `--extended-placement-debug` |
|  `--text-size` | Font size for POI labels. (25 - 60) | Off, default is 25 | `--text-size 45` |
| `--output` | Output path or folder for rendered voxel PNGs | Off, default folder locations are used | `--output /path/to/desired/output/folder` |


## Interactions

- **`--prefab-dir` vs `--blocks` (deprecated)**
  - `--blocks` is an alias for the same Prefabs directory path.
  - If both are provided, **`--prefab-dir` wins**; `--blocks` is ignored (and is slated for removal later).

- **`--xml` + `--biomes`**
  - Navezgane defaults are auto‑resolved; **RWG worlds require `--biomes`** (no auto path).
  - If `--biomes` is missing for RWG, background coloring will be incorrect/missing.

- **`--mask` (zone control)**
  - When on, **use the red/blue mask** for label placement and **skip “green‑zone” logic**.
  - When off, use green‑zone placement with red/blue as a fallback (project default behavior).

- **`--numbered-dots` (POI_ID mode)**
  - Suppresses wedge/text label rendering; **renders POI_ID boxes instead of dots**.
  - Legend behavior changes: legend entries reflect **all POI_IDs**, not just skipped labels.
  - Does **not** increase font size for higher tiers; traders are not treated specially.

- **`--combined` (output set)**
  - Adds a **composite PNG** (map + labels + markers); does **not** replace per‑layer outputs.

- **`--with-player-starts`**
  - Enables the **`player_starts`** layer (spawn candidates). No effect on other layers.

- **`--only-biomes` + `--skip-layers`**
  - `--only-biomes` filters which biome layers render.
  - If `--skip-layers` is set, biome layers are skipped entirely; therefore **`--skip-layers` overrides `--only-biomes`**.

- **`--text-size`**
  - Clamped between **25–60**. Does not scale by tier. Large values can reduce placement opportunities in dense areas.

- **`--log-missing`**
  - Emits a report of prefabs missing a Display Name mapping. Independent of `--verbose`.

- **`--version`**
  - Prints the current prefab2png version and **exits immediately** (ignores other flags).

