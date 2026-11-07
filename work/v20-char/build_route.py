"""A walkable test route between the zone's encounters: a 2 m map of where a person fits, from terrain slope and collision, then A* between stops.
Writes work/v23-actors/route.bin (u32 count, then x, y, stop flag as floats) and a picture of it."""
import heapq,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
root=Path.home()/"Documents/Opem Amalur";import os
z=Path(os.environ.get("OA_ZONE_DIR",str(root/"work/v22-stress/zone-dal")));out=Path(os.environ.get("OA_ACTORS_DIR",str(root/"work/v23-actors")))
H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text());S=2
G=H[::S,::S].copy();ny,nx=G.shape;step=100.*S
valid=G==G;F=np.where(valid,G,np.inf)
with np.errstate(invalid="ignore"):
    sx=np.nan_to_num(np.abs(np.diff(F,axis=1,append=F[:,-1:])),posinf=0,neginf=0);sy=np.nan_to_num(np.abs(np.diff(F,axis=0,append=F[-1:,:])),posinf=0,neginf=0)
steep=(sx>step*.85)|(sy>step*.85)
sx[~np.isfinite(sx)]=0
block=steep&valid
print("cells",nx,ny,"no terrain",round(float((~valid).mean()),3),"steep",round(float(((sx>step*.85)|(sy>step*.85)).mean()),3))
C=np.load(z/"zone_col.npy",mmap_mode="r");N=len(C);print("collision shape",C.shape)
quads=None
# Terrain triangles come first in the collision soup, and are as many as the terrain grid's triangles.
t0=int((~np.isnan(H[:-1,:-1])&~np.isnan(H[:-1,1:])&~np.isnan(H[1:,:-1])&~np.isnan(H[1:,1:])).sum())*2;print("collision triangles",N,"terrain",t0)
CH=2000000
FLOOR=np.where(valid,np.inf,np.inf).astype(np.float64);FLOOR_HITS=[]
FLAT=F.copy()
for a in range(t0,N,CH):
    t=np.asarray(C[a:a+CH]).reshape(-1,3,3)
    if not len(t):break
    # Sample each triangle at about 1 m.
    long=np.maximum.reduce([np.linalg.norm(t[:,i]-t[:,(i+1)%3],axis=1) for i in range(3)]);n=np.minimum((long/100).astype(int)+1,40)
    for k in np.unique(n):
        q=t[n==k];u,v=np.meshgrid(np.linspace(0,1,k+1),np.linspace(0,1,k+1));m=u+v<=1;u,v=u[m],v[m]
        p=q[:,0,None,:]+(q[:,1,None,:]-q[:,0,None,:])*u[None,:,None]+(q[:,2,None,:]-q[:,0,None,:])*v[None,:,None];p=p.reshape(-1,3)
        i=((p[:,0]-gx)/step).astype(int);j=((p[:,1]-gy)/step).astype(int);ok=(i>=0)&(j>=0)&(i<nx)&(j<ny);i,j,zz=i[ok],j[ok],p[ok,2]
        # Where terrain is cut out, the lowest collision is the floor.
        np.minimum.at(FLOOR,(j,i),zz);FLOOR_HITS.append(None)
        base=np.where(np.isfinite(F[j,i]),F[j,i],FLOOR[j,i]);hit=(zz>base+40)&(zz<base+190);block[j[hit],i[hit]]=True
block|=~valid&~np.isfinite(FLOOR)
print("blocked",round(float(block.mean()),3),"cut cells with a floor",int((~valid&np.isfinite(FLOOR)).sum()),flush=True)
wide=block.copy();wide[1:]|=block[:-1];wide[:-1]|=block[1:];wide[:,1:]|=block[:,:-1];wide[:,:-1]|=block[:,1:]
b=(out/"index.bin").read_bytes();Ty,Na=struct.unpack_from("<II",b,4);types=[struct.unpack_from("<9f3iI24s",b,12+i*76) for i in range(Ty)];o=12+Ty*76
A=[(struct.unpack_from("<4f",b,o+i*20)[:3],struct.unpack_from("<H",b,o+i*20+16)[0]) for i in range(Na)]
cell=lambda x,y:(int((x-gx)/step),int((y-gy)/step))
def free_near(c,r=12):
    x,y=c
    if not(0<=x<nx and 0<=y<ny):return None
    for d in range(r):
        for dy in range(-d,d+1):
            for dx in range(-d,d+1):
                q=(x+dx,y+dy)
                if 0<=q[0]<nx and 0<=q[1]<ny and not wide[q[1],q[0]]:return q
    return None
def astar(s,t,limit=600000):
    D={s:0.};P={};Q=[(0.,s)];n=0
    while Q:
        _,c=heapq.heappop(Q);n+=1
        if c==t:
            r=[c]
            while c in P:c=P[c];r.append(c)
            return r[::-1]
        if n>limit:return None
        for dx,dy,w in ((1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)):
            q=(c[0]+dx,c[1]+dy)
            if not(0<=q[0]<nx and 0<=q[1]<ny) or wide[q[1],q[0]]:continue
            if dx and dy and (wide[c[1],q[0]] or wide[q[1],c[0]]):continue
            g=D[c]+w
            if g<D.get(q,1e18):
                D[q]=g;P[q]=c;heapq.heappush(Q,(g+((q[0]-t[0])**2+(q[1]-t[1])**2)**.5,q))
    return None
# The same map for the game's characters: bit set where a person does not fit.
bits=np.packbits(wide.reshape(-1).astype(np.uint8),bitorder="little")
(out/"nav.bin").write_bytes(struct.pack("<II3f",nx,ny,gx,gy,step)+bits.tobytes());print("nav bytes",20+len(bits))
door=tuple(float(x) for x in os.environ.get("OA_START","1575.1 -62759.2").split());at=free_near(cell(*door));print("start",at)
hostile=[free_near(cell(p[0],p[1])) for p,t in A if types[t][12]==2];hostile=[h for h in hostile if h];print("stops available",len(hostile))
left=set(hostile);route=[];legs=fails=0;TARGET=75
while left and legs<TARGET:
    near=sorted(left,key=lambda h:(h[0]-at[0])**2+(h[1]-at[1])**2)
    t=near[0];left={h for h in left if (h[0]-t[0])**2+(h[1]-t[1])**2>20**2}
    if (t[0]-at[0])**2+(t[1]-at[1])**2<15**2:continue
    r=astar(at,t)
    if r is None:fails+=1;continue
    for c in r[3::3]:route.append((gx+(c[0]+.5)*step,gy+(c[1]+.5)*step,0.))
    route.append((gx+(t[0]+.5)*step,gy+(t[1]+.5)*step,1.));at=t;legs+=1
    if legs%15==0:print("legs",legs,"waypoints",len(route),flush=True)
print("legs",legs,"unreachable",fails,"waypoints",len(route),"metres",round(sum(((route[i+1][0]-route[i][0])**2+(route[i+1][1]-route[i][1])**2)**.5 for i in range(len(route)-1))/100))
(out/"route.bin").write_bytes(struct.pack("<I",len(route))+b"".join(struct.pack("<3f",*w) for w in route))
im=np.zeros((ny,nx,3),np.uint8);im[valid]=(50,110,50);im[block]=(90,70,70)
for x,y,f in route:
    i,j=cell(x,y);im[max(0,j-1):j+2,max(0,i-1):i+2]=(255,230,40) if not f else (255,60,60)
Image.fromarray(im[::-1]).resize((nx*3//4,ny*3//4)).save(root/"work/v21-ui/live/route.png")
