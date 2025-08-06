# render.py

import os
from PIL import Image, ImageDraw, ImageFont
from filters import should_exclude, BLOCK_CATEGORY_ALIASES, CATEGORY_COLORS
from block_parser import load_tts, load_block_names, load_block_colors
from labeler import (
	wrap_label,
	get_text_box,
	is_placeable,
	find_label_position_in_blue_zone,
	placed_bounding_boxes,
	extended_green_zone_search
)
from helper import try_green_zone_label
from block_analysis import categorize_surface, categorize_blocks
'''
# === Bounding box helper (optional future use) ===
def boxes_overlap(box1, box2, padding=2):
	return not (
		box1[2] + padding < box2[0] or
		box1[0] - padding > box2[2] or
		box1[3] + padding < box2[1] or
		box1[1] - padding > box2[3]
	)
'''

### 🧩 Top Block Renderer: Renders top-down image of a prefab using block colors
def render_top_blocks(tts_path, blocks_path, blocks_xml_path, config):
	"""
	Renders a top-down image of the prefab's topmost blocks.
		Returns:
			PIL.Image.Image: Rendered image (not saved)
	"""
	# Load all inputs
	block_names = load_block_names(blocks_path)
	prefab = load_tts(tts_path, block_names)
	block_colors = load_block_colors(blocks_xml_path)
	# 🛠️ Manual override for terrainGravel to better match splatmap road blending
	block_colors["terrAsphalt"] = (94, 93, 94)

	# Extract grid dimensions
	grid = prefab["layers"]
	sz = len(grid)
	sy = len(grid[0])
	sx = len(grid[0][0])
	top_blocks = {}

	# Scan for topmost non-air blocks
	for z in range(sz):
		for x in range(sx):
			for y in reversed(range(sy)):
				block_id = grid[z][y][x]
				if block_id != 0:
					top_blocks[(x, z)] = block_id
					break

	visible_ids = set(top_blocks.values())
	category_map = categorize_blocks(visible_ids, block_names)

	# Create transparent RGBA image
	image = Image.new("RGBA", (sx, sz), (0, 0, 0, 0))
	pixels = image.load()

	for (x, z), block_id in top_blocks.items():
		matched_color = False
		name = block_names.get(block_id, f"unknown_{block_id}")
		rgb = block_colors.get(name)
		if rgb:
			matched_color = True
		# Fallback: fuzzy match using BLOCK_CATEGORY_ALIASES and CATEGORY_COLORS keys
		if not rgb:
			name_lower = name.lower()
			matched_category = None
		
			# Step 1: Try BLOCK_CATEGORY_ALIASES
			for keyword, category in BLOCK_CATEGORY_ALIASES.items():
				if keyword in name_lower:
					matched_category = category
					break
		
			if matched_category:
				color = CATEGORY_COLORS.get(matched_category)
				if color:
					rgb = color
					if config.verbose:
						print(f"[FUZZY COLOR] '{name}' → keyword '{keyword}' → '{matched_category}' → {rgb}")
				elif config.verbose:
					print(f"[FUZZY MISS] Matched '{keyword}' → '{matched_category}' but no color assigned")
			else:
				# Step 2: Try keywords directly from CATEGORY_COLORS
				for category in CATEGORY_COLORS.keys():
					if category.lower() in name_lower:
						color = CATEGORY_COLORS[category]
						rgb = color
						if config.verbose:
							print(f"[FUZZY COLOR CATEGORY] '{name}' → matched keyword '{category}' → {rgb}")
						break
		
				if not rgb and config.verbose:
					print(f"[FUZZY NOMATCH] No keyword match for block '{name}'")

		# Final fallback
		if not rgb:
			if config.verbose:
				print(f"🎨 Missing color for block '{name}' (ID {block_id})")
			rgb = (0, 0, 0, 0)

		if len(rgb) == 4:
			pixels[x, z] = rgb
		else:
			pixels[x, z] = (*rgb, 255)
		
	return image

