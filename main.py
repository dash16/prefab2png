# main.py

from helper import Config, args
from parse import load_display_names, load_tiers, load_biome_image, extract_blue_zones
from filters import should_exclude
from render import render_category_layer
from labeler import (is_placeable, placed_bounding_boxes)
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from PIL import Image
import time
import datetime

LABEL_MASK_PATH = "mask.gif"
LABEL_MASK_RED = (165, 27, 27)
LABEL_MASK_GREEN = (0, 118, 0)
LABEL_MASK_BLUE = (0, 42, 118)

# === Logging Setup ===

def null_log(msg):
    pass

def create_logger(verbose):
    if verbose:
        os.makedirs(config.output_dir, exist_ok=True)
        log_file = open(os.path.join(config.log_dir, "green_zone_debug.txt"), "w")
        log_file.write(f"# prefab2png version: {version}\n")
        def log(msg):
            log_file.write(msg + "\n")
            log_file.flush()
        return log, log_file
    return null_log, None

# === Setup ===
config = Config(args)
start_time = time.time()
# Load version string from version.txt
try:
    with open("version.txt") as vf:
        version = vf.read().strip()
except FileNotFoundError:
    version = "unknown"

# === Build dynamic output folder name based on CLI flags ===
flag_parts = []

if args.numbered_dots:
    flag_parts.append("--numbered-dots")
if args.no_mask:
    flag_parts.append("--no-mask")
if args.with_player_starts:
    flag_parts.append("--with-player-starts")
if args.combined:
    flag_parts.append("--combined")
if args.skip_layers:
    flag_parts.append("--skip-layers")
if args.verbose:
    flag_parts.append("--verbose")

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
suffix = f"{''.join(flag_parts)}__{timestamp}" if flag_parts else timestamp

config.output_dir = f"output--{version}--{suffix}"
config.combined_dir = os.path.join(config.output_dir, "combined")
os.makedirs(config.output_dir, exist_ok=True)

if config.args.combined:
    os.makedirs(config.combined_dir, exist_ok=True)

if args.verbose or args.log_missing:
    config.log_dir = os.path.join(config.output_dir, "logs")
    os.makedirs(config.log_dir, exist_ok=True)
else:
    config.log_dir = None  # Prevent accidental use

if config.log_dir:
    config.verbose_log = os.path.join(config.log_dir, "verbose_log.csv")
    config.verbose_log_file = open(config.verbose_log, "w", encoding="utf-8")
    config.verbose_log_file.write(f"# prefab2png version: {version}\n")
    config.missing_log = os.path.join(config.log_dir, "missing_display_names.txt")
    config.excluded_log = os.path.join(config.log_dir, "excluded_prefabs.txt")
else:
    config.verbose_log = None
    config.verbose_log_file = None
    config.missing_log = None
    config.excluded_log = None

display_names = load_display_names(config.localization_path)
tier_colors, prefab_tiers = load_tiers()
biome_img = load_biome_image(config.biome_path, config.image_size)

# === Label Mask ===
label_mask = None
blue_zones = []

if args.no_mask:
    print("🚫 Skipping mask: --no-mask flag set.")
else:
    if os.path.exists(LABEL_MASK_PATH):
        label_mask = Image.open(LABEL_MASK_PATH).convert("RGB")
        blue_zones = extract_blue_zones(label_mask, LABEL_MASK_BLUE)
        print(f"✅ Loaded label mask with {len(blue_zones)} blue zones.")
    else:
        print(f"⚠️ Label mask not found: {LABEL_MASK_PATH}")

# === Logger Setup ===
log, log_file = create_logger(args.verbose)

