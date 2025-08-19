# make_stickers.py 

import os
import time
from datetime import datetime
from helper import get_args, Config
from render import render_top_blocks
import block_analysis
# silence noisy console prints
VERBOSE = False
def set_verbose(value: bool):
	"""Enable or disable verbose debug output for this module."""
	global VERBOSE
	VERBOSE = bool(value)
	
def process_prefab(tts_path, blocks_path, output_dir, blocks_xml_path, config):
	base_name = os.path.splitext(os.path.basename(tts_path))[0]
	print(f"📦 Processing: {os.path.basename(tts_path)}")

	# 🎨 Render image using block tops
	image = render_top_blocks(tts_path, blocks_path, blocks_xml_path, config)

	# 💾 Save the image
	output_png = os.path.join(output_dir, f"{base_name}.png")
	image.save(output_png)
	if VERBOSE:
		print(f"🖼️ Saved sticker: {output_png}")
	
def main():
	start_time = time.perf_counter()
	args = get_args()
	config = Config(args)
	block_analysis.set_verbose(args.verbose)
	'''
	with open("verbose_log.txt", "a", encoding="utf-8") as f:
		def log_both(msg):
			print(msg)
			print(msg, file=f)
		config.log_resolved_paths_once(log=log_both)
	'''
	print(f"🔍 Scanning prefab directory: {config.prefab_dir}")

	timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
	output_dir = f"stickers__{timestamp}"
	os.makedirs(output_dir, exist_ok=True)
	print(f"📁 Output directory: {output_dir}")

# Walk the prefab dir and render any .tts that have a matching .blocks.nim
	print(f"🔍 Scanning for prefabs in: {config.prefab_dir}")
	for root, _, files in os.walk(config.prefab_dir):
		for filename in files:
			if filename.endswith(".tts"):
				base = filename[:-4]
				tts_path = os.path.join(root, filename)
				blocks_path = os.path.join(root, base + ".blocks.nim")
	
				if os.path.exists(blocks_path):
					if VERBOSE:
						print(f"✅ Found pair: {base}")
					process_prefab(tts_path, blocks_path, output_dir, config.default_blocks_path, config)
				else:
					print(f"⚠️ Skipping {base} — missing .blocks.nim") # warning, keep printing to console if found

	duration = time.perf_counter() - start_time
	print(f"\n⏱️ Total render time: {duration:.2f} seconds")

if __name__ == "__main__":
	main()
