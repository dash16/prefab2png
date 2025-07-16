# tts_decode.py — Batch prefab renderer with top-down PNG export
import struct, os, random, pygame, xml.etree.ElementTree as ET, sys, argparse
import time
import sys

pygame.init()
sys.path.append(".")
from helper import Config

### 🧩 Robust Block Name Extractor: Scans binary for UTF-8 strings with known block patterns
def load_block_names(blocks_path):
	import re
	block_names = {}
	try:
		with open(blocks_path, "rb") as f:
			data = f.read()

		# Extract all plausible UTF-8 strings (min 4 chars)
		pattern = rb'[a-zA-Z0-9:_]{4,}'
		matches = re.findall(pattern, data)

		# Filter known block name patterns
		valid_names = [m.decode("utf-8") for m in matches if any(p in m.decode("utf-8", errors="ignore") for p in (
			"Shapes:", "cnt", "wood", "glass", "metal", "terrain", "roof", "concrete", "bulletproof", "light", "fence"
		))]

		# Assign sequential IDs
		for i, name in enumerate(valid_names):
			block_names[i] = name

	except Exception as e:
		print(f"⚠️ Could not load blocks from {blocks_path}: {e}")

	print(f"📦 Extracted {len(block_names)} block names from {os.path.basename(blocks_path)}")
	return block_names

# Dummy args for Config path resolution
dummy_args = argparse.Namespace(
	xml=None, localization=None, biomes=None, prefab_dir=None,
	verbose=False, with_player_starts=False, numbered_dots=False,
	no_mask=False, log_missing=False, combined=False,
	text_size=18, extended_placement_debug=False, log_bounds=False,
	show_all_labels=False, log_poi_ids=False, mask_path=None,
	force_biome=None, custom_output_name=None
)

args = None  # Global placeholder to be set in main()

def unpack(bin_file, data_type, length_arg=0):
	if data_type == "i" or data_type == "I":
		return int(struct.unpack(data_type, bin_file.read(4))[0])
	elif data_type == "h" or data_type == "H":
		return int(struct.unpack(data_type, bin_file.read(2))[0])
	elif data_type == "s":
		return struct.unpack(str(length_arg) + data_type, bin_file.read(length_arg))[0]
	elif data_type == "c":
		return struct.unpack(data_type, bin_file.read(1))[0]
	elif data_type == "b" or data_type == "B":
		return int(struct.unpack(data_type, bin_file.read(1))[0])

def get_prefab_rotation(prefab_name, xml_path=None):
	if xml_path is None:
		xml_path, _, _, _ = Config(dummy_args).resolve_paths()
	try:
		tree = ET.parse(xml_path)
		root = tree.getroot()
		for deco in root.findall("decoration"):
			if deco.attrib.get("name") == prefab_name:
				return int(deco.attrib.get("rotation", 0))
	except Exception as e:
		print(f"⚠️ Failed to read rotation from {xml_path}: {e}")
	return 0

### 🧩 Topdown Visibility Counter: Identifies blocks visible from above using air scan
def count_top_visible_blocks(prefab, air_id=0):
	from collections import Counter
	visible_blocks = Counter()
	size_x = prefab["size_x"]
	size_y = prefab["size_y"]
	size_z = prefab["size_z"]
	layers = prefab["layers"]

	for z in range(size_z):
		for x in range(size_x):
			for y in reversed(range(size_y)):  # top-down
				block_id = layers[z][y][x]
				if block_id != air_id:
					visible_blocks[block_id] += 1
					break
	return visible_blocks