# === Parse prefabs.xml ===
def parse_prefabs(xml_path, biome_img, config):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    categorized_points = defaultdict(list)
    excluded_names = defaultdict(set)
    missing_names = set()
    poi_counter = 0

    def transform_coords(x, z):
        cx = int(x + config.map_center if x >= 0 else config.map_center - abs(x))
        cz = int(config.map_center - z if z >= 0 else config.map_center + abs(z))
        return cx, cz

    def get_biome_name(rgb):
        from parse import get_biome_name as biome_lookup
        return biome_lookup(rgb)

    for deco in root.findall(".//decoration"):
        name = deco.attrib.get("name", "").lower()
        pos = deco.attrib.get("position")
        if not pos or should_exclude(name):
            excluded_names["excluded"].add(name)
            continue

        sx = float(deco.attrib.get("size_x", "0"))
        sz = float(deco.attrib.get("size_z", "0"))
        
        # Shift to center of prefab footprint
        x, _, z = map(float, pos.split(","))
        center_x = x + sx / 2
        center_z = z + sz / 2
        
        px, pz = transform_coords(center_x, center_z)

        # Determine category
        if name.startswith("playerstart") or name.startswith("player_start"):
            category = "player_starts"
        elif (name.startswith("street_") or name.startswith("streets_")) and not name.endswith("light"):
            category = "streets"
        elif name.startswith("sign_260") or name.startswith("sign_73"):
            category = "streets"
        else:
            biome_name = "unknown"
            if biome_img:
                biome_color = biome_img.getpixel((px, pz))
                biome_name = get_biome_name(biome_color)
            category = f"biome_{biome_name}"

        poi_id = f"P{poi_counter:04}"
        categorized_points[category].append((poi_id, name, px, pz))
        poi_counter += 1

        if name not in display_names:
            missing_names.add(name)

    return categorized_points, excluded_names, missing_names

categorized_points, excluded_names, missing_names = parse_prefabs(config.xml_path, biome_img, config)

# === Render ===
layer_files = []
legend_entries = {}
if args.skip_layers:
    if args.skip_layers:
        legend_entries["P0000"] = ("DEBUG TEST POI", "debug_test_poi")

if not args.skip_layers:
    combined_path = None
    for category, points in categorized_points.items():
        # Only render biome_* categories listed
        if args.only_biomes:
            if not category.startswith("biome_"):
                continue
            biome = category[len("biome_"):]
            if biome not in args.only_biomes:
                continue
        # ✅ Skip player_starts unless explicitly enabled
        if category == "player_starts" and not args.with_player_starts:
            continue

        dot_centers = [(px, pz) for _, _, px, pz in points]

        combined_path, rejections = render_category_layer(
            category=category,
            points=points,
            config=config,
            display_names=display_names,
            tiers=prefab_tiers,
            tier_colors=tier_colors,
            legend_entries=legend_entries,
            label_mask=label_mask,
            blue_zones=blue_zones,
            red_rgb=LABEL_MASK_RED,
            blue_rgb=LABEL_MASK_BLUE,
            log=log,
            numbered_dots=args.numbered_dots
        )
        if combined_path:
            layer_files.append(combined_path)

