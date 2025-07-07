# labeler.py

def boxes_overlap(box1, box2):
    """Return True if two filled rectangles overlap in any way, including touching."""
    return (
        box1[0] < box2[2] and  # left1 < right2
        box1[2] > box2[0] and  # right1 > left2
        box1[1] < box2[3] and  # top1 < bottom2
        box1[3] > box2[1]      # bottom1 > top2
    )

def check_label_overlap(rect, placed_rects):
    """Check whether the proposed label rect overlaps any previously placed labels."""
    for other in placed_rects:
        if boxes_overlap(rect, other):
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

def find_label_position_near_dot(dot_px, dot_pz, display, font, label_mask, red_rgb, blue_rgb, occupied_boxes):
    """
    Tries to find an acceptable area in green zone that does not overlap with existing green zone labels
    """
    pad = 4
    text_x = dot_px + pad
    text_y = dot_pz + pad + 4
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    vertical_offsets = [i * line_height for i in (0, 1, -1, 2, -2, 3, -3, 4, -4)]

    wrapped = wrap_label(display, font, max_width=200)

    for dy in vertical_offsets:
        label_y = text_y + dy
        candidate_box = get_text_box(text_x, label_y, wrapped, font)

        if is_placeable(candidate_box, label_mask, red_rgb, blue_rgb):

            collision = False
            for box in occupied_boxes:
                if boxes_overlap(candidate_box, box):
                    collision = True
                    break

            if not collision:
                return text_x, label_y, wrapped, candidate_box

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
