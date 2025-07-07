# parse.py
import os
import platform
import csv
import math
import xml.etree.ElementTree as ET
from PIL import Image, ImageFont, ImageColor, ImageDraw
from collections import defaultdict, namedtuple, deque

# === ARGUMENT PARSING ===
import argparse
parser = argparse.ArgumentParser(description="Render 7DTD prefab map layers.")
parser.add_argument("--xml", type=str)
parser.add_argument("--localization", type=str)
parser.add_argument("--biomes", type=str)
parser.add_argument("--verbose", action="store_true")
parser.add_argument("--combined", action="store_true")
parser.add_argument("--with-player-starts", action="store_true")
parser.add_argument("--log-missing", action="store_true")
parser.add_argument("--numbered-dots", action="store_true")
parser.add_argument("--skip-layers", action="store_true")
args = parser.parse_args()

# === CONFIGURATION ===
class Config:
    def __init__(self, args):
        self.args = args
        self.image_size = (6145, 6145)
        self.map_center = 3072
        self.dot_radius = 4
        self.font_size = 20
        self.label_padding = 4

        self.output_dir = "output"
        self.combined_dir = os.path.join(self.output_dir, "combined")
        self.missing_log = os.path.join(self.output_dir, "missing_display_names.txt")
        self.verbose_log = os.path.join(self.output_dir, "verbose_log.txt")
        self.excluded_log = os.path.join(self.output_dir, "excluded_prefabs.txt")

        self.xml_path, self.localization_path, self.biome_path = self.resolve_paths()
        self.font_path = self.resolve_font_path()
        self.font = self.load_font()

        os.makedirs(self.output_dir, exist_ok=True)
        if self.args.combined:
            os.makedirs(self.combined_dir, exist_ok=True)

        self.verbose_log_file = open(self.verbose_log, "w", encoding="utf-8") if self.args.verbose else None
        if self.verbose_log_file:
            self.verbose_log_file.write("poi_id,prefab_name,display_name,dot_color,placement\n")

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
            base = "~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data"
            return (
                os.path.expanduser(f"{base}/Worlds/Navezgane/prefabs.xml"),
                os.path.expanduser(f"{base}/Config/Localization.txt"),
                os.path.expanduser(f"{base}/Worlds/Navezgane/biomes.png")
            )

    def resolve_font_path(self):
        return "C:\\Windows\\Fonts\\arial.ttf" if platform.system() == "Windows" else "/System/Library/Fonts/Supplemental/Arial.ttf"

    def load_font(self):
        try:
            return ImageFont.truetype(self.font_path, self.font_size)
        except OSError:
            return ImageFont.load_default()

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
        print(f"⚠️ Localization file not found:\n{path}")
    return display_names

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
        print("⚠️ diff.csv not found.")
    return tier_colors, tiers

# === BIOME HANDLING ===
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

def load_biome_image(path, target_size):
    if os.path.exists(path):
        img = Image.open(path).convert("RGB")
        if img.size != target_size:
            img = img.resize(target_size, Image.Resampling.NEAREST)
        return img
    print(f"⚠️ Biome map not found: {path}")
    return None

# === LABEL MASK ===
def extract_blue_zones(mask_img, blue_rgb=(0, 42, 118)):
    width, height = mask_img.size
    pixels = mask_img.load()
    visited = [[False] * height for _ in range(width)]
    blue_zones = []

    def flood_fill(x, y):
        q = deque([(x, y)])
        min_x = max_x = x
        min_y = max_y = y
        visited[x][y] = True

        while q:
            cx, cy = q.popleft()
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if not visited[nx][ny] and pixels[nx, ny] == blue_rgb:
                        visited[nx][ny] = True
                        q.append((nx, ny))
                        min_x = min(min_x, nx)
                        max_x = max(max_x, nx)
                        min_y = min(min_y, ny)
                        max_y = max(max_y, ny)
        return (min_x, min_y, max_x, max_y)

    for x in range(width):
        for y in range(height):
            if not visited[x][y] and pixels[x, y] == blue_rgb:
                blue_zones.append(flood_fill(x, y))

    return blue_zones
