from PIL import Image
from filters import CATEGORY_COLORS
import random

def render_sticker(surface, color_lookup=None, scale=1):
	from PIL import Image
	import random

	height = len(surface)
	width = len(surface[0]) if height > 0 else 0
	img = Image.new("RGBA", (width * scale, height * scale))
	pixels = img.load()

	for z in range(height):
		for x in range(width):
			block_name = surface[z][x]

			# Try direct RGB lookup
			if color_lookup and block_name in color_lookup:
				r, g, b = color_lookup[block_name]
				color = (r, g, b, 255)

			# Fallback for unknowns
			elif block_name.startswith("unknown_"):
				seed = int(block_name.split("_")[1])
				random.seed(seed)
				color = (
					random.randint(80, 255),
					random.randint(80, 255),
					random.randint(80, 255),
					255
				)
			else:
				color = (200, 200, 200, 255)

			for dz in range(scale):
				for dx in range(scale):
					pixels[x * scale + dx, z * scale + dz] = color

	return img
