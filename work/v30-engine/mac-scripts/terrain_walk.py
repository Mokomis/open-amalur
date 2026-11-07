"""Walk the terrain stream and characterise decompressed blocks."""
import collections, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
print(len(s), "after first", s[16777236 - 8:16777236 + 80].hex())
# Find every zlib stream by its signature preceded by plausible sizes.
at = 16777236
sizes = collections.Counter()
records = []
i = at
while True:
    i = s.find(b"\x78\x9c", i)
    if i < 0:
        break
    if i >= 24:
        raw, total, zero, raw2, comp = struct.unpack_from("<5I", s, i - 20)
        if raw == raw2 and zero == 0 and comp <= total <= comp + 32 and i + comp <= len(s):
            records.append((i - 20, raw, total, comp))
            sizes[raw] += 1
            i += comp
            continue
    i += 1
print("zlib records", len(records), "first", records[:8], "last", records[-3:], "raw sizes", sizes.most_common(12))
print("gaps", collections.Counter(records[k + 1][0] - (records[k][0] + 20 + records[k][3]) for k in range(len(records) - 1)).most_common(6))
print("total raw", sum(r[1] for r in records), "total comp", sum(r[3] for r in records))
for r in records[:3] + records[len(records) // 2:len(records) // 2 + 2]:
    raw = zlib.decompress(s[r[0] + 20:r[0] + 20 + r[3]])
    print(r, raw[:80].hex())
    if len(raw) >= 8:
        print("   u16", struct.unpack_from("<16H", raw, 0) if len(raw) >= 32 else "", "f32", [round(x, 2) for x in struct.unpack_from("<8f", raw, 0)] if len(raw) >= 32 else "")
