# main.py

from parse import args, Config, load_display_names, load_tiers, load_biome_image, extract_blue_zones
from filters import should_exclude
from render import render_category_layer
from labeler import is_placeable  # used for legend fallback optional check
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from PIL import Image

LABEL_MASK_PATH = "mask.gif"
LABEL_MASK_RED = (165, 27, 27)
LABEL_MASK_GREEN = (0, 118, 0)
LABEL_MASK_BLUE = (0, 42, 118)

# === Logging Setup ===

def null_log(msg):
    pass

def create_logger(verbose):
    if verbose:
        os.makedirs('output', exist_ok=True)
        log_file = open("output/green_zone_debug.txt", "w")
        def log(msg):
            log_file.write(msg + "\n")
            log_file.flush()
        return log, log_file
    return null_log, None

# === Setup ===
config = Config(args)
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

        x, _, z = map(float, pos.split(","))
        px, pz = transform_coords(x, z)

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
    legend_entries["P0000"] = "DEBUG TEST POI"

if not args.skip_layers:
    combined_path = None
    for category, points in categorized_points.items():
        if args.only_biomes:
            # Only render biome_* categories listed
            if not category.startswith("biome_"):
                continue
            biome = category[len("biome_"):]
            if biome not in args.only_biomes:
                continue
            # If --biomes not used, render everything
        if args.only_biomes:
            if not category.startswith("biome_"):
                continue
            biome = category[len("biome_"):]
            if biome not in args.only_biomes:
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

    y_start = 20
    y = y_start

    line_height = font.getbbox("Ag")[3] - font.getbbox("Ag")[1] + 6

    # Zone boundaries
    LEFT_START_X = 20
    LEFT_MAX_X = LEFT_START_X + 2 * 400
    RIGHT_START_X = config.image_size[0] - 400
    RIGHT_MAX_X = config.image_size[0] - 20

    x = LEFT_START_X
    zone = "left"
    entries_drawn = 0

    # Background shading
    draw.rectangle([(0, 0), (LEFT_MAX_X, config.image_size[1])], fill="#F0F0F0")
    draw.rectangle([(RIGHT_START_X, 0), (RIGHT_MAX_X, config.image_size[1])], fill="#F0F0F0")

    # Calculate dynamic column width
    col_spacing = 40
    col_width = max(
        font.getbbox(f"{poi_id} → {label}")[2]
        for poi_id, label in legend_entries.items()
    ) + col_spacing

    for poi_id, label in legend_entries.items():
        text = f"{poi_id} → {label}"

        if y + line_height > config.image_size[1] - 20:
            if zone == "left":
                if x + col_width < LEFT_START_X + col_width * 2:
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

        draw.text((x, y), text, fill="black", font=font)
        y += line_height
        entries_drawn += 1

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
        for cat, names in excluded_names.items():
            for name in sorted(names):
                f.write(f"{cat},{name}\n")
    print(f"📝 Excluded prefab names: {config.excluded_log}")

if config.verbose_log_file:
    config.verbose_log_file.close()