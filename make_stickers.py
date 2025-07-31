# make_stickers.py (finalized)

import os
import argparse
from block_parser import load_block_names, load_tts
from sticker_render import render_sticker
from helper import get_args, Config
from render import render_top_blocks

def process_prefab(tts_path, blocks_path, output_dir, blocks_xml_path):
	base_name = os.path.splitext(os.path.basename(tts_path))[0]
	print(f"📦 Processing: {os.path.basename(tts_path)}")

	# 🎨 Render image using block tops
	image = render_top_blocks(tts_path, blocks_path, blocks_xml_path)

	# 💾 Save the image
	output_png = os.path.join(output_dir, f"{base_name}.png")
	image.save(output_png)
	print(f"🖼️ Saved sticker: {output_png}")
	
def main():
	parser = argparse.ArgumentParser(description="Render prefab sticker images from .tts and .blocks.nim files")
	parser.add_argument("--prefab-dir", help="Directory containing prefab .tts and .blocks.nim files", required=True)
	parser.add_argument("--output-dir", help="Directory to save sticker PNGs and debug logs", default="stickers")
	args = get_args()
	config = Config(args)
	print(f"🔍 Scanning prefab directory: {config.prefab_dir}")
	print(f"📁 Directory contents (first 10 files): {os.listdir(config.prefab_dir)[:10]}")

	os.makedirs(args.output or "stickers", exist_ok=True)

	print(f"🔍 Scanning for prefabs in: {config.prefab_dir}")
	for root, _, files in os.walk(config.prefab_dir):
		for filename in files:
			if filename.endswith(".tts"):
				base = filename[:-4]
				tts_path = os.path.join(root, filename)
				blocks_path = os.path.join(root, base + ".blocks.nim")
	
				if os.path.exists(blocks_path):
					print(f"✅ Found pair: {base}")
					process_prefab(tts_path, blocks_path, args.output or "stickers", config.default_blocks_path)
				else:
					print(f"⚠️ Skipping {base} — missing .blocks.nim")


if __name__ == "__main__":
	main()
