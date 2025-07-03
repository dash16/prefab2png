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
args = parser.parse_args()

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
            self.verbose_log_file.write("prefab_name,display_name,tier,dot_color\n")
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
DOT_RADIUS_HIGHLIGHT = 6
FONT_SIZE = 12
FONT_SIZE_HIGHLIGHT = 24
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
    highlight_font = ImageFont.truetype(font_path, FONT_SIZE_HIGHLIGHT)
except OSError:
    base_font = highlight_font = ImageFont.load_default()

def get_fonts(is_trader):
    return (highlight_font if is_trader else base_font), \
           ("green" if is_trader else "red"), \
           ("blue" if is_trader else "black"), \
           (DOT_RADIUS_HIGHLIGHT if is_trader else DOT_RADIUS)

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

    for deco in root.findall('.//decoration'):
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

        categorized_points[category].append((name, px, pz))

        if name not in prefab_display_names:
            missing_names.add(name)

    return categorized_points, excluded_names, missing_names

categorized_points, excluded_names, missing_names = parse_and_categorize_prefabs(
    config.xml_path, biome_img, config, prefab_display_names
)

# === RENDER ===
def render_category_layer(category, points, config, display_names, tiers, tier_colors):
    from PIL import Image, ImageDraw

    print(f"Rendering layer '{category}' with {len(points)} points...")

    points_img = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
    labels_img = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
    points_draw = ImageDraw.Draw(points_img)
    labels_draw = ImageDraw.Draw(labels_img)

    occupied = []

    for name, px, pz in points:
        display = display_names.get(name, name)
        if name not in display_names and config.args.log_missing:
            with open(config.missing_log, "a", encoding="utf-8") as f:
                f.write(f"{name}\n")

        tier = tiers.get(name)
        dot_color = tier_colors.get(tier, "red") if tier is not None else "red"

        # Draw dot
        r = config.dot_radius
        points_draw.ellipse((px - r - 1, pz - r - 1, px + r + 1, pz + r + 1), fill="white")
        points_draw.ellipse((px - r, pz - r, px + r, pz + r), fill=dot_color)

        if config.verbose_log_file:
            config.verbose_log_file.write(f"{name},{display},{tier},{dot_color}\n")

        # Measure text size
        bbox = labels_draw.textbbox((0, 0), display, font=config.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Spiral search for label placement
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
                    # Check overlap
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

        # Fallback if no space found
        if not label_box:
            label_box = (
                px, pz + 4,
                px + text_width + 2 * LABEL_PADDING,
                pz + 4 + text_height + 2 * LABEL_PADDING
            )
            occupied.append(label_box)

        text_x = label_box[0] + LABEL_PADDING
        text_y = label_box[1] + LABEL_PADDING

        # Draw connector line from dot to label
        labels_draw.line((px, pz, text_x, text_y), fill="gray", width=1)

        # Shadowed label
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if ox != 0 or oy != 0:
                    labels_draw.text((text_x + ox, text_y + oy), display, fill="white", font=config.font)
        labels_draw.text((text_x, text_y), display, fill="black", font=config.font)

    points_path = os.path.join(config.output_dir, f"{category}_points.png")
    labels_path = os.path.join(config.output_dir, f"{category}_labels.png")
    points_img.save(points_path)
    labels_img.save(labels_path)

    if config.args.combined:
        combined = Image.alpha_composite(points_img, labels_img)
        combined_path = os.path.join(config.combined_dir, f"{category}_combined.png")
        combined.save(combined_path)
        return combined_path

    return None

layer_files = []
for category, points in categorized_points.items():
    combined_path = render_category_layer(
        category,
        points,
        config,
        prefab_display_names,
        prefab_tiers,
        TIER_COLORS
    )
    if combined_path:
        layer_files.append(combined_path)

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