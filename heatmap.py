import os
from PIL import Image, ImageDraw, ImageFont, ImageOps
from helper import load_prefabs_from_xml, should_exclude, transform_coords
from parse import args, Config
import time

# === Setup ===
config = Config(args)
prefabs = load_prefabs_from_xml(config.xml_path)
output_dir = "heatmap"
image_width = 6145
image_height = 6145

# === Filter loaded prefabs ===
filtered_prefabs = [p for p in prefabs if not should_exclude(p[1])]
print(f"✅ Prefabs after filtering: {len(filtered_prefabs)}")
prefabs = filtered_prefabs

# === Generate heatmap and overlay ===
heatmap = Image.new("L", (image_width, image_height), 0)
draw = ImageDraw.Draw(heatmap)

overlay = Image.new("RGB", (image_width, image_height), "black")
ol_draw = ImageDraw.Draw(overlay)

try:
    font = ImageFont.truetype("DejaVuSans.ttf", 20)
except:
    font = ImageFont.load_default()

for poi_id, name, x, z in prefabs:
    px, pz = transform_coords(x, z)
    current = heatmap.getpixel((px, pz))
    for dx in range(-30, 31):
        for dz in range(-30, 31):
            tx, tz = px + dx, pz + dz
            if 0 <= tx < image_width and 0 <= tz < image_height:
                current = heatmap.getpixel((tx, tz))
                heatmap.putpixel((tx, tz), min(255, current + 20))
    ol_draw.rectangle((px - 2, pz - 2, px + 2, pz + 2), fill="white")
    ol_draw.text((px + 4, pz - 4), poi_id, fill="white", font=font, stroke_width=1, stroke_fill="black")

# === Save ===
os.makedirs(output_dir, exist_ok=True)
heatmap_path = os.path.join(config.output_dir, "heatmap.png")
overlay_path = os.path.join(config.output_dir, "heatmap_overlay.png")
rgb_heatmap = Image.new("RGB", (image_width, image_height), "black")

import numpy as np

# Generate color heatmap using NumPy for speed
rescaled = ImageOps.autocontrast(heatmap)
rescaled_array = np.array(rescaled)

rgb_array = np.zeros((*rescaled_array.shape, 3), dtype=np.uint8)

blue_mask = (rescaled_array > 0) & (rescaled_array < 85)
orange_mask = (rescaled_array >= 85) & (rescaled_array < 170)
white_mask = (rescaled_array >= 170)

rgb_array[blue_mask] = [0, 0, 255]
rgb_array[orange_mask] = [255, 165, 0]
rgb_array[white_mask] = [255, 255, 255]

# === Save color heatmap ===

heatmap_color = Image.fromarray(rgb_array, mode="RGB")
heatmap_color.save(os.path.join(output_dir, "heatmap_color.png"))

# === Save grayscale base heatmap ===
heatmap_path = os.path.join(output_dir, "heatmap.png")
heatmap.save(heatmap_path)

# === Save overlay ===
overlay.save(os.path.join(output_dir, "heatmap_overlay.png"))

# === Done ===
print("🌈 Color heatmap saved to: output/heatmap_color.png")
print("🔥 Heatmap saved to: output/heatmap.png")
print("🔍 Overlay saved to: output/heatmap_overlay.png")