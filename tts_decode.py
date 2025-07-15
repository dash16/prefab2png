# tts_decode.py — Batch prefab renderer with top-down PNG export
import struct, os, random, pygame, xml.etree.ElementTree as ET, sys, argparse
import time
import sys

pygame.init()
sys.path.append(".")
from helper import Config

# Load .blocks.nim to map prefab blocks
def load_block_names(blocks_path):
	block_names = {}
	try:
		with open(blocks_path, "rb") as f:
			count = int.from_bytes(f.read(2), "little")
			for i in range(count):
				name_length = int.from_bytes(f.read(1), "little")
				name = f.read(name_length).decode("utf-8")
				block_names[i] = name
	except Exception as e:
		print(f"⚠️ Could not load blocks from {blocks_path}: {e}")
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

def draw_prefab_topdown(prefab, prefab_name, block_names=None, output_dir="output_tiles"):
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
					block_name = block_names.get(block_id, f"id_{block_id}") if block_names else f"id_{block_id}"
					if "grass" in block_name:
						color = (70, 120, 60)
					elif "asphalt" in block_name or "road" in block_name:
						color = (80, 80, 80)
					elif "concrete" in block_name:
						color = (150, 150, 150)
					elif "metal" in block_name:
						color = (110, 110, 130)
					elif "roof" in block_name:
						color = (180, 50, 50)
					elif "air" in block_name:
						color = (0, 0, 0)
					else:
						color = (random.randint(80,200), random.randint(80,200), random.randint(80,200))
					colors[block_id] = color
					color_log[block_id] = color
				else:
					color = colors[block_id]
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

	# Save block ID → block name → color
	csv_out = os.path.join(output_dir, f"{prefab_name}_blockmap_named.csv")
	with open(csv_out, "w") as f:
		for bid, rgb in sorted(color_log.items()):
			bname = block_names.get(bid, f"id_{bid}") if block_names else f"id_{bid}"
			f.write(f"{bid},{bname},{rgb[0]},{rgb[1]},{rgb[2]}\n")
	print(f"🧱 Block name map saved to: {csv_out}")


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
	parser = argparse.ArgumentParser(description="Render .tts prefab(s) to top-down PNGs.")
	parser.add_argument("--tts", help="Path to a single .tts file")
	parser.add_argument("--batch", action="store_true", help="Process all .tts files in prefab_dir")
	args = parser.parse_args()

	if args.tts:
		file = args.tts
		if not os.path.exists(file):
			print(f"❌ File not found: {file}")
			return
		name = os.path.splitext(os.path.basename(file))[0]
		blocks_path = file.replace(".tts", ".blocks.nim")
		block_names = load_block_names(blocks_path)
		prefab = load_tts(file)
		draw_prefab_topdown(prefab, prefab_name=name, block_names=block_names)
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
			name = os.path.splitext(os.path.basename(full_path))[0]
			blocks_path = full_path.replace(".tts", ".blocks.nim")
			block_names = load_block_names(blocks_path)
			try:
				prefab = load_tts(full_path)
				draw_prefab_topdown(prefab, prefab_name=name, block_names=block_names)
			except Exception as e:
				print(f"❌ Failed to process {name}: {e}")
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
