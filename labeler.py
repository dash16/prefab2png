# labeler.py
import os
placed_bounding_boxes = [] # Global list of placed bounding boxes: (poi_id, layer, (x1, y1, x2, y2))

def boxes_overlap(box1, box2):
	"""Return True if two filled rectangles overlap in any way, including touching."""
	return (
		box1[0] < box2[2] and  # left1 < right2
		box1[2] > box2[0] and  # right1 > left2
		box1[1] < box2[3] and  # top1 < bottom2
		box1[3] > box2[1]	   # bottom1 > top2
	)

def check_label_overlap(rect, placed_rects):
	"""Check whether the proposed label rect overlaps any previously placed labels."""
	for other in placed_rects:
		if boxes_overlap(rect, other):
			return True
	return False

def check_dot_overlap(candidate_box, dot_centers, dot_radius=5, stroke_width=2):
	"""Returns True if the label box overlaps any POI dot."""
	buffer = dot_radius + stroke_width
	x1, y1, x2, y2 = candidate_box
	
	for cx, cy in dot_centers:
		# Define bounding box around the dot
		dot_box = (cx - buffer, cy - buffer, cx + buffer, cy + buffer)
	
		# Check for overlap with label box
		if not (x2 < dot_box[0] or x1 > dot_box[2] or y2 < dot_box[1] or y1 > dot_box[3]):
			return True
	
	return False

def wrap_label(text, font, max_width):
	"""
	Word-wraps a label string to fit within max_width using the provided font.
	"""
	words = text.split()
	lines = []
	current = ""
	for word in words:
		trial = f"{current} {word}".strip()
		width = font.getbbox(trial)[2]
		if width > max_width and current:
			lines.append(current)
			current = word
		else:
			current = trial
	if current:
		lines.append(current)
	return lines

def get_text_box(x, y, lines, font, padding=4):
	"""
	Returns bounding box [x1, y1, x2, y2] for a list of lines at (x, y).
	"""
	max_line_width = max(font.getbbox(line)[2] for line in lines)
	line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
	total_height = len(lines) * line_height
	return [
		x - padding,
		y - padding,
		x + max_line_width + padding,
		y + total_height + padding
	]

def is_placeable(rect_coords, label_mask, red_rgb, blue_rgb=None, red_corner_tolerance=2):
	"""
	Checks whether a label box can be placed at rect_coords without violating red or blue zones.
	"""
	if not label_mask:
		return True

	x1, y1, x2, y2 = rect_coords
	width, height = label_mask.size
	red_corners = 0
	for x, y in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
		if 0 <= x < width and 0 <= y < height:
			pixel = label_mask.getpixel((x, y))
			if pixel == red_rgb:
				red_corners += 1
			if blue_rgb and pixel == blue_rgb:
				return False  # 🚫 Do not place labels that touch blue zones

	return red_corners <= red_corner_tolerance

