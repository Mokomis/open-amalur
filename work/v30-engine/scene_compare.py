#!/usr/bin/env python3
"""scene_compare.py <v30 dir> <functions.tsv> <names.tsv>: compare rewrite and original per scene over the last 6000 frames, plus new D3D callers."""
import bisect,collections,csv,os,statistics as st,sys
E=sys.argv[1]
K=["DrawIndexed","Draw","SetPredication","Begin","OMSetRenderTargets","Map","PSSetShader"]
F=[]
for l in open(sys.argv[2],encoding="utf-8"):
    p=l.rstrip("\n").split("\t")
    if p[0]!="address": F.append(int(p[0],16))
F.sort()
base=set()
for l in open(os.path.join(E,"render_backend.tsv")): base.add(int(l.split("\t")[0],16))
def callers(R):
    s=collections.Counter()
    for l in open(R+"/callers.txt"):
        p=l.split()
        if len(p)==4 and p[2]!="overflow":
            a=int(p[2],16)
            if 0x400000<=a<0x1800000: s[F[bisect.bisect_right(F,a)-1]]+=int(p[3])
    return s
for sc in ("dal","ysa","haxhi"):
    print("==",sc)
    seen={}
    for m in ("rewrite","rewrite2","original"):
        R=f"{E}/oa_rec-{sc}-{m}"
        if not os.path.exists(R+"/frames.csv"): print(" ",m,"missing"); continue
        rows=list(csv.DictReader(open(R+"/frames.csv")))
        w=rows[-6000:]
        out=[f"{k}={st.median(int(r[k]) for r in w):.0f}[{min(int(r[k]) for r in w)}-{max(int(r[k]) for r in w)}]" for k in K]
        print(f"  {m:9} frames {len(rows)}",*out)
        seen[m]=callers(R)
        new=[f"{a:08x}" for a in seen[m] if a not in base]
        print(f"    D3D callers {len(seen[m])}, not in the Odarath list {len(new)}",new[:24])
