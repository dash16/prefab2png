# helper.py
# Shared utility functions used across labeler.py and render.py

# ----------------------------------------------
# 📌 Roadmap Notes (for future cleanup/refactor)
# ----------------------------------------------
# - Migrate wedge drawing functions from render.py:
#     • draw_label_wedge_only()
#     • draw_label_text_only()
# - Consider adding a shared bbox helper: get_text_dimensions()
# - Evaluate rgb_distance and biome utils for relocation
# - Ensure helper.py does not rely on category, prefab, or rendering context
# - Split label placement vs drawing logic cleanly
# - Optional: auto-generation of red/blue zones based on POI clustering (v0.6+)

from PIL import ImageFont

# ----------------------------------------------
# ✅ Bounding box + overlap logic
# ----------------------------------------------

def get_text_box(text, x, y, font, padding=4):
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    return (
        x - padding,
        y - padding,
        x + text_w + padding,
        y + text_h + padding
    )

def boxes_overlap(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])

def check_label_overlap(label_box, placed_boxes):
    return any(boxes_overlap(label_box, other) for other in placed_boxes)

def check_dot_overlap(label_box, poi_x, poi_y, radius=4):
    dot_box = (poi_x - radius, poi_y - radius, poi_x + radius, poi_y + radius)
    return boxes_overlap(label_box, dot_box)

# ----------------------------------------------
# ✅ Zone placement logic (mask-based)
# ----------------------------------------------

def is_placeable(label_box, label_mask, red_rgb):
    x0, y0, x1, y1 = map(int, label_box)
    width, height = label_mask.size

    # Clip box to within image bounds
    x0 = max(0, min(x0, width - 1))
    x1 = max(0, min(x1, width - 1))
    y0 = max(0, min(y0, height - 1))
    y1 = max(0, min(y1, height - 1))

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            r, g, b = label_mask.getpixel((x, y))
            if (r, g, b) == red_rgb:
                return False
    return True

# ----------------------------------------------
# ✅ POI_ID green zone label placement (used in --numbered-dots)
# ----------------------------------------------

def try_green_zone_label(text, base_x, base_y, font, mask, occupied_boxes, red_rgb):
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    pad = 4

    max_nudge = 4
    step = text_h + 2

    # Vertical
    for dy in range(1, max_nudge + 1):
        for offset in [-dy * step, dy * step]:
            lx = base_x - text_w // 2
            ly = base_y + offset - text_h // 2
            label_box = (lx - pad, ly - pad, lx + text_w + pad, ly + text_h + pad)
            if not is_placeable(label_box, mask, red_rgb): continue
            if check_label_overlap(label_box, occupied_boxes): continue
            return lx, ly, label_box

    # Horizontal
    for dx in range(1, max_nudge + 1):
        for offset in [-dx * (text_w + 8), dx * (text_w + 8)]:
            lx = base_x + offset - text_w // 2
            ly = base_y - text_h // 2
            label_box = (lx - pad, ly - pad, lx + text_w + pad, ly + text_h + pad)
            if not is_placeable(label_box, mask, red_rgb): continue
            if check_label_overlap(label_box, occupied_boxes): continue
            return lx, ly, label_box

    # Diagonal
    for i in range(1, max_nudge + 1):
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            lx = base_x + dx * (text_w + 10) - text_w // 2
            ly = base_y + dy * step - text_h // 2
            label_box = (lx - pad, ly - pad, lx + text_w + pad, ly + text_h + pad)
            if not is_placeable(label_box, mask, red_rgb): continue
            if check_label_overlap(label_box, occupied_boxes): continue
            return lx, ly, label_box

    return None  # Fallback: draw directly on dot
# ----------------------------------------------
# ✅ Prefab XML loader
# ----------------------------------------------

import xml.etree.ElementTree as ET

def load_prefabs_from_xml(xml_path):
    """
    Parses prefabs.xml and returns a list of (POI_ID, name, x, z) tuples.
    Supports prefabs defined using position="x,y,z" attribute.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    prefabs = []
    i = 0
    for elem in root.iter():
        name = elem.get("name")
        position = elem.get("position")
        if not name or not position:
            continue
        try:
            x, y, z = map(float, position.split(","))
            i += 1
            prefabs.append((f"POI_{i}", name, int(x), int(z)))
        except ValueError:
            continue
    print(f"✅ Found {len(prefabs)} prefab entries.")
    return prefabs

# ----------------------------------------------
# ✅ Prefab filter
# ----------------------------------------------

def should_exclude(name):
    if not name:
        return True
    name = name.lower()
    if name.startswith(("bridge", "wilderness_filler", "part_", "street_light", "diersville_city_sign", "cornfield_", "site_grave", "rwg_tile_")):
        return True
    if name.startswith("sign_") and not (name.startswith("sign_260") or name.startswith("sign_73")):
        return True
    return False
# ----------------------------------------------
# ✅ Normalize coordinates
# ----------------------------------------------    
def transform_coords(x, z, map_center=3072):
    cx = int(x + map_center if x >= 0 else map_center - abs(x))
    cz = int(map_center - z if z >= 0 else map_center + abs(z))
    return cx, cz