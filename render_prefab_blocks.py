### 🧪 render_prefab_blocks.py
# Standalone test render for prefab block tops using blocks.xml colors

import sys, os
from PIL import Image
from block_parser import load_tts, load_block_names, load_block_colors

def get_top_blocks(grid):
	sz = len(grid)
	sy = len(grid[0])
	sx = len(grid[0][0])
	top_blocks = {}

	for z in range(sz):
		for x in range(sx):
			for y in reversed(range(sy)):
				block_id = grid[z][y][x]
				if block_id != 0:
					top_blocks[(x, z)] = block_id
					break
	return top_blocks, sx, sz

def render_image(top_blocks, block_names, block_colors, sx, sz, out_path):
	from filters import BLOCK_CATEGORY_ALIASES, CATEGORY_COLORS
	image = Image.new("RGB", (sx, sz))
	pixels = image.load()

	for (x, z), block_id in top_blocks.items():
		name = block_names.get(block_id, f"unknown_{block_id}")
		rgb = block_colors.get(name)

		# 🟡 Fallback: use category alias logic
		if not rgb:
			cat = None
			for prefix, alias in BLOCK_CATEGORY_ALIASES.items():
				if name.startswith(prefix):
					cat = alias
					break
			if cat and cat in CATEGORY_COLORS:
				rgb = CATEGORY_COLORS[cat]

		if not rgb:
			print(f"❓ No color for block: {name}")
			rgb = (128, 128, 128)

		pixels[x, z] = rgb

	image.save(out_path)
	print(f"🖼️ Saved: {out_path}")

def main(tts_path, blocks_path, blocks_xml, out_path):
	print(f"📦 TTS: {tts_path}")
	print(f"🔢 BLOCKS: {blocks_path}")
	print(f"🎨 COLORS: {blocks_xml}")

	block_names = load_block_names(blocks_path)
	prefab = load_tts(tts_path, block_names)
	block_colors = load_block_colors(blocks_xml)

	top_blocks, sx, sz = get_top_blocks(prefab["layers"])
	# 🧪 Count occurrences of each block ID in top_blocks
	from collections import Counter
	block_id_counts = Counter(top_blocks.values())
	
	print(f"🔢 Unique top block IDs: {len(block_id_counts)}")
	for block_id, count in block_id_counts.most_common():
		name = block_names.get(block_id, f"unknown_{block_id}")
		print(f"🔍 ID {block_id:>4} → {name:<30} × {count}")

	render_image(top_blocks, prefab["block_names"], block_colors, sx, sz, out_path)

if __name__ == "__main__":
	if len(sys.argv) != 5:
		print("Usage:")
		print("  python3 render_prefab_blocks.py <.tts> <.blocks.nim> <blocks.xml> <output.png>")
		sys.exit(1)

	tts_path     = sys.argv[1]
	blocks_path  = sys.argv[2]
	blocks_xml   = sys.argv[3]
	out_path     = sys.argv[4]
	main(tts_path, blocks_path, blocks_xml, out_path)