# === Label helpers ===
# === Wedge ===
def draw_label_wedge_only(draw, dot_x, dot_y, final_box, padding=4, dot_color="black"):
	"""Draw only the wedge polygon and lines from dot to label box."""
	LINE_WIDTH = 2
	LABEL_FILL = (255, 255, 255, 200)  # Semi-transparent white

	x1, y1, x2, y2 = final_box

	dist_left	= abs(dot_x - x1)
	dist_right	= abs(dot_x - x2)
	dist_top	= abs(dot_y - y1)
	dist_bottom = abs(dot_y - y2)

	min_dist = min(dist_left, dist_right, dist_top, dist_bottom)
	if min_dist == dist_left:
		anchor_top = (x1, y1 + padding)
		anchor_bottom = (x1, y2 - padding)
	elif min_dist == dist_right:
		anchor_top = (x2, y1 + padding)
		anchor_bottom = (x2, y2 - padding)
	elif min_dist == dist_top:
		center = (x1 + x2) // 2
		spread = min(20, (x2 - x1) // 2 - padding)
		anchor_top = (center - spread, y1)
		anchor_bottom = (center + spread, y1)
	else:
		center = (x1 + x2) // 2
		spread = min(20, (x2 - x1) // 2 - padding)
		anchor_top = (center - spread, y2)
		anchor_bottom = (center + spread, y2)

	wedge = [ (dot_x, dot_y), anchor_top, anchor_bottom ]
	draw.polygon(wedge, fill=LABEL_FILL)
	draw.line([dot_x, dot_y, *anchor_top], fill=dot_color, width=LINE_WIDTH)
	draw.line([dot_x, dot_y, *anchor_bottom], fill=dot_color, width=LINE_WIDTH)

def draw_label_text_only(draw, wrapped_lines, font, final_box, dot_color="black"):
	"""Draw only the label box and wrapped text lines."""
	BOX_RADIUS = 8
	LABEL_FILL = (255, 255, 255, 200)
	padding = 4

	x1, y1, x2, y2 = final_box
	label_w = x2 - x1
	line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]

	draw.rounded_rectangle([x1, y1, x2, y2], radius=BOX_RADIUS, fill=LABEL_FILL, outline=dot_color, width=2)

	for i, line in enumerate(wrapped_lines):
		bbox = font.getbbox(line)
		text_w = bbox[2] - bbox[0]
		ty = y1 + padding + i * line_height
		tx = x1 + (label_w - text_w) // 2
		draw.text((tx, ty), line, font=font, fill=dot_color)

def render_category_layer(
	category,
	points,
	config,
	display_names,
	tiers,
	tier_colors,
	legend_entries,
	label_mask,
	blue_zones,
	red_rgb,
	blue_rgb,
	log,
	numbered_dots=False
):
	"""
	Renders a single prefab category (e.g., streets, biome_desert) to dot and label PNG layers.
	Returns the combined image path if combined output is enabled.
	"""
	print(f"Rendering layer '{category}' with {len(points)} points...")
	dot_centers = [(px, pz) for _, _, px, pz in points]
	from labeler import find_label_position_near_dot, find_label_position_in_blue_zone
	result = False
	points_img = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
	labels_img = Image.new("RGBA", config.image_size, (255, 255, 255, 0))
	points_draw = ImageDraw.Draw(points_img)
	labels_draw = ImageDraw.Draw(labels_img)
	blue_zone_stack_tops = {}
	font = config.font
	occupied_boxes = []
	label_infos = []
	rejection_attempts = 0
	if numbered_dots:
		for poi_id, name, px, pz in points:
			# 1️⃣ Add to legend
			legend_entries.append((poi_id, name, display_names.get(name, name)))
	
			# 2️⃣ Try green zone placement
			result = None
			if label_mask:
				result = try_green_zone_label(
					poi_id, px, pz, font, label_mask, occupied_boxes, red_rgb
				)
			else:
				# Use extended fallback without mask
				from helper import check_label_overlap
				bbox = font.getbbox(poi_id)
				text_w = bbox[2] - bbox[0]
				text_h = bbox[3] - bbox[1]
				pad = 4
				candidate_offsets = [(-text_w - 12, 0), (text_w + 12, 0), (0, -text_h - 12), (0, text_h + 12)]
				for dx, dy in candidate_offsets:
					lx = px + dx - text_w // 2
					ly = pz + dy - text_h // 2
					label_box = (lx - pad, ly - pad, lx + text_w + pad, ly + text_h + pad)
					if check_label_overlap(label_box, occupied_boxes):
						continue
					result = (lx, ly, label_box)
					break
			if result:
				lx, ly, label_box = result
				log(f"✅ numbered-dots placed near dot for {poi_id}")
			else:
				# ⚠️ Fallback: center on the dot
				bbox = font.getbbox(poi_id)
				text_w = bbox[2] - bbox[0]
				text_h = bbox[3] - bbox[1]
				pad = 4
				lx = px - text_w // 2
				ly = pz - text_h // 2
				label_box = (lx - pad, ly - pad, lx + text_w + pad, ly + text_h + pad)
				log(f"⚠️ numbered-dots fallback for {poi_id}")
	
			# 3️⃣ Draw box and text
			labels_draw.rounded_rectangle(label_box, radius=4, fill="white", outline="black")
			labels_draw.text((lx, ly), poi_id, fill="black", font=font)
	
			# 4️⃣ Optional: draw connector wedge
			draw_label_wedge_only(labels_draw, px, pz, label_box)
	
			# 5️⃣ Track occupied area
			occupied_boxes.append(label_box)
	
		labels_path = os.path.join(config.output_dir, f"{category}_labels.png")
		if points:
			labels_img.save(labels_path)
		return None, 0

	for poi_id, name, px, pz in points:
		display = display_names.get(name, name)
		tier = tiers.get(name, -1)
		dot_color = tier_colors.get(tier, "#FF0000")
		
		# ✅ Always draw a dot for every POI
		r = config.dot_radius
		points_draw.ellipse((px - r - 1, pz - r - 1, px + r + 1, pz + r + 1), fill="white")
		points_draw.ellipse((px - r, pz - r, px + r, pz + r), fill=dot_color)
		
		place_in_blue_zone = label_mask and label_mask.getpixel((px, pz)) == red_rgb

		if place_in_blue_zone:
			result = find_label_position_in_blue_zone(
				px, pz, display, font, blue_zones, blue_zone_stack_tops, label_mask, red_rgb
			)
		elif category not in ("player_starts", "streets"):
			result = find_label_position_near_dot(
				px, pz, display, font, label_mask, red_rgb, blue_rgb, occupied_boxes, dot_centers, log=log
			)
		else:
			# Unconstrained direct placement for player_starts and streets
				pad = config.label_padding
				text_x = px + pad
				text_y = pz + pad + 4
				wrapped_lines = wrap_label(display, font, max_width=200)
				final_box = get_text_box(text_x, text_y, wrapped_lines, font)
				label_x, label_y = text_x, text_y
				result = (label_x, label_y, wrapped_lines, final_box)
				
		if result and category not in ("player_starts", "streets"):
			label_x, label_y, wrapped_lines, final_box = result
			text_w = max((font.getbbox(line)[2] for line in wrapped_lines), default=0)
			line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
			text_h = line_height * len(wrapped_lines)
			label_infos.append({
				"dot_x": px,
				"dot_y": pz,
				"wrapped_lines": wrapped_lines,
				"final_box": final_box,
				"dot_color": dot_color
			})
			log(f"✅ Label added to label_infos for {poi_id} via pass 1-3")
			occupied_boxes.append(final_box)
			placed_bounding_boxes.append((poi_id, category, final_box))
			
			if config.args.verbose and config.verbose_log_file:
				tier_str = f" (Tier {tier})" if tier >= 0 else ""
				config.verbose_log_file.write(f"{poi_id},{name},{display}{tier_str},{dot_color},rendered\n")
			continue

		elif result and category in ("player_starts", "streets"):
			line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
		
			for i, line in enumerate(wrapped_lines):
				ty = label_y + i * line_height
				for ox in (-1, 0, 1):
					for oy in (-1, 0, 1):
						if ox or oy:
							labels_draw.text((label_x + ox, ty + oy), line, fill="white", font=font)
				labels_draw.text((label_x, ty), line, fill=dot_color, font=font)
		
			# Connector line
			label_mid_y = label_y + (line_height * len(wrapped_lines)) // 2
			text_w = max((font.getbbox(line)[2] for line in wrapped_lines), default=0)
			anchor_x = label_x if label_x > px else label_x + text_w
			labels_draw.line([(px, pz), (anchor_x, label_mid_y)], fill="white", width=4)
			labels_draw.line([(px, pz), (anchor_x, label_mid_y)], fill=dot_color, width=2)
		
			occupied_boxes.append(final_box)

			if config.args.verbose and config.verbose_log_file:
				tier_str = f" (Tier {tier})" if tier >= 0 else ""
				config.verbose_log_file.write(f"{poi_id},{name},{display}{tier_str},{dot_color},rendered\n")

		# log missed placements for extended_green_zone_search
		if not result and category not in ("player_starts", "streets"):
			result = extended_green_zone_search(
				dot_px=px,
				dot_pz=pz,
				display=display,
				font=font,
				label_mask=label_mask,
				red_rgb=red_rgb,
				blue_rgb=blue_rgb,
				occupied_boxes=occupied_boxes,
				dot_centers=dot_centers,
				log=log
			)
		
			if result:
				log(f"✅ Label added to label_infos for {poi_id} via Pass 4")
				label_x, label_y, wrapped_lines, final_box = result
				label_infos.append({
					"dot_x": px,
					"dot_y": pz,
					"wrapped_lines": wrapped_lines,
					"final_box": final_box,
					"dot_color": dot_color,
					"pass4_debug": config.debug_extended
				})
				occupied_boxes.append(final_box)
				placed_bounding_boxes.append((poi_id, category, final_box))
		
				if config.args.verbose and config.verbose_log_file:
					tier_str = f" (Tier {tier})" if tier >= 0 else ""
					config.verbose_log_file.write(f"{poi_id},{name},{display}{tier_str},{dot_color},rendered (pass4)\n")
				continue
		
			# ⬇️ Final fallback only if Pass 4 also fails
			legend_entries.append((poi_id, name, display_names.get(name, name)))
			bbox = labels_draw.textbbox((0, 0), poi_id, font=font)
			w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
			pad = 4
			label_box = (
				px - w // 2 - pad,
				pz - h // 2 - pad,
				px + w // 2 + pad,
				pz + h // 2 + pad
			)
			points_draw.rounded_rectangle(label_box, radius=4, fill="white", outline="black")
			labels_draw.text((px - w // 2, pz - h // 2), poi_id, fill="black", font=font)
			log(f"⚠️ Final fallback: POI_ID on dot for {poi_id}")
			rejection_attempts += 1
		
			if config.args.verbose and config.verbose_log_file:
				tier_str = f" (Tier {tier})" if tier >= 0 else ""
				config.verbose_log_file.write(
					f"{poi_id},{name},{display}{tier_str},{dot_color},skipped (fallback to legend)\n"
				)

		# 🔢 If numbered-dots mode is enabled, draw POI_ID box too
		if numbered_dots:
			legend_entries.append((poi_id, name, display_names.get(name, name)))
			bbox = font.getbbox(poi_id)
			text_w = bbox[2] - bbox[0]
			text_h = bbox[3] - bbox[1]
			pad = 4
			label_box = (
				px - text_w // 2 - pad,
				pz - text_h // 2 - pad,
				px + text_w // 2 + pad,
				pz + text_h // 2 + pad
			)
			labels_draw.rounded_rectangle(label_box, radius=4, fill="white", outline="black")
			labels_draw.text((px - text_w // 2, pz - text_h // 2), poi_id, fill="black", font=font)
		
	# First pass: draw all wedges
	for info in label_infos:
		draw_label_wedge_only(
			draw=labels_draw,
			dot_x=info["dot_x"],
			dot_y=info["dot_y"],
			final_box=info["final_box"],
			dot_color="yellow" if info.get("pass4_debug") else info["dot_color"]
		)
		
	# Second pass: draw all label text and dots
	for info in label_infos:
		draw_label_text_only(
			draw=labels_draw,
			wrapped_lines=info["wrapped_lines"],
			font=font,
			final_box=info["final_box"],
			dot_color="yellow" if info.get("pass4_debug") else info["dot_color"]
		)
	points_path = os.path.join(config.output_dir, f"{category}_points.png")
	labels_path = os.path.join(config.output_dir, f"{category}_labels.png")
	points_img.save(points_path)
	labels_img.save(labels_path)

	if config.args.combined:
		combined = Image.alpha_composite(points_img, labels_img)
		combined_path = os.path.join(config.combined_dir, f"{category}_combined.png")
		combined.save(combined_path)
		return combined_path, rejection_attempts

	return None, rejection_attempts