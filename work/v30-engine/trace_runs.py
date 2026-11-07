#!/usr/bin/env python3
"""trace_runs.py <rec>...: distribution of per-frame call counts in each run, to separate run-to-run variation from real differences."""
import collections,glob,os,sys
K=["Draw","DrawIndexed","Map","IASetVertexBuffers","PSSetShader","OMSetBlendState","OMSetDepthStencilState","PSSetShaderResources","SetPredication"]
for R in sys.argv[1:]:
    fr=[]
    for p in glob.glob(R+"/trace_*.txt"):
        t=open(p).read().split()
        if len(t)>5000: fr.append(collections.Counter(t))
    print(os.path.basename(R),"steady frames",len(fr))
    for k in K:
        c=collections.Counter(f[k] for f in fr)
        print(f"  {k:24}",sorted(c.items()))
