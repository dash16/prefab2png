# prefab2png.py
# Copyright (c) 2025 Dustin Newell
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict, namedtuple
import os
import platform
import argparse
import csv
import math

# === ARGUMENT PARSING ===
parser = argparse.ArgumentParser(description="Render 7DTD prefab map layers.")
parser.add_argument("--xml", type=str, help="Full path to prefabs.xml")
parser.add_argument("--localization", type=str, help="Full path to Localization.txt")
parser.add_argument("--biomes", type=str, help="Full path to biomes.png")
parser.add_argument("--verbose", action="store_true", help="Enable verbose prefab name and tier logging.")
parser.add_argument("--combined", action="store_true", help="Generate combined PNG layers.")
parser.add_argument("--with-player-starts", action="store_true", help="Include 'player_starts' layer.")
parser.add_argument("--log-missing", action="store_true", help="Log prefabs missing display names.")
parser.add_argument("--bounding-boxes", action="store_true", help="Render prefab bounding boxes from size attribute.")
parser.add_argument("--numbered-dots", action="store_true", help="Replace prefab dots with unique POI IDs.")
args = parser.parse_args()

# === POI Mask for safe label placement ===
from PIL import ImageColor
LABEL_MASK_PATH = "prefab_label_mask_optimized.gif"
LABEL_MASK_RED = ImageColor.getrgb("#A51B1B")  # (165, 27, 27)
LABEL_MASK_GREEN = ImageColor.getrgb("#007600")
LABEL_MASK_SEARCH_RADIUS = 10  # adjustable

label_mask = None
if os.path.exists(LABEL_MASK_PATH):
    label_mask = Image.open(LABEL_MASK_PATH).convert("RGB")
    print(f"✅ Loaded label mask: {LABEL_MASK_PATH}")
else:
    print(f"⚠️ Label mask not found: {LABEL_MASK_PATH} — label filtering disabled.")

# === CONFIGURATION ===
class Config:
    def __init__(self, args):
        self.args = args

        # Image & Map
        self.image_size = (6145, 6145)
        self.map_center = 3072
        self.dot_radius = 4
        self.font_size = 20
        self.label_padding = 4

        # Paths
        self.output_dir = "output"
        self.combined_dir = os.path.join(self.output_dir, "combined")
        self.missing_log = os.path.join(self.output_dir, "missing_display_names.txt")
        self.verbose_log = os.path.join(self.output_dir, "verbose_log.txt")
        self.excluded_log = os.path.join(self.output_dir, "excluded_prefabs.txt")

        # File path resolution
        self.xml_path, self.localization_path, self.biome_path = self.resolve_paths()

        # Font
        self.font_path = self.resolve_font_path()
        self.font = self.load_font()

        # Output folders
        os.makedirs(self.output_dir, exist_ok=True)
        if self.args.combined:
            os.makedirs(self.combined_dir, exist_ok=True)

        if self.args.verbose:
            self.verbose_log_file = open(self.verbose_log, "w", encoding="utf-8")
            self.verbose_log_file.write("poi_id,prefab_name,display_name,dot_color,placement\n")
        else:
            self.verbose_log_file = None

    def resolve_paths(self):
        if self.args.xml and self.args.localization and self.args.biomes:
            return self.args.xml, self.args.localization, self.args.biomes
        elif platform.system() == "Windows":
            return (
                os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steamapps\common\7 Days To Die\Data\Worlds\Navezgane\prefabs.xml"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steamapps\common\7 Days To Die\Data\Config\Localization.txt"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steamapps\common\7 Days To Die\Data\Worlds\Navezgane\biomes.png")
            )
        else:
            return (
                os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Worlds/Navezgane/prefabs.xml"),
                os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Config/Localization.txt"),
                os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Worlds/Navezgane/biomes.png")
            )

    def resolve_font_path(self):
        if platform.system() == "Windows":
            return "C:\\Windows\\Fonts\\arial.ttf"
        else:
            return "/System/Library/Fonts/Supplemental/Arial.ttf"

    def load_font(self):
        try:
            return ImageFont.truetype(self.font_path, self.font_size)
        except OSError:
            return ImageFont.load_default()

