# helper.py
# Shared utility functions used across labeler.py and render.py

# ----------------------------------------------
# 📌 Roadmap Notes (for future cleanup/refactor)
# ----------------------------------------------
# - Migrate wedge drawing functions from render.py:
#	  • draw_label_wedge_only()
#	  • draw_label_text_only()
# - Consider adding a shared bbox helper: get_text_dimensions()
# - Evaluate rgb_distance and biome utils for relocation
# - Ensure helper.py does not rely on category, prefab, or rendering context
# - Split label placement vs drawing logic cleanly
# - Optional: auto-generation of red/blue zones based on POI clustering (v0.6+)

from PIL import ImageFont
import os
import datetime
import platform
import csv
import re
from filters import BLOCK_CATEGORY_ALIASES

VALID_BIOMES = {"pine_forest", "desert", "snow", "burnt_forest", "wasteland"}

def get_version():
	try:
		with open("version.txt", "r", encoding="utf-8") as f:
			return f.read().strip()
	except Exception:
		return "unknown"

# === CONFIGURATION ===
class Config:
	def __init__(self, args):
		self.args = args
		self.image_size = (6145, 6145)
		self.map_center = 3072
		self.dot_radius = 4
		self.font_size = args.text_size
		self.label_padding = 4

		self.output_dir = None
		self.combined_dir = None
		self.log_dir = None
		self.xml_path, self.localization_path, self.biome_path, self.prefab_dir = self.resolve_paths()
		self.font_path = self.resolve_font_path()
		self.font = self.load_font()

		self.verbose_log = None
		self.verbose_log_file = None
		self.missing_log = None
		self.excluded_log = None
		self.debug_extended = self.args.extended_placement_debug
		
	def resolve_paths(self):
		if platform.system() == "Windows":
			base = os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steamapps\common\7 Days To Die")
			default_xml = os.path.join(base, "Data/Worlds/Navezgane/prefabs.xml")
			default_localization = os.path.join(base, "Data/Config/Localization.txt")
			default_biomes = os.path.join(base, "Data/Worlds/Navezgane/biomes.png")
			default_prefab_dir = os.path.join(base, "Data/Prefabs")
			default_blocks = os.path.join(base, "Data/Config/blocks.xml")
		else:
			base = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/7 Days To Die/7DaysToDie.app/Data")
			default_xml = os.path.join(base, "Worlds/Navezgane/prefabs.xml")
			default_localization = os.path.join(base, "Config/Localization.txt")
			default_biomes = os.path.join(base, "Worlds/Navezgane/biomes.png")
			default_prefab_dir = os.path.join(base, "Prefabs")
			default_blocks = os.path.join(base, "Config/blocks.xml")
	
		# ✅ Always assign these
		xml = self.args.xml or default_xml
		localization = self.args.localization or default_localization
		biomes = self.args.biomes or default_biomes
		prefab_dir = self.args.prefab_dir or default_prefab_dir
	
		# ✅ Save blocks.xml
		self.default_blocks_path = default_blocks
	
		# Optional print
		if not self.args.xml:
			print("⚠️  No --xml argument provided. Defaulting to Navezgane prefab paths.")
		else:
			print("📂 Resolved paths:")
			print(f"   • XML:           {xml}")
			print(f"   • Localization:  {localization}")
			print(f"   • Biomes:        {biomes}")
			print(f"   • Prefab Dir:    {prefab_dir}")
	
		return xml, localization, biomes, prefab_dir

	def resolve_font_path(self):
		return "C:\\Windows\\Fonts\\arial.ttf" if platform.system() == "Windows" else "/System/Library/Fonts/Supplemental/Arial.ttf"

	def load_font(self):
		try:
			return ImageFont.truetype(self.font_path, self.font_size)
		except OSError:
			return ImageFont.load_default()

