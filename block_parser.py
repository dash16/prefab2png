# block_parser.py
# 🧩 Prefab Block Parser: Decodes .blocks.nim and .tts files into usable structures

import struct
import os
import re
import random
from filters import BLOCK_CATEGORY_ALIASES, CATEGORY_COLORS

### 🧩 Block Name Parser: Decodes .blocks.nim using correct ID and UTF-8 format
def load_block_names(path):
	with open(path, "rb") as f:
		data = f.read()

	offset = 8  # Skip 8-byte file header
	block_names = {}

	while offset < len(data):
		try:
			# Read block ID (int32 little-endian)
			block_id = int.from_bytes(data[offset:offset+4], "little")
			offset += 4

			# Read 1 byte for name length
			name_len = data[offset]
			offset += 1

			# Read UTF-8 block name
			name_bytes = data[offset:offset+name_len]
			name = name_bytes.decode("utf-8", errors="replace")
			offset += name_len

			block_names[block_id] = name

		except Exception as e:
			print(f"❌ Failed at offset {offset}, block ID {block_id}: {e}")
			break

	print(f"✅ Parsed {len(block_names)} block names from .blocks.nim")
	for block_id, name in block_names.items():
#		print(f"🔍 ID {block_id} → {name}")
		return block_names


### 🧩 Block Color Loader: Loads both Map.Color and TintColor from blocks.xml
def load_block_colors(blocks_xml_path):
	import xml.etree.ElementTree as ET
	import re

	tree = ET.parse(blocks_xml_path)
	root = tree.getroot()

	block_colors = {}

	for block in root.findall("block"):
		name = block.get("name")
		rgb = None

		for prop in block.findall("property"):
			if prop.get("name") == "Map.Color":
				rgb_str = prop.get("value")
				if rgb_str:
					try:
						rgb = tuple(map(int, rgb_str.split(",")))
					except:
						pass

			# Fallback to TintColor if no Map.Color is present
			elif not rgb and prop.get("name") == "TintColor":
				tint = prop.get("value")
				if tint and re.fullmatch(r"#?[0-9A-Fa-f]{6,8}", tint):
					tint = tint.lstrip("#")
					# Trim alpha if present
					if len(tint) == 8:
						tint = tint[:6]
					try:
						rgb = tuple(int(tint[i:i+2], 16) for i in (0, 2, 4))
					except:
						pass

		if name and rgb:
			block_colors[name] = rgb

	print(f"🎨 Loaded {len(block_colors)} block colors (Map.Color + TintColor)")
	return block_colors

### 🧩 Block Color Fallback: Applies palette color from filters.py categories if XML/TintColor is missing
def apply_palette_from_filters(block_colors, block_names, filters):
	from filters import category_colors  # RGB triples
	from filters import categorize_block_name

	count = 0
	for block_id, name in block_names.items():
		if name not in block_colors:
			category = categorize_block_name(name)
			color = category_colors.get(category)
			if color:
				block_colors[name] = color
				count += 1

	print(f"🌈 Patched {count} block colors using category palette fallback")
	return block_colors

### 🧩 Binary Unpacker: Extracts typed values from .tts binary stream
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

### 🧩 Prefab TTS Loader: Reads .tts binary format and reconstructs 3D block data
def load_tts(filepath, local_palette=None):
	with open(filepath, "rb") as bin_file:
		header = unpack(bin_file, "s", 4)
		version = unpack(bin_file, "I")
		size_x = unpack(bin_file, "H")
		size_y = unpack(bin_file, "H")
		size_z = unpack(bin_file, "H")

		print(f"📏 Prefab dimensions: {size_x} x {size_y} x {size_z} (version {version})")

		prefab = {
			"version": version,
			"size_x": size_x,
			"size_y": size_y,
			"size_z": size_z,
			"layers": [],
			"block_names": {}
		}

		used_block_ids = set()

		for z in range(size_z):
			layer = []
			for y in range(size_y):
				row = []
				for x in range(size_x):
					value = unpack(bin_file, "I")
					block_id = value & 0x7FFF  # ✅ 15-bit mask to match TTS spec
					row.append(block_id)
					used_block_ids.add(block_id)
				layer.append(row)
			prefab["layers"].append(layer)

		for block_id in used_block_ids:
			name = None
			if local_palette:
				name = local_palette.get(block_id)
			if not name:
				name = f"unknown_{block_id}"
			prefab["block_names"][block_id] = name

	return prefab