# === Render Legend ===
def render_legend(legend_entries, config):
    from PIL import ImageDraw

    print("🗺️ Rendering POI legend with full left zone + right overflow...")

    font = config.font
    img = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    y_start = 48
    y = y_start

    line_height = font.getbbox("Ag")[3] - font.getbbox("Ag")[1] + 12

    # Zone boundaries
    COL_WIDTH = 400  # max label width, adjustable
    COL_SPACING = 20
    
    # Left zone: 2 columns
    LEFT_START_X = 20
    LEFT_MAX_X = LEFT_START_X + COL_WIDTH * 2 + COL_SPACING
    
    # Right zone: 2 columns
    RIGHT_START_X = config.image_size[0] - COL_WIDTH * 2 - COL_SPACING
    RIGHT_MAX_X = config.image_size[0] - 20

    x = LEFT_START_X
    zone = "left"
    entries_drawn = 0

    # Calculate dynamic column width
    col_spacing = 40
    col_width = max(
        font.getbbox(f"{poi_id} → {label}")[2]
        for poi_id, label in legend_entries.items()
    ) + col_spacing

    drawn_boxes = []
    drawn_entries = []
    for poi_id, (label, prefab_name) in sorted(legend_entries.items()):
        name_key = prefab_name.lower()
        tier = prefab_tiers.get(name_key, -1)
        dot_color = tier_colors.get(tier, "#FF0000")  # Default red for unknowns

        text = f"{poi_id} → {label}"

        if y + line_height > config.image_size[1] - 20:
            if zone == "left":
                if x + col_width < LEFT_MAX_X:
                    x += col_width
                else:
                    x = RIGHT_START_X
                    zone = "right"
            elif zone == "right":
                if x + col_width <= RIGHT_MAX_X:
                    x += col_width
                else:
                    print("🛑 Ran out of space in RIGHT zone.")
                    break
            y = y_start

        # Measure text box
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        pad = 6
        box = [x - pad, y - pad, x + text_w + pad, y + text_h + pad]
                
        # Draw text on top
        draw.text((x, y), text, fill=dot_color, font=font)
        drawn_boxes.append((box[0], box[1], box[2], box[3]))
        drawn_entries.append((text, tuple(box), dot_color, (x, y)))
        y += line_height
        entries_drawn += 1
       
    # Draw background and title box
    if drawn_boxes:
        pad = 8
        min_x = max(0, min(box[0] for box in drawn_boxes) - pad)
        min_y = max(0, min(box[1] for box in drawn_boxes) - pad - 24)  # space for title
        max_x = min(config.image_size[0], max(box[2] for box in drawn_boxes) + pad)
        max_y = min(config.image_size[1], max(box[3] for box in drawn_boxes) + pad)

        draw.rectangle([(min_x, min_y), (max_x, max_y)], fill=(0, 0, 0, 192))
        draw.text((min_x + 6, min_y + 4), "Legend", font=font, fill="white")

    # Redraw each entry now that background is down
    for text, box, dot_color, (x, y) in drawn_entries:
        draw.rounded_rectangle(box, radius=6, fill=(255, 255, 255, 230), outline=dot_color, width=2)
        draw.text((x, y), text, fill=dot_color, font=font)

    print(f"✅ Legend rendered: {entries_drawn} entries")
    legend_path = os.path.join(config.output_dir, "poi_legend.png")
    img.save(legend_path)
    print(f"✅ Legend saved to: {legend_path}")

if legend_entries:
    render_legend(legend_entries, config)

# === Combine All Layers ===
if args.combined and layer_files:
    print("🧩 Combining all layers...")
    final = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
    for path in layer_files:
        layer = Image.open(path)
        final = Image.alpha_composite(final, layer)

    final_path = os.path.join(config.combined_dir, "map_all_layers_combined.png")
    final.save(final_path)
    print(f"✅ Final map saved: {final_path}")

# === Final Logs ===
if args.log_missing and missing_names:
    with open(config.missing_log, "w", encoding="utf-8") as f:
        for name in sorted(missing_names):
            f.write(f"{name}\n")
    print(f"📝 Missing display names: {config.missing_log}")

if args.verbose and excluded_names:
    with open(config.excluded_log, "w", encoding="utf-8") as f:
        f.write(f"# prefab2png version: {version}\n")
        for cat, names in excluded_names.items():
            for name in sorted(names):
                f.write(f"{cat},{name}\n")
    print(f"📝 Excluded prefab names: {config.excluded_log}")

with open(os.path.join(config.log_dir or config.output_dir, "bounding_boxes.csv"), "w", encoding="utf-8") as f:
    f.write(f"# prefab2png version: {version}\n")
    f.write("poi_id,layer,x1,y1,x2,y2\n")
    for poi_id, layer, (x1, y1, x2, y2) in placed_bounding_boxes:
        f.write(f"{poi_id},{layer},{x1},{y1},{x2},{y2}\n")

if config.verbose_log_file:
    config.verbose_log_file.close()
print(f"🕒 Render completed in {time.time() - start_time:.2f} seconds")    