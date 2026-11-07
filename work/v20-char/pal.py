import struct,json,collections
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/pal.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
mapn=syms.get("ragdoll_bone_mappings",{});nm=lambda v:str(mapn.get(str(v),v))
for fid in (1362163,301406,1930173):
    fs=extract([f"{fid}.fab_bxml",f"{fid}.fab_visual_data_streamable_bin"]);fb=fs[f"{fid}.fab_bxml"].read_bytes();raw=fs[f"{fid}.fab_visual_data_streamable_bin"].read_bytes();m=amalur_mesh.parse_file(fs[f"{fid}.fab_visual_data_streamable_bin"])
    n,par,names,world=skeleton(fb);P("==",fid,"fab bytes",len(fb),"joints",n,[(i,nm(names[i])) for i in range(n)][:30])
    # every chain
    chains=[];start=0
    while start<len(fb)-52:
        c=[];at=start
        while at+52<=len(fb):
            s=struct.unpack_from("<3f",fb,at+32);q=struct.unpack_from("<4f",fb,at+16);count,idx=struct.unpack_from("<II",fb,at+44)
            if not all(abs(x-1)<.02 for x in s) or abs(sum(x*x for x in q)-1)>.02 or idx>=n or count>300:break
            c.append((idx,count,nm(names[idx])));at+=52
        if c:chains.append((start,c));start=at
        else:start+=1
    P("palette chains",[(st,len(c)) for st,c in chains]);
    for st,c in chains:P(" ",st,c)
    for ai,a in enumerate(m["assemblies"]):
        vb=m["vertex_buffers"][a["vertex_buffer"]];st=vb["stride_bytes"];b=vb["data_file_offset"];mx=collections.Counter()
        for i in range(vb["vertex_count"]):
            jx=raw[b+i*st+12:b+i*st+16];w=struct.unpack_from("<4H",raw,b+i*st+16)
            w3=max(0,32767-sum(w[:3]))
            for k,wt in zip(jx,(w[0],w[1],w[2],w3)):
                if wt>0:mx[k]+=1
        P(" assembly",ai,{k:a[k] for k in a if k in("unknown_u16_at2","vertex_buffer","index_buffer") or "palette" in k or "bone" in k or "joint" in k},"keys",list(a.keys())[:14],"stride",st,"verts",vb["vertex_count"],"indices used",sorted(mx)[:40])
out.close()
