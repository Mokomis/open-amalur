from pathlib import Path
import re
m = Path.home() / "Documents/Opem Amalur/work/v09-textures/material_package.py"; x = m.read_text()
print(re.findall(r"MAX_BYTES\s*=\s*[^;\n]+", x))
x2 = re.sub(r"MAX_BYTES\s*=\s*[^;\n]+", "MAX_BYTES=384*1024*1024", x, count=1); m.write_text(x2)
