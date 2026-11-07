#!/usr/bin/env python3
"""callers_map.py <callers.txt> <functions.tsv> <names.tsv> <out.tsv>: exact engine functions calling Direct3D."""
import bisect,collections,sys
cf,ft,nt,out=sys.argv[1:5]
F=[]
for l in open(ft,encoding="utf-8"):
    p=l.rstrip("\n").split("\t")
    if p[0]!="address": F.append((int(p[0],16),int(p[1]),p[4]))
F.sort(); S=[f[0] for f in F]
N={}
for l in open(nt):
    p=l.rstrip("\n").split("\t")
    if p[0]!="address": N[int(p[0],16)]=p[1]
def own(a):
    i=bisect.bisect_right(S,a)-1
    if i>=0: return S[i],N.get(S[i],F[i][2]),a<S[i]+max(F[i][1],1)
    return None,"?",False
per=collections.defaultdict(lambda:collections.Counter()); outside=collections.Counter(); calls=collections.Counter()
for l in open(cf):
    p=l.split()
    if len(p)!=4 or p[2]=="overflow": 
        if len(p)==4: print("OVERFLOW",p)
        continue
    a=int(p[2],16); c=int(p[3])
    if not 0x400000<=a<0x1800000: outside[p[1]]+=c; continue
    f,n,inside=own(a)
    per[(f,n)][p[1]]+=c; calls[p[1]]+=c
print("engine functions calling D3D",len(per))
print("calls from outside koa.exe",outside.most_common(12))
rows=sorted(per.items(),key=lambda kv:-sum(kv[1].values()))
with open(out,"w") as w:
    for (f,n),m in rows:
        w.write(f"{f:08x}\t{n}\t{sum(m.values())}\t{','.join(k+':'+str(v) for k,v in m.most_common())}\n")
for (f,n),m in rows[:30]:
    print(f"{f:08x} {n[:44]:44} {sum(m.values()):>10} {','.join(k for k,_ in m.most_common(4))}")
reg=collections.Counter((f>>20) for (f,n),m in rows)
print("by 1MB region",sorted((hex(k<<20),v) for k,v in reg.items()))
for meth in ("DrawIndexed","Draw","SetPredication","Begin","End","OMSetRenderTargets","Map","CreateTexture2D","CreateVertexShader","ClearDepthStencilView","CopySubresourceRegion"):
    print(meth,[ (n[:36],c[meth]) for (f,n),c in rows if c[meth]][:10])