# === CLI ARGUMENTS ===
import argparse
parser = argparse.ArgumentParser(description="Render 7DTD prefab map layers.")
parser.add_argument(
	"--xml",
	type=str,
	help="Full path to 'prefabs.xml'"
)
parser.add_argument(
	"--localization",
	type=str,
	help="Full path to 'Localization.txt'"
)
parser.add_argument(
	"--biomes",
	type=str,
	help="Full path to 'biomes.png'"
)
parser.add_argument(
	"--prefab-dir",
	type=str,
	help="Full path to the prefab directory containing individual .xml files with prefab metadata (size, difficulty, etc)."
)
parser.add_argument(
	"--verbose",
	action="store_true",
	help="Enable verbose logging."
)
parser.add_argument(
	"--combined",
	action="store_true",
	help="Generate combined PNG layers."
)
parser.add_argument(
	"--with-player-starts",
	action="store_true",
	help="Include 'player_starts' layer which shows possible spawn locations."
)
parser.add_argument(
	"--log-missing",
	action="store_true",
	help="Log prefabs placed on the map that are missing a known Display Name."
)
parser.add_argument(
	"--numbered-dots",
	action="store_true",
	help="Replace prefab dots with unique POI IDs and draw full legend."
)
parser.add_argument(
	"--skip-layers",
	action="store_true",
   help="Skip rendering biome layers and go directly to legend rendering."	#This is a debug value to display just the legend box and contents
)
parser.add_argument(
	"--mask",
	action="store_true",
	help="Enable red/blue zone label placement from mask.gif"
)
parser.add_argument(
	"--only-biomes",
	nargs="+",
	metavar="BIOME",
	help="Only render the specified biome layers. Options: pine_forest, desert, snow, burnt_forest, wasteland."
)
parser.add_argument(
	"--version",
	action="version",
	version=f"prefab2png {get_version()}",
	help="Show the current prefab2png version and exit"
)
parser.add_argument(
	"--extended-placement-debug",
	action="store_true",
	help="Highlight labels placed during extended placement (Pass 4)"
)
parser.add_argument(
	"--text-size",
	type=int,
	default=25,
	help="Font size for POI labels. Default is 25. Max is 60."
)
parser.add_argument(
	"--blocks",
	help="Path to .blocks.nim file or folder (used for voxelmap rendering)"
)
parser.add_argument(
	"--prefab-xml",
	help="Matching .xml file for a single prefab (used in voxelmap mode)"
)
parser.add_argument(
	"--output",
	help="Output path or folder for rendered voxel PNGs"
)

parser.add_argument(
	"--only",
	type=str,
	help="Render only this prefab by name (without extension)"
)
parser.add_argument(
	"--mode",
	type=str,
	default="default",
	help="Choose rendering mode (default/test1/xyz/yxz/etc)"
)


def get_args():
	args = parser.parse_args()
# ----------------------------------------------
# ✅ CLI arg validation
# ----------------------------------------------

	# --only-biomes
	if args.only_biomes:
		invalid = set(args.only_biomes) - VALID_BIOMES
		if invalid:
			parser.error(
				f"Invalid biome name(s): {', '.join(invalid)}\n"
				f"Valid options: {', '.join(sorted(VALID_BIOMES))}"
			)
	# --xml, --localization, --biomes
	for path_arg, label in [(args.xml, "XML"), (args.localization, "Localization"), (args.biomes, "Biomes")]:
		if path_arg and not os.path.isfile(path_arg):
			parser.error(f"{label} file not found: {path_arg}")
	
	# --text-size
	if args.text_size > 60:
		args.text_size = 60
	elif args.text_size < 10:
		args.text_size = 10
	return args
# ----------------------------------------------
# ✅ Bounding box + overlap logic
# ----------------------------------------------

def get_text_box(text, x, y, font, padding=4):
	bbox = font.getbbox(text)
	text_w = bbox[2] - bbox[0]
	text_h = bbox[3] - bbox[1]
	return (
		x - padding,
		y - padding,
		x + text_w + padding,
		y + text_h + padding
	)

def boxes_overlap(a, b):
	return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])

def check_label_overlap(label_box, placed_boxes):
	return any(boxes_overlap(label_box, other) for other in placed_boxes)

def check_dot_overlap(label_box, poi_x, poi_y, radius=4):
	dot_box = (poi_x - radius, poi_y - radius, poi_x + radius, poi_y + radius)
	return boxes_overlap(label_box, dot_box)

# ----------------------------------------------
# ✅ Zone placement logic (mask-based)
# ----------------------------------------------

def is_placeable(label_box, label_mask, red_rgb):
	x0, y0, x1, y1 = map(int, label_box)
	width, height = label_mask.size

	# Clip box to within image bounds
	x0 = max(0, min(x0, width - 1))
	x1 = max(0, min(x1, width - 1))
	y0 = max(0, min(y0, height - 1))
	y1 = max(0, min(y1, height - 1))

	for y in range(y0, y1 + 1):
		for x in range(x0, x1 + 1):
			r, g, b = label_mask.getpixel((x, y))
			if (r, g, b) == red_rgb:
				return False
	return True

# ----------------------------------------------
# ✅ POI_ID green zone label placement (used in --numbered-dots)
# ----------------------------------------------

def try_green_zone_label(text, base_x, base_y, font, mask, occupied_boxes, red_rgb):
	if mask is None:
			return None
	bbox = font.getbbox(text)
	text_w = bbox[2] - bbox[0]
	text_h = bbox[3] - bbox[1]
	pad = 4

	max_nudge = 4
	step = text_h + 2

	# Vertical
	for dy in range(1, max_nudge + 1):
		for offset in [-dy * step, dy * step]:
			lx = base_x - text_w // 2
			ly = base_y + offset - text_h // 2
			label_box = (lx - pad, ly - pad, lx + text_w + pad, ly + text_h + pad)
			if not is_placeable(label_box, mask, red_rgb): continue
			if check_label_overlap(label_box, occupied_boxes): continue
			return lx, ly, label_box

	# Horizontal
	for dx in range(1, max_nudge + 1):
		for offset in [-dx * (text_w + 8), dx * (text_w + 8)]:
			lx = base_x + offset - text_w // 2
			ly = base_y - text_h // 2
			label_box = (lx - pad, ly - pad, lx + text_w + pad, ly + text_h + pad)
			if not is_placeable(label_box, mask, red_rgb): continue
			if check_label_overlap(label_box, occupied_boxes): continue
			return lx, ly, label_box

	# Diagonal
	for i in range(1, max_nudge + 1):
		for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
			lx = base_x + dx * (text_w + 10) - text_w // 2
			ly = base_y + dy * step - text_h // 2
			label_box = (lx - pad, ly - pad, lx + text_w + pad, ly + text_h + pad)
			if not is_placeable(label_box, mask, red_rgb): continue
			if check_label_overlap(label_box, occupied_boxes): continue
			return lx, ly, label_box

	return None	 # Fallback: draw directly on dot
