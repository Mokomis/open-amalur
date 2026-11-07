"""Source-only classifier and all-authored-pose inventory for one proxy FAB."""
from pathlib import Path
import json,struct,collections,hashlib,sys
import numpy as np
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent;A=P/'work/v45-foliage-coverage/instance-audit';S=json.loads((P/'work/v20-inputs/symbols.json').read_text());models=json.loads((A/'authored-fab-groups.json').read_text());shadowmids={int(mid) for mid,name in S['material'].items() if 'shadowlod' in name.lower()};FAB=343974
def sha(b):return hashlib.sha256(b).hexdigest()
def find(name):return next((P/'work/v20-inputs'/pack/name for pack in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (P/'work/v20-inputs'/pack/name).exists()),None)
classes=[]
for m in models:
 proxy=[e for e in m['elements'] if e['native_material_id'] in shadowmids];groups=[dict(group=g['group'],elements=g['element_indices'],proxy_elements=[e['element'] for e in proxy if e['element'] in g['element_indices']],threshold=g['threshold'],flag=g['flag']) for g in m['groups'] if any(e['element'] in g['element_indices'] for e in proxy)]
 classes.append(dict(fab=m['fab'],name=S['fab'].get(str(m['fab'])),source=m['source'],source_sha256=m['sha256'],proxy_elements=proxy,groups_containing_proxy=groups,proxy_in_scene_groups_1_to_4=any(1<=g['group']<=4 for g in groups)))
target=next(c for c in classes if c['fab']==FAB);proxyassemblies={e['element'] for e in target['proxy_elements']};assert proxyassemblies=={9}
sources=[];allrows=[]
for sid,name in S['simspace'].items():
 if not name.startswith('out_dal_'):continue
 path=find(sid+'.space_bxml')
 if path:sources.append(('SPACE',int(sid),name,path,[(0x128,0x148,0x150),(0x130,0x158,0x160),(0x138,0x168,0x170),(0x140,0x178,0x180)]))
path=find('431608.region_bxml');sources.append(('REGION',431608,'reg_dalentarth',path,[(0x140,0x160,0x168),(0x148,0x170,0x178),(0x150,0x180,0x188),(0x158,0x190,0x198)]))
fileproof=[]
for kind,sid,name,path,slots in sources:
 raw=path.read_bytes();b=raw[8:8+struct.unpack_from('<I',raw)[0]];count=0
 for group,(rs,bs,vs) in enumerate(slots):
  rp,n=struct.unpack_from('<2I',b,rs);bp,bn=struct.unpack_from('<2I',b,bs);vp,vn=struct.unpack_from('<2I',b,vs);assert n==bn==vn
  for i in range(n):
   ref=raw[rp+16*i:rp+16*(i+1)]
   if struct.unpack_from('<I',ref,8)[0]!=FAB:continue
   rr=raw[vp+84*i:vp+84*(i+1)];mid,assembly=struct.unpack_from('<2I',rr,64)
   if mid not in shadowmids or assembly not in proxyassemblies:continue
   ph=raw[bp+80*i:bp+80*(i+1)];lo,hi,flags,rank=struct.unpack_from('<2f2I',ph,64);t=struct.unpack_from('<3f',rr,16);q=struct.unpack_from('<4f',rr,32);scale=struct.unpack_from('<3f',rr,48)
   allrows.append(dict(producer=kind,source_id=sid,source_name=name,source_path=str(path.relative_to(P)),source_sha256=sha(raw),group=group,record=i,reference_file_offset=rp+16*i,bounds_file_offset=bp+80*i,render_file_offset=vp+84*i,fab=FAB,assembly=assembly,native_material=mid,translation=list(t),quaternion=list(q),scale=list(scale),sphere=list(struct.unpack_from('<4f',rr)),interval_squared=[lo,hi],raw_flags=flags,rank=rank,reference_hex=ref.hex(),bounds_hex=ph.hex(),render_hex=rr.hex()));count+=1
 if count:fileproof.append(dict(producer=kind,id=sid,source=str(path.relative_to(P)),sha256=sha(raw),records=count))
groups=collections.defaultdict(list)
for r in allrows:
 rr=bytes.fromhex(r['render_hex']);key=(r['fab'],r['assembly'],r['native_material'],rr[16:28]+rr[32:60]);groups[key].append(r)
poses=[]
for index,(key,rows) in enumerate(sorted(groups.items(),key=lambda z:z[0])):
 intervals=[]
 for lo,hi in sorted({tuple(r['interval_squared']) for r in rows}):
  if intervals and lo<=intervals[-1][1]:intervals[-1][1]=max(hi,intervals[-1][1])
  else:intervals.append([lo,hi])
 r=rows[0];poses.append(dict(source_index=index,fab=r['fab'],assembly=r['assembly'],native_material=r['native_material'],translation=r['translation'],quaternion=r['quaternion'],scale=r['scale'],merged_intervals_squared=intervals,flag_variants=sorted({r['raw_flags'] for r in rows}),source_producers=sorted({r['producer'] for r in rows}),source_records=rows))
out=dict(status='Source-only inventory, no geometry emission yet',fab=FAB,shadow_material_ids=sorted(shadowmids),known_fab_classifier=classes,selected_fab_classifier=target,source_files_scanned=len(sources),matched_source_files=fileproof,raw_proxy_records=len(allrows),unique_pose_records=len(poses),producer_pose_counts=dict(collections.Counter(tuple(r['source_producers']) for r in poses)),cross_SPACE_REGION_overlap_poses=sum(len(r['source_producers'])>1 for r in poses),flag_counts=dict(collections.Counter(r['raw_flags'] for r in allrows)),triangle_estimate=len(poses)*14,indexed_vertex_estimate=len(poses)*28,geometry_payload_estimate=len(poses)*(28*76+42*4+48),poses=poses,limits=['Only source-authored MID named shadowlod and explicit source assembly selected; never chooses sceneleafgeometry by capturewhitelist.','Source proxy collector range overrides differ from FABelement default; both retained.','Distance policy/materialrow/wind contract await renderer/material review before emission.'])
# Tuplekeys are labels only; convert before JSON serialization.
out['producer_pose_counts']={'/'.join(k):v for k,v in out['producer_pose_counts'].items()}
(Q/'inventory.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['known_fab_classifier','selected_fab_classifier','poses','matched_source_files']},indent=2))
