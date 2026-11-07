"""Read-only geometric guard; writes report only inside this staging directory."""
from pathlib import Path
import json,struct,sys,collections
import numpy as np
sys.dont_write_bytecode=True
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_mesh
source=json.loads((P/'work/v45-foliage-coverage/expanded-leaf-attributes/source-provenance.json').read_text())
native=json.loads((P/'work/v45-foliage-coverage/instance-audit/native-tree-source-correspondence.json').read_text())
audit=json.loads((P/'work/v45-foliage-coverage/instance-audit/raw-render-translation-vs-native-audit.json').read_text())
valid={r['draw'] for r in audit['rows'] if r['same_fab_basis_raw_translation_matched']}
assert len(valid)==92
def qr(q,v):
 u=np.array(q[:3]);t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
cache={};rows=[]
for i,s in enumerate(source):
 r=bytes.fromhex(s['render_record_hex']);sphere=np.array(struct.unpack_from('<4f',r));t=np.array(struct.unpack_from('<3f',r,16));q=struct.unpack_from('<4f',r,32);sc=np.array(struct.unpack_from('<3f',r,48));cq=(-q[0],-q[1],-q[2],q[3])
 path=P/s['mesh_path']
 if path not in cache:cache[path]=amalur_mesh.parse_file(path)
 mesh=cache[path];a=mesh['assemblies'][s['assembly']];vb=mesh['vertex_buffers'][a['vertex_buffer']];xyz=np.array(vb['positions'],float);ix=np.unique(mesh['index_buffers'][a['index_buffer']]['indices']);xyz=xyz[ix]
 cl=qr(q,(sphere[:3]-t)[None,:])[0];old=qr(cq,cl+(xyz-cl)*sc)+t;direct=qr(cq,xyz*sc)+t;basis=qr(cq,np.eye(3)*sc[:,None]);offset=qr(cq,(cl*(sc-1))[None,:])[0]
 witnesses=[]
 for d in native:
  if d['draw'] not in valid:continue
  fabs={c['fab'] for c in d['source_assembly_candidates']}
  if s['fab'] not in fabs:continue
  m=np.array(d['native_world_matrix']).reshape(4,4)
  te=float(np.max(np.abs(t-m[3,:3])));be=float(np.max(np.abs(basis-m[:3,:3])))
  if te<.01 and be<.001:witnesses.append(dict(draw=d['draw'],vs=d['vs'],translation_component_error_cm=te,basis_max_error=be,geometry_same_assembly=any(c['fab']==s['fab'] and c['assembly']==s['assembly'] for c in d['source_assembly_candidates'])))
 def extent(v):
  dist=np.linalg.norm(v-sphere[:3],axis=1)
  return dict(max_center_distance_cm=float(dist.max()),radius_ratio=float(dist.max()/sphere[3]) if sphere[3]>0 else None,outside_sphere_vertices=int((dist>sphere[3]+.01).sum()),outside_original_guard_vertices=int((dist>sphere[3]*1.25+60).sum()),bounds=[v.min(0).tolist(),v.max(0).tolist()])
 rows.append(dict(source_instance=i,space=s['space'],fab=s['fab'],assembly=s['assembly'],native_material=s['material'],triangles=s['triangles'],raw_translation=t.tolist(),scale=sc.tolist(),source_sphere=sphere.tolist(),shift_cm=offset.tolist(),shift_length_cm=float(np.linalg.norm(offset)),old=extent(old),direct=extent(direct),native_matrix_witnesses=witnesses))
changed=[r for r in rows if r['shift_length_cm']>1e-6];proven=[r for r in changed if r['native_matrix_witnesses']];unproven=[r for r in changed if not r['native_matrix_witnesses']]
def summary(group):return dict(instances=len(group),triangles=sum(r['triangles'] for r in group),max_shift_cm=max((r['shift_length_cm'] for r in group),default=0),source_indices=[r['source_instance'] for r in group],unique_witness_draws=sorted({d['draw'] for r in group for d in r['native_matrix_witnesses']}))
report=dict(scope='All590source records use full referenced assembly vertices; sphere interpreted only as sourcefloat4 candidate bounds, semantics not independently proven.',native_match_guard='Restricted92previouslysource-matcheddraws; sameFAB/provengeometryalias plusrawTerror<.01cm andbasiserror<.001.',total_instances=len(rows),changed=summary(changed),individually_native_matrix_proven_changes=summary(proven),unobserved_changes=summary(unproven),old_sphere_outlier_instances=sum(r['old']['outside_sphere_vertices']>0 for r in rows),direct_sphere_outlier_instances=sum(r['direct']['outside_sphere_vertices']>0 for r in rows),old_original_guard_outlier_instances=sum(r['old']['outside_original_guard_vertices']>0 for r in rows),direct_original_guard_outlier_instances=sum(r['direct']['outside_original_guard_vertices']>0 for r in rows),top5_direct_radius_ratio=sorted(rows,key=lambda r:r['direct']['radius_ratio'] or 0,reverse=True)[:5],top5_shift=sorted(changed,key=lambda r:r['shift_length_cm'],reverse=True)[:5],rows=rows,recommendation='Preservefullcandidate. Restrictinitialpromotiontoindividuallynative-matrix-proven changedrecords until nonwitness source-sphere exceptions understood; no runtime coverage claim for unobservedrecords.')
(Q/'transform-bounds-guard.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['rows','top5_direct_radius_ratio','top5_shift']},indent=2));print('TOP5',[(r['source_instance'],r['fab'],r['shift_length_cm'],r['old']['radius_ratio'],r['direct']['radius_ratio'],[w['draw'] for w in r['native_matrix_witnesses']]) for r in report['top5_direct_radius_ratio']])