def draw_prefab_topdown(prefab, prefab_name, block_names=None, output_dir="output_tiles", verbose_csv=False):
	print(f"🧪 BLOCK_NAMES keys: {list(block_names.keys())[:10]}" if block_names else "❌ No block names loaded!")
	### 🧩 Safe semantic coloring for top-down prefab render
	colors = {}
	color_log = {}

	width = prefab["size_x"]
	height = prefab["size_z"]
	image = pygame.surface.Surface((width, height))

	for z in range(height):
		for x in range(width):
			block_id = 0
			for y in reversed(range(prefab["size_y"])):
				block_id = prefab["layers"][z][y][x]
				if block_id != 0:
					break

			if block_id != 0:
				if block_id not in colors:
					block_name = block_names.get(block_id, f"id_{block_id}").lower() if block_names else f"id_{block_id}"
					
					if args.random_colors_only:
							color = (random.randint(80, 200), random.randint(80, 200), random.randint(80, 200))  # Pure random
					else:
						### 🎨 Refined Block Name to Color Mapping (minimizes false positives)
						if block_name.startswith("terrainFiller"):
							color = (200, 176, 128)  # Light tan soil
						elif block_name.startswith("terrGravel"):
							color = (130, 120, 110)  # Grayish gravel
						elif block_name.startswith("terrDirt"):
							color = (145, 115, 85)   # Darker soil tone
						elif block_name.startswith("concreteShapes:"):
							color = (150, 150, 150)
						elif block_name.startswith("woodShapes:"):
							color = (140, 100, 70)
						elif block_name.startswith("brickShapes:"):
							color = (200, 100, 100)
						elif block_name.startswith("corrugatedMetalShapes:"):
							color = (110, 110, 130)
						elif block_name.startswith("glass"):
							color = (90, 170, 255)
						elif block_name.startswith("cnt"):
							color = None  # Skip containers
						elif "fence" in block_name:
							color = (170, 170, 170)
						elif "light" in block_name:
							color = (255, 255, 150)
						elif "roof" in block_name:
							color = (180, 50, 50)
						elif "asphalt" in block_name or "road" in block_name:
							color = (80, 80, 80)
						elif "grass" in block_name:
							color = (70, 120, 60)
						elif "air" in block_name or "terrainfiller" in block_name:
							color = None  # Invisible or ground
						else:
							color = (random.randint(80, 200),) * 3  # fallback noise
			
					colors[block_id] = color
					color_log[block_id] = color
				else:
					color = colors[block_id]
			
				if color:
					image.set_at((x, height - 1 - z), color)


	# Rotate based on prefabs.xml
	rotation = get_prefab_rotation(prefab_name)
	if rotation == 1:
		image = pygame.transform.rotate(image, -90)
	elif rotation == 2:
		image = pygame.transform.rotate(image, 180)
	elif rotation == 3:
		image = pygame.transform.rotate(image, 90)

	# Save PNG
	os.makedirs(output_dir, exist_ok=True)
	out_path = os.path.join(output_dir, f"{prefab_name}.png")
	pygame.image.save(image, out_path)
	print(f"✅ Rendered: {prefab_name} → {out_path}")
	#blocks.nim debug
	if block_names:
		sample_ids = list(block_names.items())[:10]
		print(f"🔍 Sample loaded block_names: {sample_ids}")
	else:
		print("❌ No block names loaded.")
		#blocks.nim debug
	# Prepare and write CSV log
	from collections import Counter
	
	# Count topmost block occurrences
	block_counter = Counter()
	for z in range(height):
		for x in range(width):
			block_id = 0
			for y in reversed(range(prefab["size_y"])):
				block_id = prefab["layers"][z][y][x]
				if block_id != 0:
					break
			if block_id != 0:
				block_counter[block_id] += 1
				
	# 🔍 Diagnostic: Show range and mapping of used block IDs
	if color_log:
		bid_keys = list(color_log.keys())
		print(f"🔎 block_ids used in render: total={len(bid_keys)}, min={min(bid_keys)}, max={max(bid_keys)}")
	
		sample_ids = sorted(bid_keys)[:10]
		for bid in sample_ids:
			if block_names and bid in block_names:
				name = block_names[bid]
			else:
				name = f"id_{bid}"
			print(f"🧱 {bid} → {name}")
	else:
		print("⚠️ No block_ids recorded for color_log.")
	
	# --- Top-visible blocks from air-scan logic ---
	top_visible = count_top_visible_blocks(prefab)
	if top_visible:
		print(f"🔍 Top-exposed blocks: {len(top_visible)} unique")
		for bid, count in top_visible.most_common(10):
			name = block_names.get(bid, f"id_{bid}") if block_names else f"id_{bid}"
			print(f"🧱 Visible from top: {bid} → {name} (count: {count})")
	
	csv_out = os.path.join(output_dir, f"{prefab_name}_blockmap_named.csv")
	
	if verbose_csv:
		with open(csv_out, "w") as f:
			f.write("block_id,block_name,label,r,g,b,count\n")
			for bid, rgb in sorted(color_log.items()):
				if block_names and bid in block_names:
					bname = block_names[bid]
				else:
					bname = f"id_{bid}"
				lname = bname.lower()
				label = "unknown"
				for keyword in [
					"counter", "vendor", "trader",
					"grass", "asphalt", "road", "concrete", "metal", "roof", "glass",
					"brick", "wood", "fence", "light", "air", "terrainfiller", "terrain"
				]:
					if keyword in lname:
						label = keyword
						break
				count = block_counter.get(bid, 0)
				if rgb:
					f.write(f"{bid},{bname},{label},{rgb[0]},{rgb[1]},{rgb[2]},{count}\n")
				else:
					f.write(f"{bid},{bname},{label},,,{count}\n")
	else:
		with open(csv_out, "w") as f:
			f.write("block_id,r,g,b\n")
			for bid, rgb in sorted(color_log.items()):
				if rgb:
					f.write(f"{bid},{rgb[0]},{rgb[1]},{rgb[2]}\n")
	
	# Log csv write to console
	print(f"🧱 Block name map saved to: {csv_out}")
	# 🧩 NEW: Top-visible blockmap CSV
	top_csv = os.path.join(output_dir, f"{prefab_name}_top_visible_blockmap.csv")
	with open(top_csv, "w") as f:
		f.write("block_id,block_name,count\n")
		for bid, count in top_visible.most_common():
			bname = block_names.get(bid, f"id_{bid}") if block_names else f"id_{bid}"
			f.write(f"{bid},{bname},{count}\n")
	print(f"📤 Top-visible block map saved to: {top_csv}")

