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
args = parser.parse_args()

# === FILE PATH SETUP ===
if args.xml and args.localization and args.biomes:
    INPUT_XML = args.xml
    localization_path = args.localization
    biome_path = args.biomes
else:
    if platform.system() == "Windows":
        localization_path = os.path.expandvars(
            r"%ProgramFiles(x86)%\Steam\steamapps\common\7 Days To Die\Data\Config\Localization.txt"
        )
        INPUT_XML = os.path.expandvars(
            r"%ProgramFiles(x86)%\Steam\steamapps\common\7 Days To Die\Data\Worlds\Navezgane\prefabs.xml"
        )
        biome_path = os.path.expandvars(
            r"%ProgramFiles(x86)%\Steam\steamapps\common\7 Days To Die\Data\Worlds\Navezgane\biomes.png"
        )
    else:
        localization_path = os.path.expanduser(
            "~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Config/Localization.txt"
        )
        INPUT_XML = os.path.expanduser(
            "~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Worlds/Navezgane/prefabs.xml"
        )
        biome_path = os.path.expanduser(
            "~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data/Worlds/Navezgane/biomes.png"
        )

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

prefab_display_names = load_display_names(localization_path)

# === DIFFICULTY TIER COLORS ===
def load_tiers(path):
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

TIER_COLORS, prefab_tiers = load_tiers("diff.csv")

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
biome_img = Image.open(biome_path).convert("RGB") if os.path.exists(biome_path) else None
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
tree = ET.parse(INPUT_XML)
root = tree.getroot()

categorized_points = defaultdict(list)
missing_names = set()
excluded_names = defaultdict(set)

for deco in root.findall('.//decoration'):
    name = deco.attrib.get("name", "").lower()
    pos_str = deco.attrib.get("position")
    if not pos_str:
        continue

    excluded = False
    # Allowlist for sign_260 and sign_73
    if name.startswith("sign_"):
        if not (name.startswith("sign_260") or name.startswith("sign_73")):
            excluded = True
    elif any(ex in name for ex in (
        "bridge", "part_", "street_light", "diersville_city_", "cornfield_", "site_grave",
        "wilderness_filler", "roadblock", "crater", "gravestowne_city", "departure_city", "perishton_city",
        "rubble_burnt_filler", "rubble_downtown_filler", "bus_stop", "bus_wreck", "canyon_gift_shop_parking",
        "canyon_gift_shop_sign", "desert_town_blk", "perishton_fence", "perishton_riverdock", "remnant_industrial",
        "road_railing_long_filled", "perishton_church_parking", "perishton_median", "perishton_outlet"
    )):
        excluded = True

    if excluded:
        excluded_names["excluded"].add(name)
        continue

    x, y, z = map(float, pos_str.split(","))
    px, pz = transform_coords(x, z)

    if args.with_player_starts and "player_start" in name:
        category = "player_starts"
    elif (name.startswith("street_") and "street_light" not in name) or \
     name.startswith("sign_260") or name.startswith("sign_73"):
        category = "streets"
    else:
        biome_name = "unknown"
        if biome_img:
            biome_color = biome_img.getpixel((px, pz))
            biome_name = get_biome_name(biome_color)
        category = f"biome_{biome_name}"

    categorized_points[category].append((name, px, pz))

# === RENDER ===
layer_files = []
for category, points in categorized_points.items():
    print(f"Rendering layer '{category}' with {len(points)} points...")
    points_img = Image.new("RGBA", IMAGE_SIZE, (255, 255, 255, 0))
    labels_img = Image.new("RGBA", IMAGE_SIZE, (255, 255, 255, 0))
    points_draw = ImageDraw.Draw(points_img)
    labels_draw = ImageDraw.Draw(labels_img)
    occupied = []

    for name, px, pz in points:
        is_trader = "trader" in name
        font, dot_color, text_color, radius = get_fonts(is_trader)

        display = prefab_display_names.get(name, name)
        if name not in prefab_display_names:
            missing_names.add(name)

        tier = prefab_tiers.get(name, None)
        dot_fill = TIER_COLORS.get(tier, dot_color) if tier is not None else dot_color

        if args.verbose:
            tier_str = f" (Tier {tier})" if tier is not None else ""
            verbose_log.write(f"{name},{display},{tier},{dot_fill}\n")

        points_draw.ellipse((px - radius - 1, pz - radius - 1, px + radius + 1, pz + radius + 1), fill="white")
        points_draw.ellipse((px - radius, pz - radius, px + radius, pz + radius), fill=dot_fill)

        bbox = labels_draw.textbbox((0, 0), display, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        label_rect = (
            px, pz + 4, px + text_width + 2 * LABEL_PADDING, pz + 4 + text_height + 2 * LABEL_PADDING
        )
        text_x = label_rect[0] + LABEL_PADDING
        text_y = label_rect[1] + LABEL_PADDING

        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if ox != 0 or oy != 0:
                    labels_draw.text((text_x + ox, text_y + oy), display, fill="white", font=font)
        labels_draw.text((text_x, text_y), display, fill=text_color, font=font)

    points_img.save(os.path.join(OUTPUT_DIR, f"{category}_points.png"))
    labels_img.save(os.path.join(OUTPUT_DIR, f"{category}_labels.png"))
    if args.combined:
        combined = Image.alpha_composite(points_img, labels_img)
        combined_path = os.path.join(COMBINED_DIR, f"{category}_combined.png")
        combined.save(combined_path)
        layer_files.append(combined_path)

if args.combined and layer_files:
    print("Saving overall combined map...")
    final = Image.new("RGBA", IMAGE_SIZE, (255, 255, 255, 0))
    for f in layer_files:
        img = Image.open(f)
        final = Image.alpha_composite(final, img)
    final.save(os.path.join(COMBINED_DIR, "map_all_layers_combined.png"))
    print("✅ All combined images saved.")

if args.log_missing and missing_names:
    with open(MISSING_LOG, "w", encoding="utf-8") as missing_log:
        for name in sorted(missing_names):
            missing_log.write(f"{name}\n")
    print(f"📝 Missing display names written to: {MISSING_LOG}")

if args.verbose:
    verbose_log.close()
    print(f"📝 Verbose prefab name log written to: {VERBOSE_LOG}")

# === FINALIZE EXCLUDED LOG ===
if args.verbose and excluded_names:
    with open(os.path.join(OUTPUT_DIR, "excluded_prefabs.txt"), "w", encoding="utf-8") as f:
        for cat, names in excluded_names.items():
            for name in sorted(names):
                f.write(f"{cat},{name}\n")
    print("📝 Excluded prefab names written to: output/excluded_prefabs.txt")
