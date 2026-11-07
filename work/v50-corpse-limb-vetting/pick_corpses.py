from pathlib import Path
import json,struct,hashlib,collections
import numpy as np
R=Path(r"C:\Users\rwill\Documents\Opem Amalur");O=Path(__file__).resolve().parent
W=R/"work/v48-opening/integration/probe-preview-closed-container/world"
camera_path=R/"work/v50-character-complete/ui-integration/live-before-v50-preview-promotion.json"
cam=json.loads(camera_path.read_text());M=np.array(cam["mvp_column_major"]).reshape((4,4),order="F");inv=np.linalg.inv(M);eye=np.array(cam["eye"])
src={r["source_index"]:r for r in json.loads((R/"work/v48-opening/content-audit/1417252-source-render-records.json").read_text())}
ri=(W/"region-index.bin").read_bytes();assert ri[:8]==b"OARGIDX1";scale=struct.unpack_from("<f",ri,16)[0]
pixels=[(1450,375),(1395,353),(1330,345),(1480,400),(170,285),(100,285),(280,280)]
tris=[];owners=[]
for f in sorted(W.glob("r*_*.bin")):
 b=f.read_bytes();magic,nv,ni,nd,vs,rs=struct.unpack_from("<8s5I",b);assert(magic,vs,rs)==(b"OARGEO1\0",76,48)
 va=28+nd*48;ia=va+nv*76;V=np.ndarray((nv,3),"<f4",b,va,(76,4)).astype(float);I=np.frombuffer(b,"<u4",ni,ia);mids=np.ndarray((nv,),"<u4",b,va+68,(76,))
 for di in range(nd):
  row=struct.unpack_from("<4I6fIf",b,28+48*di);mr,first,n,flags=row[:4];anchor=np.array(row[4:7]);d2=float(np.dot(anchor-eye,anchor-eye))*(row[11]or scale)**2
  if not(row[8]<=d2<row[9]):continue
  ii=I[first:first+n].reshape(-1,3);t=V[ii];mid=int(mids[ii[0,0]])if len(ii)else 0
  tris.append(t);owners.extend([dict(file=f.name,draw=di,triangle=j,source=row[10],mid=mid,flags=flags,distance=np.sqrt(d2),range_sq=list(row[8:10]))for j in range(len(ii))])
T=np.concatenate(tris);A=T[:,0];E1=T[:,1]-A;E2=T[:,2]-A;hits=[]
for px,py in pixels:
 ndc=np.array([2*(px+.5)/cam["width"]-1,1-2*(py+.5)/cam["height"],1,1]);far=inv@ndc;far=far[:3]/far[3];ray=far-eye;ray/=np.linalg.norm(ray)
 p=np.cross(np.broadcast_to(ray,E2.shape),E2);det=np.einsum("ij,ij->i",E1,p);good=abs(det)>1e-8;iv=np.where(good,1/det,0)
 tv=eye-A;u=np.einsum("ij,ij->i",tv,p)*iv;q=np.cross(tv,E1);v=q@ray*iv;distance=np.einsum("ij,ij->i",E2,q)*iv
 good&=(u>=0)&(v>=0)&(u+v<=1)&(distance>0)
 ix=np.flatnonzero(good);ix=ix[np.argsort(distance[ix])][:8];rr=[]
 for k in ix:
  r=dict(owners[k]);s=src.get(r["source"]);r.update(world_hit=(eye+ray*distance[k]).tolist(),distance_cm=float(distance[k]),fab=s["fab"]if s else None,assembly=s["assembly"]if s else None,source_name=s["name"]if s else None,barycentric=[float(1-u[k]-v[k]),float(u[k]),float(v[k])],source_transform={a:s[a]for a in["translation","quaternion","scale"]}if s else None);rr.append(r)
 hits.append(dict(pixel=[px,py],ray=ray.tolist(),hits=rr))
result=dict(camera=cam,camera_sha256=hashlib.sha256(camera_path.read_bytes()).hexdigest(),world=str(W.relative_to(R)),registry_scale=scale,active_triangles=len(T),hits=hits,policy="Read-only CPU geometry ray; no alpha/cull emulation. Corpse material442846 is sourceopaque; nearestbodyhit maystillbeoccludedbyothergeometry.")
(O/"corpse-pixel-hits.json").write_text(json.dumps(result,indent=2))
print(json.dumps([dict(pixel=r["pixel"],hits=[{k:h[k]for k in["fab","source_name","assembly","source","mid","distance_cm"]}for h in r["hits"][:3]])for r in hits],indent=2))
