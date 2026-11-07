import json,struct,sys
from pathlib import Path
import numpy as np
O=Path(__file__).resolve().parent
cat=json.loads((O/"appearance-source-catalogue.json").read_text())
def read(sid):
 b=(O/f"models/{sid}.oaam").read_bytes();ch={t.decode():(o,n,s) for t,o,n,s in struct.iter_unpack("<4sIII",b[32:32+16*struct.unpack_from("<I",b,20)[0]])};o,n,s=ch["BONE"];bones=[];world=[]
 for i in range(n):
  at=o+i*s;par,h=struct.unpack_from("<iI",b,at);row=struct.unpack_from("<12f",b,at+8);x,y,z,w=[-v for v in row[:3]]+[row[3]];m=np.eye(4);m[:3,:3]=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]];m[:3,3]=row[4:7]
  assert par<i or par==i or par==-1
  world.append(m if par in [-1,i] else world[par]@m);bones.append(dict(parent=par,hash=h,local=m))
 return bones,world
roots={s:read(s) for s in [1507280,1507282,456813,611642]};rows=[]
types={t["id"]:t for t in cat["types"]}
allowed={}
for name,sid in cat["creator_types"].items():
 sex=1 if name.endswith("_Male") else 2;rig=1507280 if sex==1 else 1507282;race={"Almain":64,"Varani":128,"Ljosalfar":512,"Dokkalfar":1024}[name.split("_")[0]]
 ids=set(x[0] for x in types[sid]["rendering"]["attachments"])
 for r in cat["options"]:
  if r["race_mask"]&race and r["gender_mask"]&sex:
   rr=types[r["asset_id"]].get("rendering",{});ids.update(v for v in rr.get("model_variants",[]) if v)
 for fab in ids:allowed.setdefault((fab,rig),[]).append(name)
for (sid,rig),names in sorted(allowed.items()):
 bones,world=read(sid);rb,rw=roots[rig];rh={r["hash"]:i for i,r in enumerate(rb)};shared=[];missing=[]
 for i,b in enumerate(bones):
  j=rh.get(b["hash"])
  if j is None:missing.append(dict(bone=i,hash=b["hash"],parent=b["parent"]));continue
  e=world[i]-rw[j];shared.append(dict(bone=i,root_joint=j,translation_error=float(np.max(np.abs(e[:3,3]))),basis_error=float(np.max(np.abs(e[:3,:3])))))
 rows.append(dict(fab=sid,rig=rig,types=names,bones=len(bones),shared=len(shared),unmatched=missing,max_translation_error=max([v["translation_error"] for v in shared],default=0),max_basis_error=max([v["basis_error"] for v in shared],default=0),matches=shared))
(O/"component-rig-audit.json").write_text(json.dumps(dict(rows=rows,limit="Comparison is source bind evidence; does not prove native runtime attachment/pose transfer. All own bones retained, no nearestancestor collapse."),indent=2))
print(json.dumps(dict(pairs=len(rows),max_translation=max(r["max_translation_error"] for r in rows),max_basis=max(r["max_basis_error"] for r in rows),worst=sorted([{k:r[k] for k in ["fab","rig","shared","bones","max_translation_error","max_basis_error"]} for r in rows],key=lambda r:r["max_translation_error"],reverse=True)[:8]),indent=2))
