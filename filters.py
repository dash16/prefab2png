# filters.py

# Prefabs containing these substrings will be excluded
EXCLUSION_PATTERNS = [
	"bridge",
	"part_",
	"street_light",
	"diersville_city_",
	"cornfield_",
	"site_grave",
	"wilderness_filler",
	"roadblock",
	"crater",
	"gravestowne_city",
	"departure_city",
	"perishton_city",
	"rubble_burnt_filler",
	"rubble_downtown_filler",
	"bus_stop",
	"bus_wreck",
	"canyon_gift_shop_parking",
	"canyon_gift_shop_sign",
	"desert_town_blk",
	"perishton_fence",
	"perishton_riverdock",
	"remnant_industrial",
	"road_railing_long_filled",
	"perishton_church_parking",
	"perishton_median",
	"perishton_outlet",
	"rwg_tile_"
]

# Special allowlist for signage exceptions
SIGN_ALLOWLIST_PREFIXES = ("sign_260", "sign_73")

def should_exclude(name: str) -> bool:
	"""
	Determines whether a prefab name should be excluded from rendering.
	"""
	name = name.lower()

	# Exclude most sign_ prefabs except specific overrides
	if name.startswith("sign_") and not name.startswith(SIGN_ALLOWLIST_PREFIXES):
		return True

	# Match any denylisted substring
	for pattern in EXCLUSION_PATTERNS:
		if pattern in name:
			return True

	return False

# 🧩 Block Category Aliases: Maps known substrings to visual or semantic groupings
BLOCK_CATEGORY_ALIASES = {
	"palette": "material_wood",
	"pallet": "material_wood",
	"plank": "material_wood",
	"crate": "material_wood",
	"locker": "material_metal",
	"shelf": "material_wood",
	"cabinet": "material_wood",
	"sink": "material_metal",
	"barrel": "material_metal",
	"vent": "material_metal",
	"grate": "material_metal",
	"radiator": "material_metal",
	"rebar": "material_metal",
	"vault": "material_metal",
	"panel": "material_metal",
	"mirror": "material_glass",
	"tv": "material_glass",
	"screen": "material_glass",
	"glass": "material_glass"	
}
# 🧩 Block Category Colors: Provides global color palette for blocks to be rendered
CATEGORY_COLORS = {
	"material_concrete": (207, 207, 207, 255),
	"material_wood": (176, 110, 61, 255),
	"material_metal": (136, 136, 136, 255),
	"color_white": (248, 248, 248, 255),
	"color_brown": (156, 107, 74, 255),
	"color_grey": (160, 160, 160, 255),
	"color_red": (160, 48, 48, 255),
	"color_green": (64, 160, 64, 255),
	"color_blue": (80, 96, 176, 255),
	"color_black": (28, 28, 28, 255),
	"color_yellow": (224, 208, 80, 255),
	"material_terrain": (124, 111, 95, 255),
	"material_gravel": (153, 153, 153, 255),
	"material_brick": (169, 71, 60, 255),
	"color_orange": (232, 124, 51, 255),
	"color_tan": (205, 187, 154, 255),
	"material_stone": (131, 127, 118, 255),
	"material_asphalt": (79, 79, 79, 255),
	"material_plastic": (200, 200, 208, 255),
	"material_dirt": (150, 122, 80, 255),
	"material_cinder": (176, 176, 176, 255),
	"color_purple": (153, 102, 204, 255),
	"material_road": (85, 85, 85, 255),
	"color_pink": (235, 166, 198, 255),
	"material_cement": (208, 208, 208, 255),
	"material_rust": (148, 74, 29, 255),
	"material_fabric": (210, 180, 140, 255),
	"material_tile": (182, 173, 161, 255),
	"material_steel": (160, 160, 160, 255),
	"material_trash": (110, 110, 110, 255),
	"material_glass": (200, 220, 255, 255)
}