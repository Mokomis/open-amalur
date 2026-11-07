#!/usr/bin/env python3
"""trace_diff.py <rec A> <rec B>: compare steady-state frame traces call by call."""
import collections,difflib,glob,re,sys
def load(R):
    out=[]
    for p in sorted(glob.glob(R+"/trace_*.txt"),key=lambda p:int(re.findall(r"(\d+)\.txt",p)[0])):
        t=open(p).read().split()
        if len(t)>5000: out.append(t)
    return out
A,B=load(sys.argv[1]),load(sys.argv[2])
print("steady traces",len(A),len(B))
if not A or not B: sys.exit()
ca=collections.Counter(tuple(t) for t in A); cb=collections.Counter(tuple(t) for t in B)
a=ca.most_common(1)[0][0]; b=cb.most_common(1)[0][0]
print("A commonest frame",len(a),"seen",ca[a],"of",len(A),"variants",len(ca))
print("B commonest frame",len(b),"seen",cb[b],"of",len(B),"variants",len(cb))
if a==b: print("SEQUENCE IDENTICAL"); sys.exit()
x=collections.Counter(a); y=collections.Counter(b)
print("count differences",{k:(x[k],y[k]) for k in set(x)|set(y) if x[k]!=y[k]})
s=difflib.SequenceMatcher(None,a,b,autojunk=False) if len(a)<40000 else None
if s:
    ops=[o for o in s.get_opcodes() if o[0]!="equal"]
    print("edit blocks",len(ops))
    for o in ops[:12]: print(" ",o[0],"A",o[1],o[2],a[o[1]:min(o[2],o[1]+8)],"B",o[3],o[4],b[o[3]:min(o[4],o[3]+8)])
