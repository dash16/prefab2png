# Placement Logic

This document describes how placement works for labels, POIs, and RWG tiles in the prefab2png pipeline.  
Each category follows its own rules, with multiple fallbacks to ensure readability and alignment.

---

## Label Placement

Labels are the trickiest element to place because they must remain legible without overlapping each other or obscuring map features.

### Zone Types
- **Green Zones** – Default placement areas.  
  Labels first attempt to nudge **vertically** (up/down). If blocked, they try **horizontal** (left/right). If still blocked, they attempt **diagonal** placement.  If still blocked, all previous directions are tried once more at 2x distance.
  If no valid space is found, the label is skipped and written to legend instead.
- **Blue Zones** – Reserved areas for dense clusters or special alignment.  Defined by mask.gif (Navezgane, RWG worlds will need their own custom mask.)
  - Labels snap **left-aligned** against the zone edge.  
  - If the label text is too wide, it **wraps vertically** without breaking or hyphenating words.  
  - Used primarily to keep city labels consistent and aligned.
- **Red Zones** – Forbidden areas.  
  - Labels can never be placed here.  
  - These are drawn in the `mask.gif` to represent high-density or restricted map regions.

By default labels use green zone logic, but if a mask.gif is provided they first attempt blue zone placement.

### Order of Operations when using mask.gif
1. Attempt placement in a nearby **Blue Zone** (if available).
2. If no valid Blue Zone, attempt **Green Zone** nudging logic.
3. Always avoid collisions with:
   - POI dots (the location markers themselves),
   - Previously placed labels,
   - Any Red Zone defined in `mask.gif`.

### Special Handling
- Debug files (`green_zone_debug.txt`) record attempted placements and rejections.
- In `--numbered-dots` mode:
  - Labels become **POI_ID boxes** instead of text names.
  - Placement still respects green/blue zone logic to avoid overlaps.

---

## RWG Tile Placement

RWG tiles represent the **foundation grid** of a random world generation (RWG) map.

### Base Position
- Tiles are square (usually 150×150 blocks).
- Positions come from `prefabs.xml`, snapped to grid coordinates.

### Rotation
- Each tile has a rotation applied:
  - Global alignment via `rotation_to_north`,
  - Local rotation as defined in the world XML.
- Certain hand-authored tiles are exceptions and may be handled with exclusion rules.

### Purpose
- RWG tiles provide the **street layouts, terrain transitions, and city blocks**.
- Prefabs placed within these tiles inherit both the **tile position** and **tile rotation** so that roads, sidewalks, and buildings line up exactly with the terrain.

---

## POI (Prefab) Placement

POIs are placed as stickers at the locations specified in `prefabs.xml`.

### POI Dot Placement
- When running labeler.py, `prefabs.xml` is used to look up prefab locations to place a highlighted, Tier-colored dot on the center of the POI to pair with the label.

### Direct Placement
- POI positions are read from `prefabs.xml` coordinates.
- Orientation is adjusted using:
  - `rotation_to_north` (the prefab’s default),
  - Any prefab-specific `rotation` stored in the XML entry.

### RWG Tile Placement
- If a prefab is placed **inside an RWG tile**, its position and rotation are relative to the tile.
- Rotation combines the prefab’s `rotation_to_north` with the parent tile’s rotation.
- This ensures **pixel-perfect alignment** with the splatmap (roads, terrain, paths, foliage, etc).

### Exclusions
Some prefabs are excluded from rendering **labels** to reduce noise:
- `aaa_` test prefabs
- Wilderness fillers
- Street lights
- Craters, rubble, and roadblocks
- Any prefab name containing:
  - `bridge`
  - `part_`
  - `street_light`
  - `diersville_city_`
  - `sign_`
  - `cornfield_`
  - `site_grave`
  - `wilderness_filler`
  - `rwg_tile_`

These prefabs are NOT skipped when rendering stickers, and may be placed on the background terrain map to add visual interest and complexity.

Special cases:  
- `sign_260*` and `sign_73*` are allow-listed into the **streets** layer.

---