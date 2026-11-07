"""Recover exact SPACE range ownership before emitting optional per-source leaf ranges."""
from pathlib import Path
import json,struct,collections,hashlib,sys
import numpy as np
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent;A=P/'work/v45-foliage-coverage';W=P/'work/v40-windows-host/assets/world'
source=json.loads((A/'expanded-leaf-attributes/source-provenance.json').read_text());assert len(source)==590
def sha(b):return hashlib.sha256(b).hexdigest()
def qr(q,v):
 u=np.array(q[:3]);x=2*np.cross(u,v);return v+q[3]*x+np.cross(u,x)
def find(name):return next((P/'work/v20-inputs'/pack/name for pack in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (P/'work/v20-inputs'/pack/name).exists()),None)
lookup={};files=[]
for sid in sorted({s['space'] for s in source}):
 path=find(str(sid)+'.space_bxml');raw=path.read_bytes();b=raw[8:8+struct.unpack_from('<I',raw)[0]];lut=collections.defaultdict(list)
 for group,(refs,bounds,renders) in enumerate([(0x128,0x148,0x150),(0x130,0x158,0x160),(0x138,0x168,0x170),(0x140,0x178,0x180)]):
  rp,n=struct.unpack_from('<2I',b,renders);bp,bn=struct.unpack_from('<2I',b,bounds);fp,fn=struct.unpack_from('<2I',b,refs);assert n==bn==fn
  for i in range(n):
   rr=raw[rp+84*i:rp+84*(i+1)];ph=raw[bp+80*i:bp+80*(i+1)];ref=raw[fp+16*i:fp+16*(i+1)];fab=struct.unpack_from('<I',ref,8)[0];lo,hi,flags,rank=struct.unpack_from('<2f2I',ph,64)
   lut[(fab,rr.hex())].append(dict(group=group,record=i,range_squared=[lo,hi],flags=flags,rank=rank,source_bounds_file_offset=bp+80*i,source_render_file_offset=rp+84*i,source_ref_file_offset=fp+16*i,source_bounds_hex=ph.hex(),source_ref_hex=ref.hex()))
 lookup[sid]=lut;files.append(dict(source=str(path.relative_to(P)),sha256=sha(raw)))
rows=[]
for i,s in enumerate(source):
 records=lookup[s['space']].get((s['fab'],s['render_record_hex']),[]);intervals=sorted({tuple(r['range_squared']) for r in records});merged=[]
 for lo,hi in intervals:
  assert np.isfinite(lo) and np.isfinite(hi) and 0<=lo<=hi,(i,lo,hi)
  if merged and lo<=merged[-1][1]:merged[-1][1]=max(hi,merged[-1][1])
  else:merged.append([lo,hi])
 rr=bytes.fromhex(s['render_record_hex']);t=struct.unpack_from('<3f',rr,16);q=struct.unpack_from('<4f',rr,32);sc=struct.unpack_from('<3f',rr,48);cq=(-q[0],-q[1],-q[2],q[3]);basis=qr(cq,np.eye(3)*np.array(sc)[:,None])
 row=dict(source_instance=i,space=s['space'],fab=s['fab'],assembly=s['assembly'],native_material=s['material'],triangles=s['triangles'],raw_translation=list(t),quaternion=list(q),scale=list(sc),basis=basis.tolist(),render_record_hex=s['render_record_hex'],source_records=records,source_flag_variants=sorted({r['flags'] for r in records}),merged_intervals_squared=merged,unknown_range=not records,disjoint_intervals=len(merged)>1)
 rows.append(row)
meta=json.loads((P/'work/v44-native-fidelity/bridge-native-final-r2.json').read_text());eye=np.array(meta['eye']);native=json.loads((A/'instance-audit/native-tree-source-correspondence.json').read_text());valid={r['draw'] for r in json.loads((A/'instance-audit/raw-render-translation-vs-native-audit.json').read_text())['rows'] if r['same_fab_basis_raw_translation_matched']};checks=[]
for d in native:
 if d['vs']!=877 or d['draw'] not in valid:continue
 m=np.array(d['native_world_matrix']).reshape(4,4);fabs={c['fab'] for c in d['source_assembly_candidates']};matches=[]
 for r in rows:
  if r['fab'] not in fabs or np.max(np.abs(np.array(r['raw_translation'])-m[3,:3]))>=.01 or np.max(np.abs(np.array(r['basis'])-m[:3,:3]))>=.001:continue
  dist2=float(np.sum((eye-r['raw_translation'])**2));active=r['unknown_range'] or any(lo<=dist2<hi for lo,hi in r['merged_intervals_squared']);matches.append(dict(source_instance=r['source_instance'],assembly=r['assembly'],distance_cm=dist2**.5,intervals_squared=r['merged_intervals_squared'],active=active))
 checks.append(dict(native_draw=d['draw'],native_assembly_candidates=d['source_assembly_candidates'],source_matches=matches,any_selected_part_active=any(x['active'] for x in matches),all_selected_parts_active=bool(matches) and all(x['active'] for x in matches)))
assert len(checks)==33
blocked=[x for x in checks if not x['any_selected_part_active']];report=dict(status='metadata recovered; geometry emission withheld pending native activity gate',source_instances=len(rows),source_triangles=sum(r['triangles'] for r in rows),unknown_sources=sum(r['unknown_range'] for r in rows),disjoint_sources=sum(r['disjoint_intervals'] for r in rows),matched_source_files=files,native_space_leaf_checks=checks,captured_draws_checked=len(checks),captured_draws_inactive=len(blocked),rows=rows,distance_policy='Raw sourceT, distanceScale1; exact selectedassembly interval union across4SPACEcollections. Adjacent blend bands merged without duplicate draws.',limits=['No farbillboard added. Selectedassembly may be a cached farLOD while native draws equivalentnear assembly; activity gate prevents accidental removal.','Unknown range fallback may be unbounded with explicit report. Source flags retained as variants, not guessed semantic categories.'])
(Q/'authored-range-metadata.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['rows','matched_source_files','native_space_leaf_checks']},indent=2));print('BLOCKERS',json.dumps(blocked,indent=2))
