### 🧪 Block Parser Test Harness: Confirm correct block ID + name mapping from .blocks.nim

def load_block_names(path):
	with open(path, "rb") as f:
		data = f.read()

	offset = 8  # Skip 8-byte file header
	block_names = {}

	while offset < len(data):
		try:
			# Read 4 bytes → Block ID (little-endian int32)
			block_id = int.from_bytes(data[offset:offset + 4], "little")
			offset += 4

			# Read 1 byte → length of UTF-8 name string
			name_len = data[offset]
			offset += 1

			# Read 'name_len' bytes as UTF-8 block name
			name_bytes = data[offset:offset + name_len]
			name = name_bytes.decode("utf-8", errors="replace")
			offset += name_len

			block_names[block_id] = name

		except Exception as e:
			print(f"❌ Failed at offset {offset}, block ID {block_id}: {e}")
			break

	print(f"✅ Parsed {len(block_names)} block names from .blocks.nim")
	sorted_ids = sorted(block_names.keys())
	for i, bid in enumerate(sorted_ids):
		print(f"🔍 ID {bid} → {block_names[bid]}")
	return block_names


if __name__ == "__main__":
	path = "/Users/dustinn/Projects/gamefiles/RWG/traders/trader_rekt.blocks.nim"
	load_block_names(path)