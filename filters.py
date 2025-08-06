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
	"palette": "wood",
	"pallet": "wood",
	"plank": "wood",
	"crate": "wood",
	"locker": "metal",
	"shelf": "wood",
	"cabinet": "wood",
	"sink": "metal",
	"barrel": "metal",
	"vent": "metal",
	"grate": "metal",
	"radiator": "metal",
	"rebar": "metal",
	"vault": "metal",
	"panel": "metal",
	"mirror": "glass",
	"tv": "glass",
	"screen": "glass"
}
# 🧩 Block Category Colors: Provides global color palette for blocks to be rendered
CATEGORY_COLORS = {
	"terrainFiller": (0, 0, 0, 0),
	"concrete": (207, 207, 207, 255),
	"wood": (97, 80, 67, 255),
	"metal": (108, 112, 128, 255),
	"barbedWire": (86, 86, 86, 255),
	"chainlinkFencePole": (52, 53, 58, 255),
	"plantedCorn": (112, 157, 83, 255),
	"tree": (42, 78, 19, 255),
	"helipad": (189, 189, 44, 255),
	"gravel": (153, 153, 153, 255),
	"brick": (169, 71, 60, 255),
	"stone": (131, 127, 118, 255),
	"asphalt": (79, 79, 79, 255),
	"plastic": (200, 200, 208, 255),
	"dirt": (150, 122, 80, 255),
	"cinder": (176, 176, 176, 255),
	"road": (85, 85, 85, 255),
	"cement": (208, 208, 208, 255),
	"rust": (148, 74, 29, 255),
	"fabric": (210, 180, 140, 255),
	"tile": (182, 173, 161, 255),
	"steel": (160, 160, 160, 255),
	"trash": (110, 110, 110, 255),
	"glass": (200, 220, 255, 255),
	"white": (248, 248, 248, 255),
	"brown": (156, 107, 74, 255),
	"grey": (160, 160, 160, 255),
	"red": (160, 48, 48, 255),
	"green": (64, 160, 64, 255),
	"blue": (80, 96, 176, 255),
	"black": (28, 28, 28, 255),
	"yellow": (224, 208, 80, 255),
	"orange": (232, 124, 51, 255),
	"tan": (205, 187, 154, 255),
	"purple": (153, 102, 204, 255),
	"pink": (235, 166, 198, 255)
}