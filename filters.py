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
