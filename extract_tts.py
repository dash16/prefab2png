def extract_block_ids_from_tts(path):
	with open(path, "rb") as f:
		data = f.read()

	assert data[:4] == b'tts\x00', "Invalid TTS header"

	version = int.from_bytes(data[4:8], "little")
	sx = int.from_bytes(data[8:10], "little")
	sy = int.from_bytes(data[10:12], "little")
	sz = int.from_bytes(data[12:14], "little")

	total_blocks = sx * sy * sz
	print(f"📏 Prefab: {sx}×{sy}×{sz} = {total_blocks} blocks")

	offset = 14
	block_ids = {}

	for i in range(total_blocks):
		raw = int.from_bytes(data[offset:offset+4], "little")
		block_id = raw & 0x7FFF  # lower 15 bits
		block_ids[block_id] = block_ids.get(block_id, 0) + 1
		offset += 4

	print(f"✅ Found {len(block_ids)} unique block IDs")
	for block_id, count in sorted(block_ids.items()):
		print(f"🔢 ID {block_id}: {count} uses")

if __name__ == "__main__":
	import sys
	if len(sys.argv) != 2:
		print("Usage: python3 extract_tts_block_ids.py file.tts")
	else:
		extract_block_ids_from_tts(sys.argv[1])
