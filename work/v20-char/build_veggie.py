"""Real foliage placement: match each veggie block to its terrain tile by height, read its density layers."""
import collections,json,os,pickle,struct,sys,zlib
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";inp=root/"work/v20-inputs";wc=root/"work/v20-char"
out=Path(os.environ.get("OA_ZONE_DIR",str(root/"work/v22-stress/zone-dal")));out.mkdir(parents=True,exist_ok=True);tdir=Path(os.environ.get("OA_TERRAIN_DIR",str(root/"work/v24-zones/dal")));tid=os.environ.get("OA_TERRAIN_ID","431658")
import subprocess
g=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
if not (inp/f"DATA_0.pak/{tid}.veggie_streamable_bin").exists():subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data/DATA_0.pak"),"unpack",str(inp/"DATA_0.pak"),f"{tid}.veggie_streamable_bin"],cwd=g/"modding",capture_output=True,timeout=280)
vb=(inp/f"DATA_0.pak/{tid}.veggie_streamable_bin").read_bytes()
pos=0;blocks=[]
while True:
    i=vb.find(b"\x78\x9c",pos)
    if i<0:break
    try:
        do=zlib.decompressobj();d=do.decompress(vb[i:i+400000]);pos=i+min(400000,len(vb)-i)-len(do.unused_data);blocks.append(d)
    except Exception:pos=i+2
print("blocks",len(blocks))
# Layout: height grid; counted byte mask; low, high, tag, zero; then counted float density grids; 16 trailing bytes.
parsed=[];lays=collections.Counter();stats=[]
for d in blocks:
    n=struct.unpack_from("<I",d,0)[0]
    if n!=4225:continue
    h=np.frombuffer(d,"<f4",n,4).reshape(65,65);o=4+n*4
    c=struct.unpack_from("<I",d,o)[0];o+=4
    mask=np.frombuffer(d,"u1",c,o).reshape(65,65) if c==4225 else None;o+=c
    lo,hi,tag=struct.unpack_from("<ffI",d,o);o+=12
    if struct.unpack_from("<I",d,o)[0]==0:o+=4
    layers=[]
    while o+4+16900<=len(d) and struct.unpack_from("<I",d,o)[0]==4225:
        layers.append(np.frombuffer(d,"<f4",4225,o+4).reshape(65,65));o+=4+16900
    lays[len(layers)]+=1
    parsed.append((h,mask,layers))
    for a2 in layers:
        if np.any(a2): stats.append((float(a2.max()),float(a2.mean()),float((a2>0).mean())))
print("layers per block",lays.most_common(10))
st=np.array(stats);print("float layer stats: max pct",np.percentile(st[:,0],[50,90,100]).round(3),"mean pct",np.percentile(st[:,1],[50,90,100]).round(4),"nonzero pct",np.percentile(st[:,2],[50,90,100]).round(3))
print("mask mean",round(float(np.mean([p[1].mean() for p in parsed if p[1] is not None])),1))
# Terrain grid at 1 m, cached.
Hp=out/"terrain_H.npy"
if Hp.exists():
    H=np.load(Hp);gx0,gy0=json.loads((out/"terrain_H.json").read_text())
