"""Bounded source-only reverse projection guard for the reported sky opening."""
from pathlib import Path
import json,struct,collections
import numpy as np
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
meta=json.loads((P/'work/v44-native-fidelity/bridge-native-final-r2.json').read_text());vp=np.array(meta['mvp_column_major'],float).reshape(4,4,order='F');eye=np.array(meta['eye']);width,height=meta['width'],meta['height'];rect=np.array([[950.,0.],[1020.,180.]])
prov={r['source_index']:r for r in json.loads((Q/'region-aux-full-source-provenance.json').read_text())}
native=json.loads((Q/'region-native-tree-correspondence.json').read_text());byrecord=collections.defaultdict(set);bypose=collections.defaultdict(set)
def posekey(r):return (r['fab'],tuple(r['translation']),tuple(r['quaternion']),tuple(r['scale']))
for d in native:
 for m in d['matches']:
  r=m['source_record'];byrecord[(r['group'],r['record'])].add(d['draw']);bypose[posekey(r)].add(d['draw'])
results={};active={};soup={}
def overlaps(t):
 lo=t.min(1);hi=t.max(1);ok=np.all(hi>=rect[0],axis=1)&np.all(lo<=rect[1],axis=1)
 # Triangle edge normals provide the remaining separating axes; rectangle axes above.
 for i in range(3):
  edge=t[:,(i+1)%3]-t[:,i];normal=np.c_[-edge[:,1],edge[:,0]];dot=np.einsum('nkj,nj->nk',t,normal);corners=np.array([[950,0],[1020,0],[1020,180],[950,180]]);rdot=normal@corners.T
  ok&=(dot.max(1)>=rdot.min(1))&(dot.min(1)<=rdot.max(1))
 return ok
for f in (Q/'candidate-world-full').glob('r*.bin'):
 if f.name=='region-index.bin':continue
 b=f.read_bytes();magic,nv,ni,nd,vs,rs=struct.unpack_from('<8s5I',b);assert magic==b'OARGEO1\0' and vs==76 and rs==48
 verts=np.ndarray((nv,3),'<f4',b,28+48*nd,(76,4)).astype(float);ix=np.frombuffer(b,'<u4',ni,28+48*nd+76*nv)
 for j in range(nd):
  mat,first,count,flags,x,y,z,r,lo,hi,source,scale=struct.unpack_from('<4I6fIf',b,28+48*j);s=prov[source];distance=float(np.linalg.norm(eye-[x,y,z]));scale=scale or .5;d2=(distance*scale)**2
  if not(lo<=d2<=hi):continue
  active[source]=s
  tri=verts[ix[first:first+count]].reshape(-1,3,3);clips=np.concatenate([tri,np.ones((*tri.shape[:2],1))],axis=2)@vp.T
  front=np.all(clips[:,:,3]>0,axis=1)
  clips=clips[front]
  if not len(clips):continue
  screen=np.stack([(clips[:,:,0]/clips[:,:,3]+1)*width*.5,(1-clips[:,:,1]/clips[:,:,3])*height*.5],axis=2)
  hit=overlaps(screen)
  if not hit.any():continue
  ndcz=clips[:,:,2]/clips[:,:,3];hit&=(ndcz.max(1)>=-1)&(ndcz.min(1)<=1)
  if not hit.any():continue
  row=results.setdefault(source,dict(source_index=source,fab=s['fab'],fab_name=s['fab_name'],assembly=s['assembly'],native_material=s['native_material'],material_row=s['material_row'],family=s['family'],translation=s['translation'],quaternion=s['quaternion'],scale=s['scale'],group=s['group'],record=s['record'],distance_cm=distance,scaled_distance_cm=distance*scale,interval_squared=[lo,hi],captured_same_record_draws=sorted(byrecord[(s['group'],s['record'])]),captured_same_physical_pose_draws=sorted(bypose[posekey(s)]),projected_triangles=0,screen_bounds=None,cells=[]))
  row['projected_triangles']+=int(hit.sum());row['cells'].append(f.name);bb=np.stack([screen[hit].min((0,1)),screen[hit].max((0,1))])
  if row['screen_bounds'] is not None:bb=np.stack([np.minimum(row['screen_bounds'][0],bb[0]),np.maximum(row['screen_bounds'][1],bb[1])])
  row['screen_bounds']=bb.tolist()
  soup.setdefault(source,[]).append(screen[hit])
# Overlapping active ranges for a physical source pose are not automatically duplicates:
# trunk/branch/leaves and shadow/pass records may coexist. Report material+assembly.
groups=collections.defaultdict(list)
for i,s in active.items():groups[posekey(s)].append(i)
rows=sorted(results.values(),key=lambda r:(not bool(r['captured_same_physical_pose_draws']),-r['projected_triangles']))
report=dict(scope='Existing frozen fullregionalpack geometry and capturecamera only; no alpha/depth/lighting replay, no native queries.',rectangle_pixels=rect.tolist(),camera=meta,region_distance_scale=.5,active_source_records=len(active),active_physical_poses=len(groups),rectangle_candidate_records=len(rows),rectangle_candidate_poses=len({posekey(prov[r['source_index']]) for r in rows}),candidate_records_without_same_pose_capture=sum(not bool(r['captured_same_physical_pose_draws']) for r in rows),candidate_records_without_same_record_capture=sum(not bool(r['captured_same_record_draws']) for r in rows),rows=rows,limits=['Projected triangle/rectangle intersection proves geometric candidates only; raw alpha, culling, occlusion and final visibility not evaluated.','Captureset covers189cataloguedtreeGBufferdraws, not everyopaque/skyline/nativepass; absenttreecapturewitness is notalone evidence of extraobjects.','Fullregionpackselection preserveswholeauthorrecord and mayprojectoutsideoriginal203centroidcells.','Forward97/97LODfitdoesnotproveabsenceofextraregionalactiveposes orcorrectLODpolicy.','Trianglecrossingeyewithsomeverticesbehindcamera omitted; reported openingcandidatesallfullyinfront.'])
(Q/'sky-opening-reverse-coverage.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['rows','camera']},indent=2));print('ROWS',json.dumps(rows,indent=2))