config = Config(args)


# === DISPLAY NAME MAPPING ===
def load_display_names(path):
    display_names = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) > 5:
                    prefab_name = parts[0].strip().lower()
                    display_name = parts[5].strip()
                    if prefab_name and display_name:
                        display_names[prefab_name] = display_name
        print(f"✅ Loaded {len(display_names)} display name mappings.")
    else:
        print(f"⚠️ Localization file not found:\n{path}\nUsing internal prefab names.")
    return display_names
prefab_display_names = load_display_names(config.localization_path)

# === DIFFICULTY TIER COLORS ===
def load_tiers(path="diff.csv"):
    tier_colors = {
        0: "#99896B",
        1: "#C4833D",
        2: "#A2A43A",
        3: "#69BF4B",
        4: "#3C5CC7",
        5: "#9734C5"
    }
    tiers = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row["prefabName"].strip().lower()
                try:
                    tier = int(float(row["Tier"]))
                    if 0 <= tier <= 5:
                        tiers[name] = tier
                except (ValueError, KeyError):
                    continue
        print(f"✅ Loaded {len(tiers)} prefab difficulty ratings from {path}")
    else:
        print("⚠️ diff.csv not found. Using default red/green dots.")
    return tier_colors, tiers
TIER_COLORS, prefab_tiers = load_tiers()

