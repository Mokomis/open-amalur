#!/usr/bin/env python3
"""render_map.py <decomp dir> <out>: find the code that talks to Direct3D by vtable offset in the decompile. Counts only, no code copied."""
import collections, glob, os, re, sys
R, out = sys.argv[1:3]
CTX = {0x30:"DrawIndexed",0x34:"Draw",0x38:"Map",0x3c:"Unmap",0x6c:"Begin",0x70:"End",0x78:"SetPredication",0x84:"OMSetRenderTargets",0x9c:"Unused"}
pat = re.compile(r"\*\*?\(code \*\*\)\(\*[^\n]{0,40}?\+ (0x[0-9a-f]+)\)\)")
head = re.compile(r"^// ([0-9a-f]+) (\S+)$", re.M)
total=0; ok=0; size=0; byfile=[]
marks = {"D3D11CreateDevice":0,"SetPredication":0}
strs = collections.Counter()
hits = collections.defaultdict(list)
for p in glob.glob(R+"/*.c"):
    t=open(p,errors="replace").read(); size+=len(t)
    parts=head.split(t)
    byfile.append((len(parts)//3, os.path.basename(p)))
    for i in range(1,len(parts),3):
        addr,name,body=parts[i],parts[i+1],parts[i+2]
        total+=1
        if "decompile failed" not in body[:60]: ok+=1
        if "D3D11CreateDevice" in body: hits["creates_device"].append((addr,name))
        off=set(int(m,16) for m in pat.findall(body))
        d3d=off & {0x30,0x34,0x78,0x84,0xb8}
        if len(off & {0x30,0x34})>=1 and len(off&{0x38,0x3c,0x48,0x4c,0x50,0x60,0x84,0xac,0xb0})>=1: hits["draw_like"].append((addr,name))
        if 0x78 in off and (0x6c in off or 0x70 in off or 0x30 in off): hits["predication_like"].append((addr,name))
        if re.search(r"Scaleform|GFx",body): hits["scaleform"].append((addr,name))
print("functions",total,"decompiled",ok,"chars",size,"files",len(byfile))
print("largest files",sorted(byfile,reverse=True)[:14])
named=sum(1 for n,f in byfile if not f.startswith("unnamed_"))
for k,v in hits.items():
    print(k,len(v),[n for a,n in v[:25]])
with open(out,"w") as w:
    for k,v in hits.items():
        for a,n in v: w.write(f"{k}\t{a}\t{n}\n")
