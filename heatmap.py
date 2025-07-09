
import os
from PIL import Image, ImageDraw
from parse import args, Config, load_display_names, load_biome_image, parse_prefabs

# === Setup ===
config = Config(args)
display_names = load_display_names(config.localization_path)
biome_img = load_biome_image(config.biome_path, config.image_size)
categorized_points, _, _ = parse_prefabs(config.xml_path, biome_img, config)

# === Collect POIs ===
all_pois = []
for point_list in categorized_points.values():
    all_pois.extend(point_list)

# === Generate density heatmap ===
heatmap = Image.new("L", config.image_size, 0)
draw = ImageDraw.Draw(heatmap)

for _, _, px, pz in all_pois:
    if 0 <= px < config.image_size[0] and 0 <= pz < config.image_size[1]:
        current = heatmap.getpixel((px, pz))
        draw.point((px, pz), fill=min(255, current + 10))  # Accumulate density

heatmap_path = os.path.join(config.output_dir, "heatmap.png")
heatmap.save(heatmap_path)
print(f"🔥 Density heatmap saved to {heatmap_path}")

# === Generate overlay with POI_ID labels ===
overlay = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
ol_draw = ImageDraw.Draw(overlay)

font = config.font
for poi_id, name, px, pz in all_pois:
    r = config.dot_radius
    ol_draw.ellipse((px - r, pz - r, px + r, pz + r), fill="white")
    ol_draw.text((px + 4, pz - 4), poi_id, fill="black", font=font)

overlay_path = os.path.join(config.output_dir, "heatmap_overlay.png")
overlay.save(overlay_path)
print(f"🔍 POI overlay saved to {overlay_path}")
