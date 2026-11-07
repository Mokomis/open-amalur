#!/usr/bin/env python3
"""job_size.py <decomp dir> <functions.tsv> <render_backend.tsv> <out>: size the decompile job from the call graph. Counts only."""
import collections,glob,re,sys
R,ft,rb,out=sys.argv[1:5]
head=re.compile(r"^// ([0-9a-f]{8}) (\S+)$",re.M)
sizes={}
for l in open(ft,encoding="utf-8"):
    p=l.rstrip("\n").split("\t")
    if p[0]!="address": sizes[p[0]]=int(p[1])
body={};name={}
for p in glob.glob(R+"/*.c"):
    t=open(p,errors="replace").read(); parts=head.split(t)
    for i in range(1,len(parts),3):
        body[parts[i]]=parts[i+2]; name[parts[i]]=parts[i+1]
by_name={n:a for a,n in name.items()}
tok=re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
callees={}
indirect={}
for a,b in body.items():
    c=set()
    for m in tok.findall(b):
        x=by_name.get(m)
        if x and x!=a: c.add(x)
    callees[a]=c
    indirect[a]=len(re.findall(r"\(\*\*?\(code \*",b))
def fam(n):
    if n.startswith("FUN_"): return "unnamed"
    for k,v in (("bt","Bullet"),("BHG_Bullet","BHG"),("OC3Ent","FaceFX"),("keen","keen sound"),("Kore","Kore"),("Z_","Z"),("std_","CRT"),("BHG","BHG"),("T_","templates"),("ConvexDecomposition","Bullet")):
        if n.startswith(k): return v
    return "other named"
fc=collections.Counter(); fb=collections.Counter()
for a,n in name.items():
    f=fam(n); fc[f]+=1; fb[f]+=sizes.get(a,0)
print("by family (functions, code KB)")
for f,c in fc.most_common(): print(f"  {f:14} {c:6} {fb[f]//1024:7}")
leaf=[a for a in body if not callees[a] and not indirect[a]]
print("total",len(body),"leaf with no calls",len(leaf),"code KB",sum(sizes.get(a,0) for a in leaf)//1024)
# layers: a function is ready once everything it directly calls is done. Indirect calls ignored here.
done=set(); layers=[]
rem=set(body)
while rem:
    ready={a for a in rem if callees[a]<=done}
    if not ready: break
    layers.append(len(ready)); done|=ready; rem-=ready
print("layers from direct calls",layers[:14],"...", "in layers",len(done),"stuck in cycles or above them",len(rem))
b=[0,32,64,128,256,1024,4096,1<<30]
h=collections.Counter()
for a in body:
    s=sizes.get(a,0)
    for i in range(len(b)-1):
        if b[i]<s<=b[i+1]: h[b[i+1]]+=1
print("bytes <=",sorted(h.items()))
print("code KB in functions under 256 bytes",sum(s for a,s in sizes.items() if s<=256)//1024,"of",sum(sizes.values())//1024)
rows=[]
for l in open(rb):
    p=l.rstrip("\n").split("\t")
    a=p[0]; rows.append((sizes.get(a,0),a,name.get(a,p[1]),int(p[2]),p[3][:60],len(callees.get(a,())),indirect.get(a,0)))
rows.sort()
print("render backend total bytes",sum(r[0] for r in rows),"functions",len(rows))
print("size addr name calls methods direct_callees indirect")
for r in rows[:40]: print(*r)
print("largest",[(r[0],r[1]) for r in rows[-8:]])
