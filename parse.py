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