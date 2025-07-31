# block_analysis.py
# 🧩 Analyzes prefab voxel data to identify visible blocks and group them into semantic categories

from collections import defaultdict
from filters import BLOCK_CATEGORY_ALIASES  # centralized alias map for category classification
# from block_parser import get_color_for_block

### 🧩 Categorize Visible Blocks: Returns category for each visible block_id
def categorize_blocks(block_ids, block_names):
	"""
	Given a list/set of visible block IDs, return a dict mapping each to a category string.
	"""
	return {block_id: classify_block(block_names.get(block_id, "")) for block_id in block_ids}

### 🧩 Block Classifier: Categorizes each block name using alias mapping and fallback heuristics
def classify_block(block_name):
	"""
	Categorizes a block name into a semantic type using substring matching and alias mapping.
	Prioritizes explicit mappings from filters.py, then applies lightweight heuristics.
	"""
	name = block_name.lower()

	# Alias map (catch explicit keywords like "plank", "tv", "barrel")
	for keyword, category in BLOCK_CATEGORY_ALIASES.items():
		if keyword in name:
			return category

	# Fallback heuristics (minimal and safe)
	if "wood" in name:
		return "wood"
	if "metal" in name or "truss" in name:
		return "metal"
	if "concrete" in name or "cobble" in name:
		return "concrete"
	if "terrain" in name:
		return "terrain"
	if "roof" in name:
		return "roof"
	if "light" in name:
		return "light"
	if "air" in name:
		return "air"

	return "unknown"
'''
### 🧩 Surface Block Extractor: Returns topmost block name per (x, z)
def get_top_block_surface(prefab, block_names, air_id=0):
	layers = prefab["layers"]
	size_z = len(layers)
	size_y = len(layers[0])
	size_x = len(layers[0][0])
	surface = []

	for y in range(size_y):
		row = []
		for x in range(size_x):
			block = "air"
			for z in reversed(range(size_z)):
				block_id = layers[z][y][x]
				if block_id != air_id:
					block = block_names.get(block_id, f"unknown_{block_id}")
					break
			row.append(block)
		surface.append(row)

	return surface

### 🧩 Top Block Analyzer: Extract the topmost non-air block for each x,z column
def count_top_visible_blocks(prefab, block_names, air_id=0):
	"""
	Returns a dict of {block_name: count} for the topmost visible blocks in the prefab.
	"""
	size_x, size_y, size_z = prefab["size_x"], prefab["size_y"], prefab["size_z"]
	layers = prefab["layers"]

	counts = defaultdict(int)

	for z in range(size_z):
		for x in range(size_x):
			for y in reversed(range(size_y)):  # top-down
				block_id = layers[z][y][x]
				if block_id != air_id:
					block_name = block_names.get(block_id, f"unknown_{block_id}")
					counts[block_name] += 1
					break  # only the top block matters

	return dict(counts)
'''

### 🧩 Block Category Collapser: Reduces block_name → count to category → total count
def count_block_categories(block_counts):
	"""
	Converts a block_name → count dict into category → total count.
	Uses classify_block() to group semantically similar blocks.
	"""
	category_counts = defaultdict(int)
	for block_name, count in block_counts.items():
		category = classify_block(block_name)
		category_counts[category] += count
	return dict(category_counts)


### 🖼️ Category Surface Builder: Produces a 2D grid of category tags from top layer
def categorize_surface(prefab, block_names):
	"""
	Creates a 2D grid of category labels from the topmost visible (non-air) block in each column.
	Returns a 2D list: surface[z][x] = category
	"""
	layers = prefab["layers"]
	size_z = len(layers)            # vertical height
	size_y = len(layers[0])         # rows (world Z)
	size_x = len(layers[0][0])      # columns (world X)

	surface = []

	for y in range(size_y):  # world Z (rows)
		row = []
		for x in range(size_x):  # world X (columns)
			category = "air"  # fallback
			for z in reversed(range(size_z)):  # top-down
				block_id = layers[z][y][x]
				if block_id != 0:  # ✅ no need to look up 'air'
					block_name = block_names.get(block_id, f"unknown_{block_id}")
					category = classify_block(block_name)
					break
			row.append(category)
		surface.append(row)

	return surface

### Logging debug
import csv

def save_debug_block_map(prefab, block_names, output_path="block_map_debug.csv", air_id=0):
	"""
	Logs block_id → name → category for the topmost visible blocks in the prefab.
	"""
	seen_ids = set()
	records = []

	size_x, size_y, size_z = prefab["size_x"], prefab["size_y"], prefab["size_z"]
	layers = prefab["layers"]

	for z in range(size_z):
		for x in range(size_x):
			for y in reversed(range(size_y)):
				block_id = layers[z][y][x]
				if block_id != air_id and block_id not in seen_ids:
					name = block_names.get(block_id, f"unknown_{block_id}")
					category = classify_block(name)
					records.append((block_id, name, category))
					seen_ids.add(block_id)
					break  # only topmost block per column

	with open(output_path, "w", newline='') as f:
		writer = csv.writer(f)
		writer.writerow(["block_id", "block_name", "category"])
		for rec in sorted(records, key=lambda r: r[0]):
			writer.writerow(rec)

	print(f"📝 Debug block map saved to: {output_path}")
