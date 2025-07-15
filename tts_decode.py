# tts_decode.py — Top-down prefab renderer with correct prefab2png integration
import struct
import os
import random
import pygame
import xml.etree.ElementTree as ET
import sys

pygame.init()

# 🧩 Import prefab2png config with OS-aware + CLI-aware paths
sys.path.append(".")
from helper import Config
import argparse

dummy_args = argparse.Namespace(
	xml=None,
	localization=None,
	biomes=None,
	prefab_dir=None,
	verbose=False,
	with_player_starts=False,
	numbered_dots=False,
	no_mask=False,
	log_missing=False,
	combined=False,
	text_size=18,
	extended_placement_debug=False,
	log_bounds=False,
	show_all_labels=False,
	log_poi_ids=False,
	mask_path=None,
	force_biome=None,
	custom_output_name=None
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

### 🧩 Rotation Fetcher: Gets prefab rotation from prefabs.xml
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

### 🧩 Top-Down View Renderer: Draws 2D overhead map using top visible block at each (x,z)
def draw_prefab_topdown(prefab, prefab_name=None):
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
					color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
					colors[block_id] = color
					color_log[block_id] = color
				else:
					color = colors[block_id]
				image.set_at((x, height - 1 - z), color)  # vertical flip

	# Apply prefab.xml rotation if name is provided
	if prefab_name:
		rotation = get_prefab_rotation(prefab_name)
		if rotation == 1:
			image = pygame.transform.rotate(image, -90)
		elif rotation == 2:
			image = pygame.transform.rotate(image, 180)
		elif rotation == 3:
			image = pygame.transform.rotate(image, 90)
		print(f"📐 Applied prefab rotation: {rotation * 90}°")

	# Save PNG
	output_name = f"output_topdown_{prefab_name}.png" if prefab_name else "output_topdown.png"
	pygame.image.save(image, output_name)
	print(f"✅ Saved: {output_name}")

	# Save block ID → color mapping
	with open("blockmap.csv", "w") as f:
		for bid, rgb in sorted(color_log.items()):
			f.write(f"{bid},{rgb[0]},{rgb[1]},{rgb[2]}\n")
	print("🗂️  Block ID → Color mapping saved to blockmap.csv")

def main():
	file_name = input("TTS FILE?: ").strip()
	if not os.path.exists(file_name):
		print("❌ File not found.")
		return

	prefab_name = os.path.splitext(os.path.basename(file_name))[0]

	with open(file_name, "rb") as bin_file:
		prefab = {}
		prefab["header"] = unpack(bin_file, "s", 4)
		prefab["version"] = unpack(bin_file, "I")
		prefab["size_x"] = unpack(bin_file, "H")
		prefab["size_y"] = unpack(bin_file, "H")
		prefab["size_z"] = unpack(bin_file, "H")

		print(f"📏 Dimensions: {prefab['size_x']} x {prefab['size_y']} x {prefab['size_z']}")

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

	draw_prefab_topdown(prefab, prefab_name=prefab_name)

if __name__ == "__main__":
	main()
