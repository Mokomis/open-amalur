"""Rewrites only the foliage cell files of a pack, from the same placement build_world_pack.py uses."""
import json, re, struct, sys
from pathlib import Path
import numpy as np
src, out = Path(sys.argv[1]), Path(sys.argv[2])
code = (Path(__file__).parent / "build_world_pack.py").read_text()
exec(code[code.index("def grass_mesh"):code.index("VERTEX =")])
VERTEX = np.dtype([("p", "<f4", 3), ("n", "<i2", 4), ("t", "<f4", 2)])
CELL = 6400.0
zone_meta = json.loads((src / "zone_materials.json").read_text())
exec(code[code.index("ATLAS ="):code.index("head = b\"OAWI\"")])
print("foliage cells", len(grass_tris), "triangles", sum(grass_tris.values()))
