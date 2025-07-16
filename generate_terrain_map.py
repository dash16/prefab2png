from PIL import Image, ImageEnhance, ImageDraw
import numpy as np
import os

# File paths
#raw_path = "dtm_processed.raw"
#biome_path = "biomes.png"
#splat_path = "splat3_processed.png"
#radiation_path = "radiation.png"
output_path = "terrain_biome_shaded_final.png"

raw_path ="/Users/dustinn/Projects/gamefiles/RWG/dtm_processed.raw"
biome_path = "/Users/dustinn/Projects/gamefiles/RWG/biomes.png"
splat_path = "/Users/dustinn/Projects/gamefiles/RWG/splat3_processed.png"
#radiation_path = "/Users/dustinn/Projects/gamefiles/RWG/radiation.png"

# Map Size, change as necessary for larger worlds
map_size = 6144

# Load heightmap
with open(raw_path, "rb") as f:
	raw_data = f.read()
print(f"Loaded RAW: {len(raw_data)} bytes")

# Validate size
if len(raw_data) != 6144 * 6144 * 2:
	raise ValueError("RAW file size does not match expected 6144x6144 uint16 format.")

# Decode heightmap
height_data = np.frombuffer(raw_data, dtype=np.uint16).reshape((6144, 6144))
height_normalized = (height_data - height_data.min()) / height_data.ptp()

# Load biome image
biome_img = Image.open(biome_path).convert("RGB")
if biome_img.size != (6144, 6144):
	print(f"Resizing biome map from {biome_img.size} to 6144x6144...")
	biome_img = biome_img.resize((6144, 6144), Image.Resampling.NEAREST)
biome_array = np.array(biome_img)

# Biome colors (with names for logging)
biomes = {
	"Burnt Forest": {"color": (186, 0, 255), "shade": (48, 43, 43)},
	"Desert":       {"color": (255, 228, 119), "shade": (127, 118, 104)},
	"Pine Forest":  {"color": (0, 64, 0), "shade": (46, 62, 41)},
	"Snow":         {"color": (255, 255, 255), "shade": (149, 178, 195)},
	"Wasteland":    {"color": (255, 168, 0), "shade": (84, 100, 73)}
}

from scipy.spatial import KDTree

# Build color list and KDTree from biome definitions
biome_names = list(biomes.keys())
biome_colors = [biomes[name]["color"] for name in biome_names]
biome_shades = [biomes[name]["shade"] for name in biome_names]
tree = KDTree(biome_colors)

# Flatten biome image and map each pixel to nearest biome color
flat_pixels = biome_array.reshape((-1, 3))
_, idx = tree.query(flat_pixels)
biome_indices = idx.reshape((6144, 6144))

# Render base shaded terrain
output = np.zeros((6144, 6144, 3), dtype=np.uint8)
matches_found = 0
brightness = 1.4
gamma = 0.9

# Use softened brightness curve (emphasize midrange elevation)
height_brightness = np.clip(np.sqrt(height_normalized), 0, 1)

for i, name in enumerate(biome_names):
	mask = biome_indices == i
	count = np.count_nonzero(mask)
	matches_found += count
	print(f"{name}: {count} pixels")

	shade = biome_shades[i]
	for c in range(3):
		val = height_brightness[mask] * shade[c]
		output[..., c][mask] = np.clip(val, 0, 255).astype(np.uint8)

# Contour settings
contour_interval = 600  # space between lines (try 800 or 1000 for large-scale maps)
contour_thickness = 1   # how many vertical units wide
contour_color = (200, 200, 200)  # soft gray, not white

# Create mask for thin contour band
contour_mask = np.logical_and(
	(height_data % contour_interval) < contour_thickness,
	height_data > 0  # skip flat terrain
)

# Blend contour color instead of hard overwrite
blend_strength = 0.25  # 0 = no effect, 1 = full line color

for c in range(3):
	base = output[..., c].astype(np.float32)
	contour_layer = contour_color[c]
	output[..., c][contour_mask] = np.clip(
		(1 - blend_strength) * base[contour_mask] + blend_strength * contour_layer,
		0, 255
	).astype(np.uint8)

# Apply hillshading
gradient_x, gradient_y = np.gradient(height_data.astype(np.float32))
slope = np.sqrt(gradient_x**2 + gradient_y**2)
hillshade = 1 - np.clip(slope / slope.max(), 0, 1)
hillshade = (hillshade * 255).astype(np.uint8)

# Apply gamma correction to soften hillshade contrast
hillshade_gamma = 1.2
hillshade_corrected = 255 * ((hillshade / 255.0) ** hillshade_gamma)
hillshade_corrected = hillshade_corrected.astype(np.uint8)

# LERP blend: soften the hillshade influence
hillshade_opacity = 0.4  # Adjust 0.2–0.5 for lighter/darker terrain

for c in range(3):
	base = output[..., c].astype(np.float32)
	shadow = base * (hillshade_corrected / 255.0)
	output[..., c] = np.clip(
		(1 - hillshade_opacity) * base + hillshade_opacity * shadow,
		0, 255
	).astype(np.uint8)

# Nonlinear remap — emphasize mid elevations
height_brightness = np.clip(np.sqrt(height_normalized), 0, 1)

# Final output brighten for visual clarity
output = np.clip(output * 1.2 + 32, 0, 255).astype(np.uint8)

### 🧩 Roads Overlay from Splat3: Adds major and minor roads to the final image
if os.path.exists(splat_path):
	print(f"🛣️ Adding roads from: {splat_path}")
	splat_img = Image.open(splat_path).convert("RGB").resize((6144, 6144), Image.NEAREST)
	splat_data = np.array(splat_img)

	# Create transparent overlay
	roads_overlay = Image.new("RGBA", (6144, 6144), (0, 0, 0, 0))
	draw = ImageDraw.Draw(roads_overlay)

	# Major roads: Red channel > 128
	red_mask = splat_data[..., 0] > 128
	red_coords = np.column_stack(np.where(red_mask))
	for y, x in red_coords:
		draw.point((x, y), fill=(94, 93, 94))  # terrAsphalt

	# Minor roads: Green channel > 128
	green_mask = splat_data[..., 1] > 128
	green_coords = np.column_stack(np.where(green_mask))
	for y, x in green_coords:
		draw.point((x, y), fill=(116, 109, 100))  # Gravel, else use Sand: (116, 113, 92)

	# Composite on top of final image
	final_img = Image.fromarray(output).convert("RGBA")
	final_img.alpha_composite(roads_overlay)
else:
	print("⚠️ Roads overlay skipped (splat3_processed.png not found)")

# === ☢️ Radiation Overlay (disabled for now) ===
"""
if os.path.exists(radiation_path):
	print(f"☢️ Adding radiation from: {radiation_path}")
	radiation_img = Image.open(radiation_path).convert("L").resize((map_size, map_size), Image.NEAREST)
	radiation_mask = np.array(radiation_img) > 0
	radiation_count = np.sum(radiation_mask)
	print(f"Radiation zones: {radiation_count} pixels")

	# Draw semi-transparent red over radiation zones
	overlay = np.zeros_like(output, dtype=np.uint8)
	overlay[..., 0] = 255  # Red channel

	alpha = 100  # Transparency level
	output[radiation_mask] = (
		(1 - alpha / 255) * output[radiation_mask] + (alpha / 255) * overlay[radiation_mask]
	).astype(np.uint8)
else:
	print("⚠️ Radiation map not found, skipping radiation overlay.")
"""

# Save composite
final_img.save("terrain_biome_shaded_final.png")
print("✅ Saved: terrain_biome_shaded_final.png")
