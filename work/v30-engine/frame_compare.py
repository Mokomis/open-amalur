#!/usr/bin/env python3
"""frame_compare.py <rec>...: per-frame count distributions over the steady part of each run, and any odd frames."""
import collections,csv,glob,os,sys
for R in sys.argv[1:]:
    rows=list(csv.DictReader(open(R+"/frames.csv")))
    steady=[r for r in rows if int(r["DrawIndexed"])>1000]
    print("==",os.path.basename(R),"frames",len(rows),"steady",len(steady),"first steady",steady[0]["frame"] if steady else None,"last",steady[-1]["frame"] if steady else None)
    for k in ("DrawIndexed","Draw","SetPredication","Begin","OMSetRenderTargets","OMSetBlendState","OMSetDepthStencilState","PSSetShader","Map"):
        c=collections.Counter(int(r[k]) for r in steady)
        print(f"  {k:24}",sorted(c.items())[:14])
    cc=collections.Counter(int(r["DrawIndexed"]) for r in steady)
    common=cc.most_common(1)[0][0] if cc else 0
    odd=[int(r["frame"]) for r in steady if int(r["DrawIndexed"])!=common]
    print("  commonest DrawIndexed",common,"odd frames",len(odd),odd[:24])
    if len(odd)>2:
        d=[b-a for a,b in zip(odd,odd[1:])]
        print("  gaps between odd frames",collections.Counter(d).most_common(8))
    print("  odd dumps",len(glob.glob(R+"/odd_*.txt")))
