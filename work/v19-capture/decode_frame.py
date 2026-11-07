"""Decode captured constant buffers using layouts taken from the shipped shader disassembly."""
import collections, json, re, struct, sys
from pathlib import Path

root = Path.home() / "Documents" / "Opem Amalur"
run = Path(sys.argv[1])
f = json.loads((run / "frame.json").read_text())
blob = (run / "frame.bin").read_bytes()
ev = f["events"]
shaders = root / "outputs/scene-v19/shaders"

layouts = {}
pattern = re.compile(r"^//\s+cbuffer (\w+)\s*$")
var = re.compile(r"^//\s+(.+?)\s+(\w+)(\[\d+\])?;\s+// Offset:\s+(\d+)\s+Size:\s+(\d+)")
for path in sorted(shaders.glob("*.asm")):
    name = None
    for line in path.read_text(errors="replace").splitlines():
        m = pattern.match(line)
        if m:
            name = m.group(1)
            layouts.setdefault(name, {})
            continue
        m = var.match(line)
        if m and name:
            layouts[name][m.group(2)] = (int(m.group(4)), int(m.group(5)), m.group(1).strip())
for name, rows in sorted(layouts.items()):
    size = max((o + s for o, s, _ in rows.values()), default=0)
    print("layout", name, "bytes", size, "vars", len(rows))

latest = {}
for e in ev:
    if e["e"] == "cbdata":
        latest.setdefault((e["buf"], e["size"]), []).append(blob[e["at"]:e["at"] + e["len"]])


def show(name, data):
    print("=== %s (%d bytes)" % (name, len(data)))
    for var_name, (off, size, kind) in sorted(layouts[name].items(), key=lambda kv: kv[1][0]):
        if off + size > len(data) or "PAD" in var_name:
            continue
        chunk = data[off:off + min(size, 64)]
        if "int" in kind or "bool" in kind:
            vals = struct.unpack("<%di" % (len(chunk) // 4), chunk)
        else:
            vals = tuple(round(v, 5) for v in struct.unpack("<%df" % (len(chunk) // 4), chunk))
        print("  %4d %-28s %s" % (off, var_name, vals))


by_size = {}
for (buf, size), items in latest.items():
    by_size.setdefault(size, []).append((buf, items))
for name, rows in layouts.items():
    total = (max((o + s for o, s, _ in rows.values()), default=0) + 15) // 16 * 16
    if total == 1376:
        for buf, items in by_size.get(1376, []):
            print("updates this capture:", len(items), "identical:", len(set(items)) == 1)
            show(name, items[-1])

print("=== Small slot-0 buffers near the end of the frame")
for size in (16, 32, 48, 64, 96, 128):
    for buf, items in by_size.get(size, []):
        vals = struct.unpack("<%df" % (size // 4), items[-1])
        print(size, buf, "updates", len(items), [round(v, 4) for v in vals])
print("=== 144-byte buffers")
for buf, items in by_size.get(144, []):
    print(buf, "updates", len(items), [round(v, 4) for v in struct.unpack("<36f", items[-1])])

print("=== Merge chain")
tex = f["textures"]
state = {"rt": (), "srv": {}, "ps": None, "cb0": None}
out = []
for e in ev:
    k = e["e"]
    if k == "rt": state["rt"] = tuple(e["res"])
    elif k == "ps": state["ps"] = e["id"]
    elif k == "srv":
        for i, r in enumerate(e["res"]): state["srv"][e["start"] + i] = r
    elif k == "pscb" and e["start"] == 0 and e["bufs"] and e["bufs"][0]: state["cb0"] = e["bufs"][0]
    elif k.startswith("draw"):
        size = tex.get(state["rt"][0], {}) if state["rt"] and state["rt"][0] else {}
        if size.get("w") in (1440, 256):
            out.append((state["ps"], state["rt"][0], dict(state["srv"]), state["cb0"]))
seen = []
for ps, rt, srv, cb in out:
    if not seen or seen[-1] != (ps, rt):
        seen.append((ps, rt))
        print(ps, "rt", rt, tex[rt].get("w"), tex[rt].get("fmt"), "cb0", cb, "srv", {i: (r, tex.get(r, {}).get("w"), tex.get(r, {}).get("h"), tex.get(r, {}).get("fmt")) for i, r in srv.items() if r and i < 8})
    if len(seen) > 70:
        break
