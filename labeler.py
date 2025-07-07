# labeler.py

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

def is_placeable(rect_coords, label_mask, red_rgb, red_corner_tolerance=2):
    """
    Checks whether a label box can be placed at rect_coords without violating red zones.
    """
    if not label_mask:
        return True

    x1, y1, x2, y2 = rect_coords
    width, height = label_mask.size
    red_corners = 0
    for x, y in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
        if 0 <= x < width and 0 <= y < height:
            if label_mask.getpixel((x, y)) == red_rgb:
                red_corners += 1

    return red_corners <= red_corner_tolerance

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
