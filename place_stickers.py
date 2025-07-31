### 🧩 POI Sticker Placer: Places prefab "stickers" on the terrain canvas using coordinates from prefabs.xml

import os
import glob
from PIL import Image
from helper import Config, get_args, load_prefabs_from_xml, transform_coords, get_rotation_to_north
from parse import load_display_names
import xml.etree.ElementTree as ET
import numpy as np
args = get_args()
config = Config(args)
display_names = load_display_names(config.localization_path)
prefabs = load_prefabs_from_xml(config.xml_path)
tree = ET.parse(config.xml_path)
root = tree.getroot()
prefab_elements = root.findall("decoration")

### 🧩 Sticker Loader: Attempts to load a PNG prefab image from known filename formats
def load_sticker(name, directory):
	candidates = [
		os.path.join(directory, f"{name}.png"),
		os.path.join(directory, f"{name.lower()}.png"),
		os.path.join(directory, f"{name}.PNG")
	]
	for path in candidates:
		if os.path.exists(path):
			return Image.open(path).convert("RGBA")
	return None

### 🧩 Missing Sticker Logger: Tracks prefabs that had no matching PNG and logs them
def log_missing_sticker(name, log_path):
	os.makedirs(os.path.dirname(log_path), exist_ok=True)
	with open(log_path, "a", encoding="utf-8") as f:
		f.write(f"{name}\n")

### 🧩 Main Overlay Routine: Loads terrain canvas and overlays each valid POI sticker

### 🧭 Get prefab rotation from XML
def get_prefab_rotation(name):
	for elem in prefab_elements:
		if elem.get("name", "").lower() == name.lower():
			return int(elem.get("rotation", "0"))
	return 0

def place_stickers():
	config.resolve_paths()
	import datetime
	timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
	config.output_dir = f"output_sticker_overlay__{timestamp}"
		
	# 🔍 Auto-detect latest terrain image
	terrain_candidates = sorted(glob.glob("output_terrain_*/terrain_biome_shaded_final.png"), reverse=True)
	if not terrain_candidates:
		raise FileNotFoundError("❌ No terrain image found in any output_terrain_* folder.")
	terrain_path = terrain_candidates[0]

	# 🔍 Auto-detect latest sticker folder
	sticker_folders = sorted(glob.glob("output_stickers_*"), reverse=True)
	if not sticker_folders:
		raise FileNotFoundError("❌ No sticker folders found matching output_stickers_*")
	stickers_path = sticker_folders[0]
	os.makedirs(config.output_dir, exist_ok=True)
	output_path = os.path.join(config.output_dir, "sticker_overlay.png")
	log_path = os.path.join(config.log_dir or config.output_dir, "missing_stickers.txt")
	debug_log_path = os.path.join(config.output_dir, "sticker_debug_log.csv")
	debug_log = open(debug_log_path, "w", encoding="utf-8")

	# --- 🖼️ Load base terrain and prepare layers ---
	base_img = Image.open(terrain_path).convert("RGBA")
	rwg_img = Image.new("RGBA", base_img.size, (0, 0, 0, 0))            # Only RWG tiles
	sticker_only_img = Image.new("RGBA", base_img.size, (0, 0, 0, 0))   # All non-RWG POIs
	debug_log.write("prefab_name,display_name,rotation,width,height,x,z,draw_x,draw_z\n")


	# --- 📍 Load prefab positions from XML ---

	count = 0
	for poi_id, name, x, z in prefabs:
	
		sticker = load_sticker(name, stickers_path)
		if sticker is None:
			log_missing_sticker(name, log_path)
			continue
		
		rotation = get_prefab_rotation(name)  # from world XML
		authored_facing = get_rotation_to_north(name, config.prefab_dir)  # from prefab XML
		# Net rotation needed = how much you must rotate the prefab sticker to match world rotation
		net_rotation = (rotation - authored_facing) % 4

		if net_rotation == 1:
			sticker = sticker.rotate(-90, expand=True)
		elif net_rotation == 2:
			sticker = sticker.rotate(180, expand=True)
		elif net_rotation == 3:
			sticker = sticker.rotate(90, expand=True)
		
		# Calculate adjusted top-left position to center the sticker
		w, h = sticker.size
		draw_x, draw_z = transform_coords(x, z, config.map_center)
		draw_z -= h
		
		display_name = display_names.get(name, "")
		debug_log.write(f"{name},{display_name},{rotation},{w},{h},{x},{z},{draw_x},{draw_z}\n")
	
		### 🧩 RWG Tile Soft Blend (LERP with terrain background)
		if name.startswith("rwg_tile"):
			sticker = sticker.copy()
			sx, sy = sticker.size
			crop_box = (draw_x, draw_z, draw_x + sx, draw_z + sy)
			terrain_crop = base_img.crop(crop_box).convert("RGBA")
			
			# Prepare sticker and background as arrays
			sticker_arr = np.array(sticker).astype(np.float32)
			terrain_arr = np.array(terrain_crop).astype(np.float32)
		
			# Blend the RGB channels, preserve alpha
			blend_factor = 0.5  # 0 = only terrain, 1 = only sticker
			blended_rgb = (
				(1 - blend_factor) * terrain_arr[..., :3] +
				blend_factor * sticker_arr[..., :3]
			).astype(np.uint8)
		
			alpha = sticker_arr[..., 3].astype(np.uint8)
			blended_arr = np.dstack((blended_rgb, alpha))
		
			# Convert back to RGBA image
			blended = Image.fromarray(blended_arr, mode="RGBA")
			rwg_img.paste(blended, (draw_x, draw_z), blended)
		else:
			base_img.paste(sticker, (draw_x, draw_z), sticker)
			sticker_only_img.paste(sticker, (draw_x, draw_z), sticker)
	
		count += 1
	
	# --- 💾 Save outputs ---
	output_path = os.path.join(config.output_dir, "sticker_overlay.png")
	base_img.save(output_path)
	
	rwg_path = os.path.join(config.output_dir, "sticker_rwg_tiles_only.png")
	rwg_img.save(rwg_path)
	
	sticker_only_path = os.path.join(config.output_dir, "stickers_only.png")
	sticker_only_img.save(sticker_only_path)
	
	# --- 🧾 Done ---
	print(f"✅ Placed {count} POI stickers.")
	print(f"🗂️ RWG tiles saved to: {rwg_path}")
	print(f"🖼️ Sticker-only layer saved to: {sticker_only_path}")
	print(f"🖼️ Terrain + POIs saved to: {output_path}")
	debug_log.close()

if __name__ == "__main__":
	place_stickers()