# ----------------------------------------------
# ✅ Prefab XML loader
# ----------------------------------------------

import xml.etree.ElementTree as ET

def load_prefabs_from_xml(xml_path):
	"""
	Parses prefabs.xml and returns a list of (POI_ID, name, x, z) tuples.
	Supports prefabs defined using position="x,y,z" attribute.
	"""
	tree = ET.parse(xml_path)
	root = tree.getroot()
	prefabs = []
	i = 0
	for elem in root.iter():
		name = elem.get("name")
		position = elem.get("position")
		if not name or not position:
			continue
		try:
			x, y, z = map(float, position.split(","))
			i += 1
			prefabs.append((f"POI_{i}", name, int(x), int(z)))
		except ValueError:
			continue
	print(f"✅ Found {len(prefabs)} prefab entries.")
	return prefabs

# ----------------------------------------------
# ✅ Prefab filter
# ----------------------------------------------

def should_exclude(name):
	if not name:
		return True
	name = name.lower()
	if name.startswith(("bridge", "wilderness_filler", "part_", "street_light", "diersville_city_sign", "cornfield_", "site_grave", "rwg_tile_")):
		return True
	if name.startswith("sign_") and not (name.startswith("sign_260") or name.startswith("sign_73")):
		return True
	return False
# ----------------------------------------------
# ✅ Normalize coordinates
# ----------------------------------------------
def transform_coords(x, z, map_center=3072):
	cx = int(x + map_center if x >= 0 else map_center - abs(x))
	cz = int(map_center - z if z >= 0 else map_center + abs(z))
	return cx, cz

# ----------------------------------------------
# ✅ Normalize blocks to categories to map colors
# ----------------------------------------------

def normalize_name(name):
	name = name.strip().lower()

	skip_keywords = [
		"sleeper", "cobweb", "trash", "decal", "gore", "paper", "cloth", "clothpile", "box", "bag",
		"toilet", "sink", "bathtub", "faucet", "light", "fan", "vent", "candle", "spider", "crate", "decor",
		"cash", "mug", "jar", "plate", "glass", "bottle", "bone", "flesh", "skull", "carton", "urn", "shard",
		"poster", "mirror", "note", "magazine", "frame", "flag", "painting", "lamp"
	]

	material_keywords = [
		"wood", "metal", "steel", "concrete", "brick", "trash", "glass", "stone", "asphalt", "tile", "shingle",
		"plaster", "roof", "gravel", "terrain", "road", "dirt", "soil", "sand", "marble", "cinder", "cement"
	]

	color_keywords = [
		"red", "green", "blue", "gray", "grey", "white", "black",
		"brown", "yellow", "tan", "pink", "orange", "purple"
	]

	if not name.isidentifier():
		return None
	if any(skip in name for skip in skip_keywords):
		return None

	# Remove common suffixes
	name = re.sub(r'(left|right|top|bottom|corner)$', '', name)
	name = re.sub(r'\d+$', '', name)
	name = re.sub(r'[_]+$', '', name)

	# Color category
	for color in color_keywords:
		if color in name:
			return f"color_{color}"

	# Material category
	for material in material_keywords:
		if material in name:
			return f"material_{material}"

	if len(name) < 4:
		return None

	return name

# ----------------------------------------------
# ✅ Loads color palette of category mappings
# ----------------------------------------------
def load_color_palette(path):
	color_map = {}
	with open(path, newline='') as f:
		reader = csv.DictReader(f)
		for row in reader:
			key = row['category'].strip().lower()
			value = row['color_hex'].strip()
			if key and value:
				color_map[key] = value
	return color_map

# ----------------------------------------------
# ✅ Parse XML to get prefab orientation to North
# ----------------------------------------------
def get_rotation_to_north(prefab_name, prefab_dir):
	xml_path = os.path.join(prefab_dir, f"{prefab_name}.xml")
	if not os.path.exists(xml_path):
		return 0  # Default fallback

	try:
		tree = ET.parse(xml_path)
		for prop in tree.findall(".//property"):
			if prop.attrib.get("name") == "RotationToFaceNorth":
				return int(prop.attrib.get("value", 0))
	except Exception as e:
		print(f"⚠️ Failed to parse RotationToFaceNorth for {prefab_name}: {e}")
	return 0

