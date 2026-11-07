"""Bounded exact-mesh-alias and source-center activity checks; report only."""
from pathlib import Path
import json,struct,hashlib,collections,sys
import numpy as np
sys.dont_write_bytecode=True
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent;A=P/'work/v45-foliage-coverage';sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_mesh
report=json.loads((Q/'authored-range-metadata.json').read_text());rows=report['rows'];source=json.loads((A/'expanded-leaf-attributes/source-provenance.json').read_text());eye=np.array(json.loads((P/'work/v44-native-fidelity/bridge-native-final-r2.json').read_text())['eye'])
def hash(b):return hashlib.sha256(b).hexdigest()
def union(intervals):
 out=[]
 for lo,hi in sorted(set(tuple(z) for z in intervals)):
  if out and lo<=out[-1][1]:out[-1][1]=max(hi,out[-1][1])
  else:out.append([lo,hi])
 return out
meshes={};records={}
for s in source:
 f=P/s['mesh_path']
 if s['fab'] not in meshes:
  m=amalur_mesh.parse_file(f);b=f.read_bytes();keys=[]
  for asm in m['assemblies']:
   vb=m['vertex_buffers'][asm['vertex_buffer']];ib=m['index_buffers'][asm['index_buffer']];at=vb['data_file_offset'];vbhash=hash(b[at:at+vb['vertex_count']*vb['stride_bytes']]);ibhash=hash(np.asarray(ib['indices'],'<u2').tobytes());keys.append((vbhash,ibhash))
  meshes[s['fab']]=keys
for sf in report['matched_source_files']:
 path=P/sf['source'];raw=path.read_bytes();b=raw[8:8+struct.unpack_from('<I',raw)[0]];sid=int(path.stem.split('.')[0]);lookup=collections.defaultdict(list)
 for group,(refs,bounds,renders) in enumerate([(0x128,0x148,0x150),(0x130,0x158,0x160),(0x138,0x168,0x170),(0x140,0x178,0x180)]):
  rp,n=struct.unpack_from('<2I',b,renders);bp,_=struct.unpack_from('<2I',b,bounds);fp,_=struct.unpack_from('<2I',b,refs)
  for j in range(n):
   rr=raw[rp+84*j:rp+84*(j+1)];ref=raw[fp+16*j:fp+16*(j+1)];fab=struct.unpack_from('<I',ref,8)[0];mid,ai=struct.unpack_from('<2I',rr,64);ph=raw[bp+80*j:bp+80*(j+1)]
   if fab not in meshes or ai>=len(meshes[fab]):continue
   key=(fab,rr[16:28]+rr[32:60],mid);lookup[key].append(dict(group=group,record=j,assembly=ai,geometry_hashes=meshes[fab][ai],interval_squared=list(struct.unpack_from('<2f',ph,64)),flags=struct.unpack_from('<I',ph,72)[0],bound_sphere=list(struct.unpack_from('<4f',rr)),reference_file_offset=fp+16*j,bounds_file_offset=bp+80*j,render_file_offset=rp+84*j))
 records[sid]=lookup
for r,s in zip(rows,source):
 rr=bytes.fromhex(s['render_record_hex']);key=(s['fab'],rr[16:28]+rr[32:60],s['material']);geom=meshes[s['fab']][s['assembly']];aliases=[x for x in records[s['space']][key] if tuple(x['geometry_hashes'])==geom];intervals=union([x['interval_squared'] for x in aliases]);sphere=np.array(struct.unpack_from('<4f',rr));td=float(np.linalg.norm(eye-r['raw_translation']));cd=float(np.linalg.norm(eye-sphere[:3]));r.update(exact_geometry_alias_assemblies=sorted({x['assembly'] for x in aliases}),exact_geometry_alias_records=aliases,exact_geometry_alias_intervals_squared=intervals,bound_sphere=sphere.tolist(),distance_T_cm=td,distance_C_cm=cd,selected_T_active=any(lo<=td*td<hi for lo,hi in r['merged_intervals_squared']),selected_C_active=any(lo<=cd*cd<hi for lo,hi in r['merged_intervals_squared']),alias_T_active=any(lo<=td*td<hi for lo,hi in intervals),alias_C_active=any(lo<=cd*cd<hi for lo,hi in intervals))
checks=[]
for c in report['native_space_leaf_checks']:
 matches=[rows[m['source_instance']] for m in c['source_matches']];checks.append(dict(draw=c['native_draw'],source_indices=[r['source_instance'] for r in matches],any_selected_T_active=any(r['selected_T_active'] for r in matches),any_selected_C_active=any(r['selected_C_active'] for r in matches),any_alias_T_active=any(r['alias_T_active'] for r in matches),any_alias_C_active=any(r['alias_C_active'] for r in matches),matches=[{k:r[k] for k in ['source_instance','fab','assembly','distance_T_cm','distance_C_cm','bound_sphere','merged_intervals_squared','exact_geometry_alias_assemblies','exact_geometry_alias_intervals_squared','selected_T_active','selected_C_active','alias_T_active','alias_C_active']} for r in matches]))
summary={k:sum(c[k] for c in checks) for k in ['any_selected_T_active','any_selected_C_active','any_alias_T_active','any_alias_C_active']};offender=rows[198];result=dict(status='Evidence-only; no geometry writes',native_positive_count=33,positive_counts=summary,offender198={k:offender[k] for k in ['source_instance','fab','assembly','space','distance_T_cm','distance_C_cm','bound_sphere','merged_intervals_squared','exact_geometry_alias_assemblies','exact_geometry_alias_intervals_squared','selected_T_active','selected_C_active','alias_T_active','alias_C_active']},checks=checks,source_rows=rows,alias_rule='SameSPACE/rawTQS,FAB,nativeMID (thus same source shader), EXACTfullVBbytes+fullIBbyteshash; novalue/visual/permutation guesses.',limits=['Native distance consumer/bounding-radius contribution not recovered; no fittedfactor or forcedexceptions.','Currentselectedassembly geometry maydiffer slightly fromnear sourcealias; exacthashrule deliberatelykeeps those separate.'])
(Q/'alias-bound-center-check.json').write_text(json.dumps(result,indent=2));print('SUMMARY',summary);print('OFFENDER',result['offender198']);print('STILLINACTIVE',[(c['draw'],c['matches']) for c in checks if not c['any_alias_C_active']])