else:
    grids=pickle.load(open(tdir/"terrain-grids.pkl","rb"));masks=pickle.load(open(tdir/"terrain-masks.pkl","rb"));abs_pos=pickle.load(open(tdir/"terrain-abs.pkl","rb"));fit=json.loads((tdir/"terrain-fit.json").read_text())
    level=collections.defaultdict(dict)
    for n,(x,y,w) in abs_pos.items():level[w][(x,y)]=n
    ORIGIN=-102425.0
    xs=[x*50+ORIGIN for x,y,w in abs_pos.values()];ys=[y*50+ORIGIN for x,y,w in abs_pos.values()];x1=[x*50+ORIGIN+w*50 for x,y,w in abs_pos.values()];y1=[y*50+ORIGIN+w*50 for x,y,w in abs_pos.values()]
    gx=np.arange(np.floor(min(xs)/100)*100,max(x1)+100,100.);gy=np.arange(np.floor(min(ys)/100)*100,max(y1)+100,100.)
    H=np.full((len(gy),len(gx)),np.nan,np.float32);HF=H.copy()
    def ground(wx,wy):
        ux,uy=(wx-ORIGIN)/50,(wy-ORIGIN)/50
        for w in sorted(level):
            px,py=int(ux//w)*w,int(uy//w)*w;n=level[w].get((px,py))
            if n is None:continue
            v=grids[n][2];fx,fy=(ux-px)*16/w+1,(uy-py)*16/w+1;ix,iy=int(fx),int(fy);q=(v[iy*19+ix],v[iy*19+ix+1],v[(iy+1)*19+ix],v[(iy+1)*19+ix+1])
            if 65535 in q:continue
            m=masks[n]
            cut=m is not None and not(m[iy*19+ix] or m[iy*19+ix+1] or m[(iy+1)*19+ix] or m[(iy+1)*19+ix+1])
            q=tuple(x-65536 if x>=32768 else x for x in q)  # Heights are signed.
            ax,ay=fx-ix,fy-iy;return (q[0]*(1-ax)*(1-ay)+q[1]*ax*(1-ay)+q[2]*(1-ax)*ay+q[3]*ax*ay)*fit["k"]+fit["z0"],cut
        return None
    for j,wy in enumerate(gy):
        for i,wx in enumerate(gx):
            h=ground(float(wx),float(wy))
            if h is not None:
                HF[j,i]=h[0]
                if not h[1]:H[j,i]=h[0]
    np.save(Hp,H);np.save(out/"terrain_Hfull.npy",HF);gx0,gy0=float(gx[0]),float(gy[0]);(out/"terrain_H.json").write_text(json.dumps([gx0,gy0]))
print("H",H.shape,gx0,gy0)
# Foliage tiles keep heights under cut-out cells too, so they match against the uncut map; clumps in cut-outs go.
Hcut=H;H=np.load(out/"terrain_Hfull.npy")
# Tiles are 32 m with heights on a 0.5 m lattice; other tile sizes are tried too.
ORIGIN=-102425.0;ny,nx=H.shape;pts=np.array([0,8,16,24,32,40,48,56,64])
matched=[];errs=[];unmatched=0;sizes=collections.Counter()
cands={}
for TILE,step in ((3200.0,50.0),(6400.0,100.0),(1600.0,25.0),(12800.0,200.0)):
    ox=np.arange(np.ceil((gx0-ORIGIN)/TILE)*TILE+ORIGIN,gx0+nx*100-TILE+1,TILE);oy=np.arange(np.ceil((gy0-ORIGIN)/TILE)*TILE+ORIGIN,gy0+ny*100-TILE+1,TILE)
    A=np.full((len(oy),len(ox),9,9),np.nan,np.float32)
    for yi,wy in enumerate(oy):
        for xi,wx in enumerate(ox):
            ii=np.clip(((wx+pts*step-gx0)/100).round().astype(int),0,nx-1);jj=np.clip(((wy+pts*step-gy0)/100).round().astype(int),0,ny-1);A[yi,xi]=H[np.ix_(jj,ii)]
    cands[TILE]=(ox,oy,A,np.nan_to_num(A,nan=-1e9),step)
for h,mask,layers in parsed:
    q=h[np.ix_(pts,pts)].astype(np.float32);best=(1e9,None)
    for TILE,(ox,oy,A,Af,step) in cands.items():
        e=np.abs(Af-q);e=np.where(e>1e6,0,e);v=(A==A).sum((2,3));m=e.sum((2,3))/np.maximum(v,1);m[v<40]=1e9
        yi,xi=np.unravel_index(np.argmin(m),m.shape)
        if m[yi,xi]<best[0]:best=(float(m[yi,xi]),(float(ox[xi]),float(oy[yi]),step,TILE))
    errs.append(best[0])
    if best[0]<30:matched.append((best[1],h,layers));sizes[best[1][3]]+=1
    else:unmatched+=1
print("matched",len(matched),"unmatched",unmatched,"sizes",sizes,"err pct",np.percentile(errs,[10,50,90]).round(2))
rng=np.random.default_rng(431658);rows=[];per=collections.Counter();density=[]
for (x0,y0,step,T),h,layers in matched:
    for li,a in enumerate(layers):
        j,i=np.nonzero(a>0)
        if not len(j):continue
        # Authored reading: the float is the chance one lattice sample holds a clump.
        keep=rng.random(len(j))<np.clip(a[j,i],0,1);j,i=j[keep],i[keep];per[li]+=len(j)
        wx=x0+i*step+rng.random(len(j))*step;wy=y0+j*step+rng.random(len(j))*step;wz=h[j,i]
        rows.append(np.stack([wx,wy,wz,np.full(len(j),li,np.float32)],1).astype(np.float32))
    density.append(sum(float(np.clip(a,0,1).sum()) for a in layers)/((step*64/100)**2))
G=np.concatenate(rows) if rows else np.zeros((0,4),np.float32)
if len(G):
    gi=np.clip(((G[:,0]-gx0)/100).astype(int),0,Hcut.shape[1]-1);gj=np.clip(((G[:,1]-gy0)/100).astype(int),0,Hcut.shape[0]-1);G=G[Hcut[gj,gi]==Hcut[gj,gi]]
np.save(out/"zone_grass.npy",G);print("clumps",len(G),"per layer",per.most_common(12));print("clumps per m2 by tile pct",np.percentile(density,[50,90,99]).round(2),"mean",round(float(np.mean(density)),3))
