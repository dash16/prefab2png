# Data Sources

## prefabs.xml
- **Role:** World placements of prefabs (name, position, rotation).
- **Default paths:**
  - **macOS (Navezgane):** `~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Worlds/Navezgane/prefabs.xml`
  - **Windows (Navezgane):** `C:\Program Files (x86)\Steam\steamapps\common\7 Days To Die\Data\Worlds\Navezgane\prefabs.xml`
- **Source:** Per‑world (Navezgane default; RWG/Pregen generated in the world save).
- **Notes:** Rotation is corrected at render time using `rotation_to_north` + tile/slot orientation.

## LocalizationPOIs.txt
- **Role:** Maps internal prefab names → Display Names.
- **Default paths:**
  - **macOS:** `~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Config/Localization.txt`
  - **Windows:** `C:\Program Files (x86)\Steam\steamapps\common\7 Days To Die\Data\Config\LocalizationPOIs.txt`
- **Notes:** Missing/dupe handling is logged when `--log-missing` is set.


## Prefabs directory (`--prefab-dir`, alias `--blocks` [deprecated])
- **Role:** Prefab assets for sticker generation (top‑down “satellite” renders).
- **Contents:** `.tts`, `.blocks.nim`, `.xml`, `.jpg`, `.ins`, `.mesh` (we primarily use `.tts` + `.blocks.nim`).
- **Default paths:**
  - **macOS:** `~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Prefabs`
  - **Windows:** `C:\Program Files (x86)\Steam\steamapps\common\7 Days To Die\Data\Prefabs`
- **Used by:** `make_stickers.py` (not the main POI label render).
- **Output contract:** Stickers are written to `stickers__{YYYY-MM-DD_HHMM}` (downstream expects `/stickers*`).
Sticker output is for visual fidelity. The sticker pipeline pairs .tts with .blocks.nim to produce top‑down prefab images which provide environmental texture on the map. These outputs are not filtered by label denylist rules.

## blocks.xml
- **Role:** Block definitions used for color/lookups in some paths.
- **Default paths:**
  - **macOS:** `~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Config/blocks.xml`
  - **Windows:** `C:\Program Files (x86)\Steam\steamapps\common\7 Days To Die\Data\Config\blocks.xml`
- **Important:** **Does not contain block IDs**; IDs must be resolved from prefab-local data (`.tts`, `.xml`, `.ins`).
- **Project stance:** Treat the above as authoritative.

### Terrain Files

These files are read directly from the world directory to build the terrain base layer in `generate_terrain_map.py`.

- **`dtm.raw`**  
  - **Role:** Heightmap for the world terrain. Used to compute hillshading and relief in the final base layer.  
  - **Default paths:**  
    - **macOS:** `~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Worlds/<WorldName>/dtm.raw`  
    - **Windows:** `C:\Program Files (x86)\Steam\steamapps\common\7 Days To Die\Data\Worlds\<WorldName>\dtm.raw`

- **`splat3.png`**  
  - **Role:** Splat/paint map defining surface coverage (roads, dirt, gravel, water, POI footprint, etc.). Used to add subtle surface and road cues to the terrain base layer.  
  - **Default paths:**  
    - **macOS:** `~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Worlds/<WorldName>/splat3.png`  
    - **Windows:** `C:\Program Files (x86)\Steam\steamapps\common\7 Days To Die\Data\Worlds\<WorldName>\splat3.png`

- **`biomes.png`**
  - **Role:** Background coloring + biome categorization for layers.
  - **Default paths:**
    - **macOS (Navezgane):** `~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Worlds/Navezgane/biomes.png`
    - **Windows (Navezgane):** `C:\Program Files (x86)\Steam\steamapps\common\7 Days To Die\Data\Worlds\Navezgane\biomes.png`
- **RWG:** Must be provided via `--biomes` (no auto path, Navezgane file will be used instead!).
- **Notes:** Lower-res is acceptable; dimensions must match render grid.

## mask.gif (optional)
- **Role:** Label placement guide (red = never, blue = reserved, green = preferred).
- **Modes:**
  - Default: green‑zone placement with red/blue as fallback.
  - `--mask`: **use red/blue only**; skip green‑zone logic.
- **Notes:** Blue‑zone support is evolving; RWG clusters are denser and may require more curated blue zones.
