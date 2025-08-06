### 🧩 POI Sticker Placer: Places prefab "stickers" on the terrain canvas using coordinates from prefabs.xml

import os
import glob
from PIL import Image
from helper import Config, get_args, load_prefabs_from_xml, transform_coords, get_rotation_to_north, rotate_poi_within_tile, parse_embedded_pois
from parse import load_display_names
import xml.etree.ElementTree as ET
import numpy as np
import datetime

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

### 🧩 Global RWG Tile Registry
RWG_TILE_SIZE = 150

def get_rwg_tile_bounds(name, x, z, rotation):
	if rotation % 2 == 0:
		w, h = RWG_TILE_SIZE, RWG_TILE_SIZE
	else:
		w, h = RWG_TILE_SIZE, RWG_TILE_SIZE  # same footprint due to square tiles

	return {
		"name": name,
		"x": x,
		"z": z,
		"rotation": rotation,
		"x_min": x,
		"x_max": x + w,
		"z_min": z,
		"z_max": z + h
	}

### 🧩 Main Overlay Routine: Loads terrain canvas and overlays each valid POI sticker
def place_stickers():
	config.resolve_paths()
	import datetime
	timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
	config.output_dir = f"output_sticker_overlay__{timestamp}"

	# Load terrain and sticker layers
	terrain_candidates = sorted(glob.glob("output_terrain_*/terrain_biome_shaded_final.png"), reverse=True)
	if not terrain_candidates:
		raise FileNotFoundError("❌ No terrain image found.")
	terrain_path = terrain_candidates[0]

	sticker_folders = sorted(glob.glob("stickers_*"), reverse=True)
	if not sticker_folders:
		raise FileNotFoundError("❌ No sticker folders found.")
	stickers_path = sticker_folders[0]

	os.makedirs(config.output_dir, exist_ok=True)
	log_path = os.path.join(config.log_dir or config.output_dir, "missing_stickers.txt")
	debug_log_path = os.path.join(config.output_dir, "sticker_debug_log.csv")
	debug_log = open(debug_log_path, "w", encoding="utf-8")

	# --- 🖼️ Load base terrain and prepare layers ---
	base_img = Image.open(terrain_path).convert("RGBA")
	rwg_img = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
	sticker_only_img = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
	debug_log.write("name,display_name,rotation,rotation_to_north,net_rotation,net_degrees,w,h,x,z,draw_x,draw_z\n")

	rwg_tiles = []
	count = 0

	# --- Pass 1: Place RWG tiles ---
	for poi in prefabs:
		name = poi["name"]
		if not name.startswith("rwg_tile"):
			continue

		x, z, rotation = poi["x"], poi["z"], poi["rotation"]
		display_name = display_names.get(name, "")
		sticker = load_sticker(name, stickers_path)
		if not sticker:
			log_missing_sticker(name, log_path)
			continue

		sticker = sticker.transpose(Image.FLIP_LEFT_RIGHT)
		rotation_to_north = get_rotation_to_north(name, config.prefab_dir)
		if config.verbose:
			print(f"🧭 {name} → RotationToFaceNorth: {rotation_to_north}")
		
		# Compute net rotation
		# ⛔ List of RWG tiles to exclude from global 180° rotation
		no_global_flip = {
			"rwg_tile_gateway_intersection2",
			"rwg_tile_gateway_straight3b",
			"rwg_tile_gateway_straight3a",
			"rwg_tile_gateway_straight3",
			"rwg_tile_gateway_t"
		}
		rotation_adjust = 2 if name not in no_global_flip else 0
		net_rotation = (rotation + rotation_to_north + rotation_adjust) % 4
		# 🧩 Manual rotation fix for specific known tile(s)
		if name == "rwg_tile_gateway_t":
			net_rotation = (net_rotation + 3) % 4  # +270°
			if config.verbose:
				print(f"🛠️ Applied +270° manual fix for: {name}")
		net_degrees = net_rotation * 90
		
		# Apply rotation to image
		if net_rotation in [1, 2, 3]:
			sticker = sticker.rotate(net_degrees, expand=True)
			if config.verbose:
				print(f"🧭 Rotated RWG tile {name} by {net_degrees}°")
		if config.verbose and name in no_global_flip:
			print(f"⛔ Skipping global 180° flip for: {name}")

		# Draw it
		w, h = sticker.size
		draw_x, draw_z = transform_coords(x, z, config.map_center)
		draw_z -= h
		
		debug_log.write(f"{name},{display_name},{rotation},{rotation_to_north},{net_rotation},{net_degrees},{w},{h},{x},{z},{draw_x},{draw_z}\n")
		if config.verbose:
			print(f"🧱 Placed RWG tile: {name} at ({x}, {z}) with rotation {rotation} → north {rotation_to_north}")
		if not sticker:
			print(f"⚠️ Missing sticker for RWG tile: {name}")
			
		# Blend onto terrain
		sx, sy = sticker.size
		crop_box = (draw_x, draw_z, draw_x + sx, draw_z + sy)
		terrain_crop = base_img.crop(crop_box).convert("RGBA")
		sticker_arr = np.array(sticker).astype(np.float32)
		terrain_arr = np.array(terrain_crop).astype(np.float32)
		blended_rgb = ((1 - 0.5) * terrain_arr[..., :3] + 0.5 * sticker_arr[..., :3]).astype(np.uint8)
		alpha = sticker_arr[..., 3].astype(np.uint8)
		blended_arr = np.dstack((blended_rgb, alpha))
		blended = Image.fromarray(blended_arr, mode="RGBA")
		rwg_img.paste(blended, (draw_x, draw_z), blended)

		rwg_tiles.append(get_rwg_tile_bounds(name, x, z, rotation))
		count += 1

	# --- After RWG: Parse embedded POIs ---
	embedded_pois = []
	for tile in rwg_tiles:
		embedded = parse_embedded_pois(
			tile_name=tile["name"],
			tile_x=tile["x"],
			tile_z=tile["z"],
			tile_rotation=tile["rotation"],
			prefab_dir=config.prefab_dir
		)
		embedded_pois.extend(embedded)

	# --- Pass 2: Place all other POIs (including embedded) ---
	for poi in prefabs + embedded_pois:
		name = poi["name"]
		if name.startswith("rwg_tile"):
			continue

		x, z, rotation = poi["x"], poi["z"], poi["rotation"]
		display_name = display_names.get(name, "")
		sticker = load_sticker(name, stickers_path)
		if not sticker:
			log_missing_sticker(name, log_path)
			continue

		sticker = sticker.transpose(Image.FLIP_LEFT_RIGHT)

		# --- Check if this POI is inside an RWG tile ---
		containing_tile = None
		for tile in rwg_tiles:
			if tile["x_min"] <= x < tile["x_max"] and tile["z_min"] <= z < tile["z_max"]:
				containing_tile = tile
				break

		# Adjust for tile rotation
		adjusted_rotation = rotation
		if containing_tile:
			tile_rot = containing_tile["rotation"]
			adjusted_rotation = (rotation + tile_rot) % 4

		# Apply prefab-facing logic
		authored_facing = get_rotation_to_north(name, config.prefab_dir)
		net_rotation = (adjusted_rotation - authored_facing) % 4
		if net_rotation == 1:
			sticker = sticker.rotate(90, expand=True)
		elif net_rotation == 2:
			sticker = sticker.rotate(180, expand=True)
		elif net_rotation == 3:
			sticker = sticker.rotate(-90, expand=True)

		# Calculate adjusted top-left position to center the sticker
		w, h = sticker.size
		draw_x, draw_z = transform_coords(x, z, config.map_center)
		draw_z -= h
		debug_log.write(f"{name},{display_name},{rotation},{w},{h},{x},{z},{draw_x},{draw_z}\n")
		if config.verbose:	
			print(f"📍 Placed POI: {name} at ({x}, {z}) rot={rotation} → net_rot={net_rotation}")
			if "parent_tile" in poi:
				print(f"🔄 Embedded POI inside {poi['parent_tile']}: {name}")

		base_img.paste(sticker, (draw_x, draw_z), sticker)
		sticker_only_img.paste(sticker, (draw_x, draw_z), sticker)
		count += 1

	# --- Save outputs ---
	output_overlay = os.path.join(config.output_dir, "sticker_overlay.png")
	output_rwg = os.path.join(config.output_dir, "sticker_rwg_tiles_only.png")
	output_stickers = os.path.join(config.output_dir, "stickers_only.png")
	
	base_img.save(output_overlay)
	rwg_img.save(output_rwg)
	sticker_only_img.save(output_stickers)
	debug_log.close()
	
	print(f"✅ Placed {count} POI stickers.")
	print(f"🗂️ RWG tiles saved to: {output_rwg}")
	print(f"🖼️ Sticker-only layer saved to: {output_stickers}")
	print(f"🖼️ Terrain + POIs saved to: {output_overlay}")

if __name__ == "__main__":
	place_stickers()