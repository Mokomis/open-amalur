#!/usr/bin/env python3
"""trace_counts.py <rec A> <rec B>: per-frame call counts by method for steady frames. Sequence order varies between runs, counts are the fair comparison."""
import collections,glob,re,statistics,sys
def load(R):
    d=collections.defaultdict(list);n=0
    for p in glob.glob(R+"/trace_*.txt"):
        t=open(p).read().split()
        if len(t)<=5000: continue
        n+=1; c=collections.Counter(t)
        for k,v in c.items(): d[k].append(v)
    return d,n
A,na=load(sys.argv[1]);B,nb=load(sys.argv[2])
print("steady frames",na,nb)
for k in sorted(set(A)|set(B),key=lambda k:-statistics.median(A.get(k,[0]))):
    x=statistics.median(A[k]) if k in A else 0; y=statistics.median(B[k]) if k in B else 0
    print(f"{'  ' if x==y else '* '}{k:30} {x:8} {y:8}")
