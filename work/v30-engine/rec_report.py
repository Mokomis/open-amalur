#!/usr/bin/env python3
"""rec_report.py <oa_rec dir>: summary of a proxy recording."""
import collections, glob, os, re, struct, sys

R = sys.argv[1]
DXGI = {2: "RGBA32F", 6: "RGB32F", 10: "RGBA16F", 11: "RGBA16", 16: "RG32F", 24: "RGB10A2", 26: "R11G11B10F", 28: "RGBA8", 29: "RGBA8_sRGB", 34: "RG16F", 35: "RG16", 39: "R32T", 40: "D32F", 41: "R32F", 44: "R24G8T", 45: "D24S8", 46: "R24X8", 49: "RG8", 54: "R16F", 56: "R16", 57: "R16_SNORM", 61: "R8", 65: "A8", 71: "BC1", 72: "BC1_sRGB", 74: "BC2", 75: "BC2_sRGB", 77: "BC3", 78: "BC3_sRGB", 80: "BC4", 83: "BC5", 87: "BGRA8", 88: "BGRX8", 91: "BGRA8_sRGB"}

traces = sorted(glob.glob(R + "/trace_*.txt"), key=lambda p: int(re.findall(r"(\d+)\.txt", p)[0]))
print("traces", len(traces))
t = open(traces[-1]).read().split()
print("last trace", os.path.basename(traces[-1]), "calls", len(t))
c = collections.Counter(t)
for k, v in c.most_common(30):
    print(f"  {v:7} {k}")

print("\nsequence by render target binding (calls in each group)")
groups, cur = [], None
for m in t:
    if m == "OMSetRenderTargets":
        if cur:
            groups.append(cur)
        cur = collections.Counter()
    elif cur is not None:
        cur[m] += 1
if cur:
    groups.append(cur)
print(" binds", len(groups))
for i, g in enumerate(groups[:70]):
    d = g["DrawIndexed"] + g["Draw"] + g["DrawIndexedInstanced"] + g["DrawInstanced"]
    print(f"  {i:3} draws {d:5} pred {g['SetPredication']:5} begin {g['Begin']:5} clearRT {g['ClearRenderTargetView']} clearDS {g['ClearDepthStencilView']} copy {g['CopyResource'] + g['CopySubresourceRegion']} resolve {g['ResolveSubresource']} vsset {g['VSSetShader']}")

sizes = [len(open(p).read().split()) for p in traces]
print("\ncalls per trace", sizes)

fmt, usage, dims = collections.Counter(), collections.Counter(), collections.Counter()
rt = collections.Counter()
misc = collections.Counter()
layouts = set()
for line in open(R + "/resources.txt", errors="replace"):
    p = line.split()
    if len(p) < 2:
        continue
    if p[1] == "tex2d":
        kv = dict(x.split("=") for x in p[3:])
        f = DXGI.get(int(kv["fmt"]), kv["fmt"])
        fmt[f] += 1
        b = int(kv["bind"], 16)
        if b & 0x60:
            rt[f"{p[2]} {f} samples={kv['samples']} bind={kv['bind']} mips={kv['mips']}"] += 1
    elif p[1] == "layout":
        layouts.add(" ".join(p[2:]))
    elif p[1] in ("predicate", "query"):
        misc[" ".join(p[1:])] += 1
    elif p[1] in ("swapchain", "D3D11CreateDevice", "real"):
        print(" ".join(p[1:]))
print("\ntexture formats", fmt.most_common())
print("\nrender and depth targets")
for k, v in rt.most_common(40):
    print(f"  {v:3} {k}")
print("\ninput layouts", len(layouts))
print("predicates and queries", misc.most_common())

kinds = collections.Counter()
models = collections.Counter()
total = 0
for p in glob.glob(R + "/shaders/*.dxbc"):
    d = open(p, "rb").read()
    total += len(d)
    kinds[os.path.basename(p)[:2]] += 1
    n = struct.unpack_from("<I", d, 28)[0]
    for i in range(n):
        o = struct.unpack_from("<I", d, 32 + 4 * i)[0]
        if d[o:o + 4] in (b"SHEX", b"SHDR"):
            v = struct.unpack_from("<I", d, o + 8)[0]
            models[f"{(v >> 16) & 0xffff}:{(v >> 4) & 15}.{v & 15}"] += 1
print("\nshaders on disk", dict(kinds), "bytes", total, "versions (type:major.minor, 0=ps 1=vs)", models.most_common())
