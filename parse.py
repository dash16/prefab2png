# parse.py
import os
import platform
import csv
import math
import xml.etree.ElementTree as ET
from PIL import Image, ImageFont, ImageColor, ImageDraw
from collections import defaultdict, namedtuple, deque


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
### 🧩 Tier Color Map: Defines hex colors for difficulty tiers 0–5 (used for dots and label text)
def load_tiers():
	tier_colors = {
		0: "#99896B",  # Tier 0
		1: "#C4833D",
		2: "#A2A43A",
		3: "#69BF4B",
		4: "#3C5CC7",
		5: "#9734C5"
	}
	return tier_colors

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

### 🧩 Prefab Metadata Loader: Loads size and difficulty for prefab2png center shift and tier coloring
def load_prefab_metadata(prefab_dir):
	"""
	Scans all .xml prefab files in the given directory and extracts:
	- size_x, size_z from PrefabSize
	- difficulty from DifficultyTier
	Returns: dict[prefab_name] = (size_x, size_z, difficulty)
	"""
	import os
	import xml.etree.ElementTree as ET

	prefab_data = {}

	for root, _, files in os.walk(prefab_dir):
		for file in files:
			if file.endswith(".xml"):
				prefab_name = os.path.splitext(file)[0].lower()
				xml_path = os.path.join(root, file)
				try:
					tree = ET.parse(xml_path)
					props = {
						p.attrib["name"].lower(): p.attrib["value"]
						for p in tree.findall(".//property")
						if "name" in p.attrib and "value" in p.attrib
					}
					size_x, size_z = 0, 0
					if "prefabsize" in props:
						parts = [s.strip() for s in props["prefabsize"].split(",")]
						if len(parts) >= 3:
							size_x = int(parts[0])
							size_z = int(parts[2])
					difficulty = int(props.get("difficultytier", -1))
					prefab_data[prefab_name] = (size_x, size_z, difficulty)
				except Exception as e:
					print(f"⚠️ Failed to parse {file}: {e}")
	return prefab_data


# Extract dot centers from each category for collision/density use
def determine_category(name, px, pz, biome_img):
	name = name.lower()
	if name.startswith("playerstart") or name.startswith("player_start"):
		return "player_starts"
	if (name.startswith("street_") or name.startswith("streets_")) and not name.endswith("light"):
		return "streets"
	if name.startswith("sign_260") or name.startswith("sign_73"):
		return "streets"

	biome_name = "unknown"
	if biome_img:
		rgb = biome_img.getpixel((px, pz))
		biome_name = get_biome_name(rgb)
	return f"biome_{biome_name}"

def categorize_points(prefabs, display_names, tier_data, biome_image):
	categorized_points = {}
	dot_centers_by_category = {}

	for poi_id, name, px, pz in prefabs:
		display = display_names.get(name.lower(), name)
		tier = tier_data.get(name.lower(), None)

		category = determine_category(name, px, pz, biome_image)
		if category not in categorized_points:
			categorized_points[category] = []
			dot_centers_by_category[category] = []

		categorized_points[category].append((poi_id, display, px, pz))
		dot_centers_by_category[category].append((px, pz))

	return categorized_points, dot_centers_by_category
	
### 🧩 Tile Rotation Lookup: Builds a (x, z) → (tile_name, rotation) mapping for all RWG tiles
def build_tile_rotation_lookup(prefabs_xml_path):
	tile_map = {}
	tree = ET.parse(prefabs_xml_path)
	root = tree.getroot()
	for deco in root.findall(".//decoration[@type='model']"):
		name = deco.attrib["name"]
		if name.startswith("rwg_tile_"):
			pos = deco.attrib["position"]
			rot = int(deco.attrib.get("rotation", 0))
			x, _, z = map(int, pos.split(","))
			tile_map[(x, z)] = (name, rot)
	return tile_map

### 🧩 Tile Lookup by POI: Checks if a POI falls inside any RWG tile by comparing world coords
def find_tile_for_poi(poi_x, poi_z, tile_map, tile_size=150):
	for (tile_x, tile_z), (name, rot) in tile_map.items():
		if (tile_x <= poi_x < tile_x + tile_size) and (tile_z <= poi_z < tile_z + tile_size):
			return name, rot
	return None, None
	