# === CONFIGURATION ===
IMAGE_SIZE = (6145, 6145)
MAP_CENTER = 3072
DOT_RADIUS = 4
FONT_SIZE = 12
LABEL_PADDING = 4
LABEL_SEARCH_RADIUS = 100
LABEL_STEP = 10
OUTPUT_DIR = "output"
COMBINED_DIR = os.path.join(OUTPUT_DIR, "combined")
MISSING_LOG = os.path.join(OUTPUT_DIR, "missing_display_names.txt")
VERBOSE_LOG = os.path.join(OUTPUT_DIR, "verbose_log.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)
if args.combined:
    os.makedirs(COMBINED_DIR, exist_ok=True)
if args.verbose:
    verbose_log = open(VERBOSE_LOG, "w", encoding="utf-8")

# === FONT SETUP ===
if platform.system() == "Windows":
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
else:
    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
try:
    base_font = ImageFont.truetype(font_path, FONT_SIZE)
except OSError:
    base_font = ImageFont.load_default()

# === BIOME SETUP ===
biome_img = None
if os.path.exists(config.biome_path):
    biome_img = Image.open(config.biome_path).convert("RGB")
    if biome_img.size != config.image_size:
        biome_img = biome_img.resize(config.image_size, Image.Resampling.NEAREST)
if biome_img and biome_img.size != IMAGE_SIZE:
    biome_img = biome_img.resize(IMAGE_SIZE, Image.Resampling.NEAREST)

Biome = namedtuple("Biome", ["name", "rgb"])
canonical_biomes = [
    Biome("pine_forest", (0, 64, 0)),
    Biome("wasteland", (255, 172, 0)),
    Biome("desert", (255, 224, 128)),
    Biome("burnt_forest", (190, 14, 246)),
    Biome("snow", (255, 255, 255)),
]

def rgb_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def get_biome_name(rgb):
    closest = min(canonical_biomes, key=lambda b: rgb_distance(rgb, b.rgb))
    return closest.name

def transform_coords(x, z):
    return int(x + MAP_CENTER if x >= 0 else MAP_CENTER - abs(x)), int(MAP_CENTER - z if z >= 0 else MAP_CENTER + abs(z))

# === PARSE XML AND CATEGORIZE ===
def parse_and_categorize_prefabs(xml_path, biome_img, config, prefab_display_names):
    import xml.etree.ElementTree as ET
    from collections import defaultdict

    categorized_points = defaultdict(list)
    missing_names = set()
    excluded_names = defaultdict(set)

    def should_exclude(name):
        if name.startswith("sign_"):
            return not (name.startswith("sign_260") or name.startswith("sign_73"))
        if any(ex in name for ex in (
            "bridge", "part_", "street_light", "diersville_city_", "cornfield_", "site_grave",
            "wilderness_filler", "roadblock", "crater", "gravestowne_city", "departure_city", "perishton_city",
            "rubble_burnt_filler", "rubble_downtown_filler", "bus_stop", "bus_wreck", "canyon_gift_shop_parking",
            "canyon_gift_shop_sign", "desert_town_blk", "perishton_fence", "perishton_riverdock", "remnant_industrial",
            "road_railing_long_filled", "perishton_church_parking", "perishton_median", "perishton_outlet"
        )):
            return True
        return False

    def transform_coords(x, z):
        cx = int(x + config.map_center if x >= 0 else config.map_center - abs(x))
        cz = int(config.map_center - z if z >= 0 else config.map_center + abs(z))
        return cx, cz

    def get_biome_name(rgb):
        def rgb_distance(c1, c2):
            return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

        canonical_biomes = [
            ("pine_forest", (0, 64, 0)),
            ("wasteland", (255, 172, 0)),
            ("desert", (255, 224, 128)),
            ("burnt_forest", (190, 14, 246)),
            ("snow", (255, 255, 255)),
        ]
        closest = min(canonical_biomes, key=lambda b: rgb_distance(rgb, b[1]))
        return closest[0]

    tree = ET.parse(xml_path)
    root = tree.getroot()

    for idx, deco in enumerate(root.findall('.//decoration')):
        size_str = deco.attrib.get("size")
        if size_str:
            sx, sy, sz = map(float, size_str.split(","))
        else:
            sx, sy, sz = 0, 0, 0
        name = deco.attrib.get("name", "").lower()
        pos_str = deco.attrib.get("position")
        if not pos_str:
            continue
        if should_exclude(name):
            excluded_names["excluded"].add(name)
            continue

        x, y, z = map(float, pos_str.split(","))
        px, pz = transform_coords(x, z)

# Player start handling
        if "player_start" in name:
            if config.args.with_player_starts:
                category = "player_starts"
            else:
                excluded_names["excluded"].add(name)
                continue
# Street aggregate and exclusions        
        elif name.startswith("street_") and "street_light" not in name:
            category = "streets"
        elif name.startswith("sign_260") or name.startswith("sign_73"):
            category = "streets"
        else:
            biome_name = "unknown"
            if biome_img:
                biome_color = biome_img.getpixel((px, pz))
                biome_name = get_biome_name(biome_color)
            category = f"biome_{biome_name}"
# POI_ID
#        poi_id = f"P{idx+1:04d}"
        categorized_points[category].append((name, px, pz))
#        if config.args.numbered_dots:
#            legend_entries.append((poi_id, display))

        if name not in prefab_display_names:
            missing_names.add(name)

    return categorized_points, excluded_names, missing_names

categorized_points, excluded_names, missing_names = parse_and_categorize_prefabs(
    config.xml_path, biome_img, config, prefab_display_names
)

# === RENDER ===
global_rejection_total = 0
def render_category_layer(category, points, config, display_names, tiers, tier_colors, legend_entries, poi_counter):
    from PIL import ImageDraw, Image

    print(f"Rendering layer '{category}' with {len(points)} points...")
    rejection_attempts = 0
    points_img = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
    labels_img = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
    points_draw = ImageDraw.Draw(points_img)
    labels_draw = ImageDraw.Draw(labels_img)
    occupied = []

    for name, px, pz in points:
        display = display_names.get(name, name)
        tier = tiers.get(name)
        dot_color = tier_colors.get(tier, "red") if tier is not None else "red"

        poi_id = f"P{poi_counter:04d}"
        poi_counter += 1

        if name not in display_names and config.args.log_missing:
            with open(config.missing_log, "a", encoding="utf-8") as f:
                f.write(f"{name}\n")

        if config.args.verbose:
            tier_str = f" (Tier {tier})" if tier is not None else ""
            config.verbose_log_file.write(f"{poi_id},{name},{display}{tier_str},{dot_color},rendered\n")

        if config.args.bounding_boxes:
            size = 8  # fallback if no size
            if "_" in name:
                try:
                    size = int(name.split("_")[-1])
                except:
                    pass
            box_size = size * config.cell_size
            x1 = px - box_size // 2
            y1 = pz - box_size // 2
            x2 = px + box_size // 2
            y2 = pz + box_size // 2
            points_draw.rectangle((x1, y1, x2, y2), outline="gray")

        if config.args.numbered_dots:
            legend_entries.append((poi_id, display))

            # Measure text size
            bbox = labels_draw.textbbox((0, 0), poi_id, font=config.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            pad = 4
            w = text_width + pad * 2
            h = text_height + pad * 2

            # Spiral search for non-overlapping label placement
            LABEL_SEARCH_RADIUS = 100
            LABEL_STEP = 10
            label_box = None
            for radius in range(0, LABEL_SEARCH_RADIUS, LABEL_STEP):
                for dx in range(-radius, radius + 1, LABEL_STEP):
                    for dy in range(-radius, radius + 1, LABEL_STEP):
                        lx = px + dx
                        ly = pz + dy
                        test_box = (lx, ly, lx + w, ly + h)
                        if all(
                            test_box[2] <= ox1 or test_box[0] >= ox2 or
                            test_box[3] <= oy1 or test_box[1] >= oy2
                            for (ox1, oy1, ox2, oy2) in occupied
                        ):
                            label_box = test_box
                            occupied.append(test_box)
                            break
                    if label_box:
                        break
                if label_box:
                    break

            # Fallback to center
            if not label_box:
                label_box = (px - w // 2, pz - h // 2, px + w // 2, pz + h // 2)
                occupied.append(label_box)

            # Choose nearest corner for connector line
            x1, y1, x2, y2 = label_box
            corners = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]
            nearest_corner = min(corners, key=lambda c: (c[0] - px) ** 2 + (c[1] - pz) ** 2)
            labels_draw.line((px, pz, nearest_corner[0], nearest_corner[1]), fill="gray", width=1)

            # Draw badge and POI_ID
            text_x = x1 + pad
            text_y = y1 + pad
            points_draw.rounded_rectangle(label_box, radius=4, fill="white", outline="black")
            labels_draw.text((text_x, text_y), poi_id, fill="black", font=config.font)

        else:
            # Standard prefab dot
            r = config.dot_radius
            points_draw.ellipse((px - r - 1, pz - r - 1, px + r + 1, pz + r + 1), fill="white")
            points_draw.ellipse((px - r, pz - r, px + r, pz + r), fill=dot_color)

            # Spiral label placement for display name
            bbox = labels_draw.textbbox((0, 0), display, font=config.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            LABEL_PADDING = config.label_padding
            LABEL_SEARCH_RADIUS = 100
            LABEL_STEP = 10
            label_box = None
            for radius in range(0, LABEL_SEARCH_RADIUS, LABEL_STEP):
                for dx in range(-radius, radius + 1, LABEL_STEP):
                    for dy in range(-radius, radius + 1, LABEL_STEP):
                        lx = px + dx
                        ly = pz + dy
                        test_box = (
                            lx, ly,
                            lx + text_width + 2 * LABEL_PADDING,
                            ly + text_height + 2 * LABEL_PADDING
                        )
                        if all(
                            test_box[2] <= ox1 or test_box[0] >= ox2 or
                            test_box[3] <= oy1 or test_box[1] >= oy2
                            for (ox1, oy1, ox2, oy2) in occupied
                        ):
                            label_box = test_box
                            occupied.append(test_box)
                            break
                    if label_box:
                        break
                if label_box:
                    break

            if not label_box:
                label_box = (
                    px, pz + 4,
                    px + text_width + 2 * LABEL_PADDING,
                    pz + 4 + text_height + 2 * LABEL_PADDING
                )
                occupied.append(label_box)

            text_x = label_box[0] + LABEL_PADDING
            text_y = label_box[1] + LABEL_PADDING
            
            
            # Check prefab label mask before drawing
            should_draw_label = True
            if label_mask:
                lx = int(round(text_x))
                ly = int(round(text_y))
                if 0 <= lx < label_mask.width and 0 <= ly < label_mask.height:
                    r, g, b = label_mask.getpixel((lx, ly))
                    if (r, g, b) == LABEL_MASK_RED:
                        # Try to nudge slightly to green, but ensure label box stays out of red
                        found = False
                        bbox = labels_draw.textbbox((0, 0), display, font=config.font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    
                        for dy in range(-LABEL_MASK_SEARCH_RADIUS, LABEL_MASK_SEARCH_RADIUS + 1):
                            for dx in range(-LABEL_MASK_SEARCH_RADIUS, LABEL_MASK_SEARCH_RADIUS + 1):
                                nx = lx + dx
                                ny = ly + dy
                    
                                # Define label box corners
                                x1, y1 = nx, ny
                                x2, y2 = nx + text_width, ny + text_height
                    
                                # Check bounds
                                if x2 >= label_mask.width or y2 >= label_mask.height or x1 < 0 or y1 < 0:
                                    continue
                    
                                # Check corners and center of bounding box
                                corners = [
                                    (x1, y1), (x2, y1), (x1, y2), (x2, y2),
                                    ((x1 + x2) // 2, (y1 + y2) // 2)
                                ]
                            else:

                                if all(label_mask.getpixel((cx, cy)) != LABEL_MASK_RED for cx, cy in corners):
                                    text_x = nx
                                    text_y = ny
                                    found = True
                                    break
                            if found:
                                break
                    
                        if not found:
#                            print(f"[DEBUG] Rejected: {poi_id} → {display} — no safe label position found.")
                            should_draw_label = False
                            rejection_attempts += 1  # 🧮 Count 1 skipped label
#                            print(f"[DEBUG] rejection_attempts = {rejection_attempts}")
                            if config.args.verbose and config.verbose_log_file:
                                config.verbose_log_file.write(f"{poi_id},{name},{display}{tier_str},{dot_color},skipped (blocked by red zone at {text_x},{text_y})\n")

            if should_draw_label:
                labels_draw.line((px, pz, text_x, text_y), fill="gray", width=1)
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        if ox != 0 or oy != 0:
                            labels_draw.text((text_x + ox, text_y + oy), display, fill="white", font=config.font)
                labels_draw.text((text_x, text_y), display, fill="black", font=config.font)

    # Save output images
    points_path = os.path.join(config.output_dir, f"{category}_points.png")
    labels_path = os.path.join(config.output_dir, f"{category}_labels.png")
    points_img.save(points_path)
    labels_img.save(labels_path)

    if config.args.combined:
        combined = Image.alpha_composite(points_img, labels_img)
        combined_path = os.path.join(config.combined_dir, f"{category}_combined.png")
        combined.save(combined_path)
        return combined_path, poi_counter, rejection_attempts
    return None, poi_counter, rejection_attempts

layer_files = []
poi_counter = 0
legend_entries = []

for category, points in categorized_points.items():
    combined_path, poi_counter, rejection_attempts = render_category_layer(
        category,
        points,
        config,
        prefab_display_names,
        prefab_tiers,
        TIER_COLORS,
        legend_entries,
        poi_counter
    )
    global_rejection_total += rejection_attempts
    if combined_path:
        layer_files.append(combined_path)


# === Draw Legend ===
def render_legend_overlay(legend_entries, config):
    from PIL import ImageDraw, ImageFont, Image

    print("🗺️ Rendering POI legend with full left zone + right overflow...")

    legend_img = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(legend_img)

    font = config.font
    y_start = 20
    y = y_start

    line_height = font.getbbox("Ag")[3] - font.getbbox("Ag")[1] + 6

    # Zones
    LEFT_START_X = 20
    LEFT_MAX_X = 900
    RIGHT_START_X = config.image_size[0] - 400
    RIGHT_MAX_X = config.image_size[0] - 20

    x = LEFT_START_X
    zone = "left"
    entries_drawn = 0

    # Determine column width
    col_spacing = 40
    col_width = max(
        font.getbbox(f"{poi_id} → {display}")[2]
        for poi_id, display in legend_entries
    ) + col_spacing
#    print(f"ℹ️ Computed col_width = {col_width}")
    print(f"🧮 Collecting legend entries: {len(legend_entries)}")

    # Draw opaque background only behind the legend zones
    draw.rectangle([(0, 0), (LEFT_MAX_X, config.image_size[1])], fill="#F0F0F0")
    draw.rectangle([(RIGHT_START_X, 0), (RIGHT_MAX_X, config.image_size[1])], fill="#F0F0F0")

    for poi_id, display in legend_entries:
        text = f"{poi_id} → {display}"
    
        if y + line_height > config.image_size[1]:
#            print(f"🔄 Column full at x={x} (zone={zone}), y={y}.")
    
            if zone == "left":
                if x + col_width * 2 <= LEFT_MAX_X:
                    x += col_width
#                    print(f"➡️ Staying in LEFT zone, shifting to x={x}")
                else:
                    x = RIGHT_START_X
                    zone = "right"
#                    print(f"↘️ Switching to RIGHT zone, x={x}")
            elif zone == "right":
                if x + col_width <= RIGHT_MAX_X:
                    x += col_width
#                    print(f"➡️ Continuing in RIGHT zone, shifting to x={x}")
                else:
                    print("🛑 Ran out of space in RIGHT zone.")
                    break
            y = y_start
    
        draw.text((x, y), text, fill="black", font=font)
        y += line_height
        entries_drawn += 1


    print(f"✅ Legend rendered: {entries_drawn} entries ({zone} zone)")
    legend_path = os.path.join(config.output_dir, "poi_legend.png")
    legend_img.save(legend_path)
    print(f"✅ Legend saved to: {legend_path}")

if config.args.numbered_dots:
    render_legend_overlay(legend_entries, config)

# === Combined map output ===
def render_combined_map(layer_files, config):
    if not layer_files:
        return

    print("Saving overall combined map...")

    final = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
    for f in layer_files:
        img = Image.open(f)
        final = Image.alpha_composite(final, img)

    final_path = os.path.join(config.combined_dir, "map_all_layers_combined.png")
    final.save(final_path)
    print("✅ All combined images saved.")

# === default logging ===
def finalize_logs(config, missing_names, excluded_names):
    if config.args.log_missing and missing_names:
        with open(config.missing_log, "w", encoding="utf-8") as f:
            for name in sorted(missing_names):
                f.write(f"{name}\n")
        print(f"📝 Missing display names written to: {config.missing_log}")

    if config.args.verbose and config.verbose_log_file:
        config.verbose_log_file.write(f"Summary,of,rejected,labels:,{global_rejection_total} label placements rejected across all layers\n")

    if config.verbose_log_file:
        config.verbose_log_file.close()
        print(f"📝 Verbose prefab name log written to: {config.verbose_log}")

    if config.args.verbose and excluded_names:
        with open(config.excluded_log, "w", encoding="utf-8") as f:
            for cat, names in excluded_names.items():
                for name in sorted(names):
                    f.write(f"{cat},{name}\n")
        print(f"📝 Excluded prefab names written to: {config.excluded_log}")

if config.args.combined:
    render_combined_map(layer_files, config)

finalize_logs(config, missing_names, excluded_names)