def find_label_position_near_dot(dot_px, dot_pz, display, font, label_mask, red_rgb, blue_rgb, occupied_boxes, dot_centers, log):
	"""
	Tries to find an acceptable area in green zone that does not overlap with existing labels.
	First attempts vertical offsets, then horizontal as fallback.
	"""
	pad = 4
	text_x = dot_px + pad + 5  # extra 5px skew for wedge visibility
	text_y = dot_pz + pad + 9
	
	# Wrap the label and calculate height for vertical offset
	line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
	# Vertical spacing uses line height (e.g. ~12-14px typically)
	vertical_offsets = [i * line_height for i in (0, 1, -1, 2, -2, 3, -3, 4, -4)]
	wrapped = wrap_label(display, font, max_width=200)

	# Pass 1: vertical placement
	log(f"Trying vertical offsets for {display}") #debug
	for dy in vertical_offsets:
		label_y = text_y + dy
		candidate_box = get_text_box(text_x, label_y, wrapped, font)
		if is_placeable(candidate_box, label_mask, red_rgb, blue_rgb):
			if not check_label_overlap(candidate_box, occupied_boxes) and not check_dot_overlap(candidate_box, dot_centers):
				log(f"✅ Placed using vertical for {display}")
				return text_x, label_y, wrapped, candidate_box

	# Pass 2: horizontal fallback : try horizontal placement using label width as nudge size
	# This calculates the total width of the wrapped label
	log(f"Trying horizontal fallback for {display}") #debug
	max_line_width = max((font.getbbox(line)[2] - font.getbbox(line)[0]) for line in wrapped)
	step = max_line_width // 2
	horizontal_offsets = [i * step for i in (1, -1, 2, -2, 3, -3, 4, -4)]
	for dx in horizontal_offsets:
		label_x = dot_px + dx + pad
		label_y = text_y
		candidate_box = get_text_box(label_x, label_y, wrapped, font)
		if is_placeable(candidate_box, label_mask, red_rgb, blue_rgb):
			if not check_label_overlap(candidate_box, occupied_boxes) and not check_dot_overlap(candidate_box, dot_centers):
				log(f"✅ Placed using horizontal for {display}")
				return label_x, label_y, wrapped, candidate_box
	
	# Pass 3: Diagonal fallback (intercardinal)
	log(f"Trying diagonal fallback for {display}") #debug
	for offset in range(1, 5):
		dx = (max_line_width // 2) * offset
		dy = line_height * offset
		for sign_x, sign_y in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
			label_x = dot_px + sign_x * dx + pad
			label_y = dot_pz + sign_y * dy + pad + 4
			candidate_box = get_text_box(label_x, label_y, wrapped, font)
			if is_placeable(candidate_box, label_mask, red_rgb, blue_rgb):
				if not check_label_overlap(candidate_box, occupied_boxes) and not check_dot_overlap(candidate_box, dot_centers):
					log(f"✅ Placed using diagonal for {display}")
					return label_x, label_y, wrapped, candidate_box
		
	log(f"❌ Failed to place label for {display} in any green zone position")
	return None

# Pass 4: Try passes 1-3 again, this time at a further range
def extended_green_zone_search(dot_px, dot_pz, display, font, label_mask, red_rgb, blue_rgb, occupied_boxes, dot_centers, log, max_range=10):
	pad = 4
	text_x = dot_px + pad + 5
	text_y = dot_pz + pad + 9
	line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
	wrapped = wrap_label(display, font, max_width=200)
	max_line_width = max((font.getbbox(line)[2] for line in wrapped), default=100)
	
	# 🔁 More accurate vertical throw
	box_height = line_height * len(wrapped) + 2 * pad
	
	for offset in range(5, max_range + 1):
		# 🔁 Scaled vertical offsets
		for dy in [offset * box_height, -offset * box_height]:
			label_y = text_y + dy
			candidate_box = get_text_box(text_x, label_y, wrapped, font)
			if is_placeable(candidate_box, label_mask, red_rgb, blue_rgb):
				if not check_label_overlap(candidate_box, occupied_boxes) and not check_dot_overlap(candidate_box, dot_centers):
					log(f"✅ Pass 4 vertical: {display} at offset {dy}")
					return text_x, label_y, wrapped, candidate_box

		# Horizontal (left/right)
		for dx in [offset * (max_line_width // 2), -offset * (max_line_width // 2)]:
			label_x = dot_px + dx + pad
			label_y = text_y
			candidate_box = get_text_box(label_x, label_y, wrapped, font)
			if is_placeable(candidate_box, label_mask, red_rgb, blue_rgb):
				if not check_label_overlap(candidate_box, occupied_boxes) and not check_dot_overlap(candidate_box, dot_centers):
					log(f"✅ Pass 4 horizontal: {display} at offset {dx}")
					return label_x, label_y, wrapped, candidate_box

		# Diagonal
		dx = offset * (max_line_width // 2)
		dy = offset * line_height
		for sign_x, sign_y in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
			label_x = dot_px + sign_x * dx + pad
			label_y = dot_pz + sign_y * dy + pad + 4
			candidate_box = get_text_box(label_x, label_y, wrapped, font)
			if is_placeable(candidate_box, label_mask, red_rgb, blue_rgb):
				if not check_label_overlap(candidate_box, occupied_boxes) and not check_dot_overlap(candidate_box, dot_centers):
					log(f"✅ Pass 4 diagonal: {display} at range {offset}")
					return label_x, label_y, wrapped, candidate_box

	log(f"❌ Pass 4 failed for {display}")
	return None

def find_label_position_in_blue_zone(dot_px, dot_pz, display, font, blue_zones, zone_stack_tops, label_mask, red_rgb):
	"""
	Tries to find a blue zone near the dot to place the label.
	Returns (label_x, label_y, wrapped_lines, label_box) or None if no placement possible.
	"""
	best_zone = None
	min_dist = float("inf")

	for zone in blue_zones:
		zx1, zy1, zx2, zy2 = zone
		cx = (zx1 + zx2) // 2
		cy = (zy1 + zy2) // 2
		dist = abs(cx - dot_px) + abs(cy - dot_pz)
		if dist < min_dist:
			min_dist = dist
			best_zone = zone

	if not best_zone:
		return None

	zx1, zy1, zx2, zy2 = best_zone
	label_x = zx1 + 6  # Snap to left edge
	label_y = zone_stack_tops.get(best_zone, zy1 + 6)

	wrapped = wrap_label(display, font, max_width=200)
	rect_coords = get_text_box(label_x, label_y, wrapped, font)

	if is_placeable(rect_coords, label_mask, red_rgb):
		zone_stack_tops[best_zone] = label_y + (font.getbbox("A")[3] * len(wrapped)) + 6
		return label_x, label_y, wrapped, rect_coords

	return None