def load_tts(filepath):
	with open(filepath, "rb") as bin_file:
		prefab = {}
		prefab["header"] = unpack(bin_file, "s", 4)
		prefab["version"] = unpack(bin_file, "I")
		prefab["size_x"] = unpack(bin_file, "H")
		prefab["size_y"] = unpack(bin_file, "H")
		prefab["size_z"] = unpack(bin_file, "H")
		prefab["layers"] = []
		for z in range(prefab["size_z"]):
			layer = []
			for y in range(prefab["size_y"]):
				row = []
				for x in range(prefab["size_x"]):
					value = unpack(bin_file, "I")
					block_id = value & 2047
					row.append(block_id)
				layer.append(row)
			prefab["layers"].append(layer)
	return prefab

def main():
	global args
	parser = argparse.ArgumentParser(description="Render .tts prefab(s) to top-down PNGs.")
	parser.add_argument("--tts", help="Path to a single .tts file")
	parser.add_argument("--batch", action="store_true", help="Process all .tts files in prefab_dir")
	parser.add_argument("--verbose-csv", action="store_true", help="Include detailed block metadata in the CSV output.")
	parser.add_argument("--random-colors-only", action="store_true", help="Render using only random colors (ignore block name rules)")
	args = parser.parse_args()

	if args.tts:
		file = args.tts
		if not os.path.exists(file):
			print(f"❌ File not found: {file}")
			return
		prefab_name = os.path.splitext(os.path.basename(file))[0]
		blocks_path = file.replace(".tts", ".blocks.nim")
		block_names = load_block_names(blocks_path) if os.path.exists(blocks_path) else None
		prefab = load_tts(file)
		draw_prefab_topdown(prefab, prefab_name, block_names, "output_tiles", verbose_csv=args.verbose_csv)

	elif args.batch:
		_, _, _, prefab_dir = Config(dummy_args).resolve_paths()
		tts_files = []
		for root, _, files in os.walk(prefab_dir):
			for f in files:
				lower_name = f.lower()
				if f.endswith(".tts") and not (lower_name.startswith("aaa_") or lower_name.startswith("000_")):
					full_path = os.path.join(root, f)
					tts_files.append(full_path)
		print(f"🔍 Found {len(tts_files)} prefab files in {prefab_dir}")
		os.makedirs("output_tiles", exist_ok=True)
		log_path = os.path.join("output_tiles", "00_batch_render_log.txt")
		log_file = open(log_path, "w")
		sys.stdout = log_file
		batch_start = time.time()
		for full_path in tts_files:
			prefab_name = os.path.splitext(os.path.basename(full_path))[0]
			blocks_path = full_path.replace(".tts", ".blocks.nim")
			block_names = load_block_names(blocks_path) if os.path.exists(blocks_path) else None
			try:
				prefab = load_tts(full_path)
				draw_prefab_topdown(prefab, prefab_name, block_names, "output_tiles", verbose_csv=args.verbose_csv)
			except Exception as e:
				print(f"❌ Failed to process {prefab_name}: {e}")
		batch_end = time.time()
		total = batch_end - batch_start
		print(f"\n🏁 Finished batch render of {len(tts_files)} prefabs in {total:.2f} seconds")
		sys.stdout = sys.__stdout__
		print(f"\n🏁 Finished batch render of {len(tts_files)} prefabs in {total:.2f} seconds")
		print(f"📄 Batch log saved to: {log_path}")
	else:
		print("⚠️ Please provide --tts or --batch")



if __name__ == "__main__":
	main()
