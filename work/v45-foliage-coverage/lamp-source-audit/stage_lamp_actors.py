"""Private authored lamp actor geometry with source LODs. Never deploys."""
from pathlib import Path
import json,struct,sys,hashlib,math,collections
import numpy as np
sys.dont_write_bytecode=True
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent;ST=O/'stage';ST.mkdir(exist_ok=True);W=ST/'lamp-world';W.mkdir(exist_ok=True)
sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_mesh
src=P/'work/v20-inputs/DATA_0.pak/540961.fab_visual_data_streamable_bin';raw=src.read_bytes();m=amalur_mesh.parse_file(src);f=json.loads((O/'lamp-authored-groups.json').read_text());actors=json.loads((O/'actor-lamp-id-hits.json').read_text());visible=set(map(tuple,json.loads((P/'work/v45-foliage-coverage/visible-cells.json').read_text())));base=(P/'work/v40-windows-host/assets/world/index.bin').read_bytes();cs,ncells=struct.unpack_from('<fI',base,4);assert cs==6400;cells={struct.unpack_from('<ii',base,20+i*48) for i in range(ncells)};assert ncells==1271
sha=lambda b:hashlib.sha256(b).hexdigest();dt=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('native_mid','<u4'),('flags','<u4')]);assert dt.itemsize==76
mapping={489075:11,489077:14,374967:43,489073:12,654012:298};groups=[g for g in f['groups'][1:5] if g['element_indices']];assert [g['element_indices'] for g in groups]==[[0,1,2,3,4],[5,6,7,8],[9,10,11,12]]
def qr(q,v):
 u=np.array(q[:3]);z=2*np.cross(u,v);return v+q[3]*z+np.cross(u,z)
local=[]
for ai,a in enumerate(m['assemblies']):
 vb=m['vertex_buffers'][a['vertex_buffer']];ib=m['index_buffers'][a['index_buffer']];n=vb['vertex_count'];at=vb['data_file_offset'];stride=vb['stride_bytes'];assert stride==48
 p=np.array(vb['positions']);frame=[np.maximum(np.ndarray((n,3),'<i2',raw,at+off,(stride,2)).astype(float)/32767.,-1) for off in [20,28,36]];uv=np.ndarray((n,2),'<f4',raw,at+12,(stride,4)).copy();color=np.ndarray((n,4),'u1',raw,at+44,(stride,1)).copy();ix=np.array(ib['indices'],'<u4');local.append((p,frame,uv,color,ix))
buckets=collections.defaultdict(list);provenance=[];rejected=[];cost=collections.Counter()
for source_ordinal,a in enumerate(actors):
 t=np.array(a['T']);q=np.array(a['quaternion']);cq=np.r_[-q[:3],q[3]];s=np.array(a['scale']);assert np.all(abs(s)>1e-6);parts=[];allp=[]
 for g in groups:
  for ai in g['element_indices']:
   e=f['elements'][ai];p,frame,uv,color,ix=local[ai];world=qr(cq,p*s)+t;worldframe=[]
   for n in frame:
    n=n/s;n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-20);worldframe.append(qr(cq,n))
   v=np.zeros(len(p),dt);v['v']=np.c_[world,*worldframe,uv,uv].astype('<f4');v['rgba']=color;v['native_mid']=e['native_material_id'];v['flags']=3;parts.append((v,ix,e,g));allp.append(world)
 allp=np.concatenate(allp);lo=allp.min(0);hi=allp.max(0);mins=np.floor(lo[:2]/cs).astype(int);maxs=np.floor(hi[:2]/cs).astype(int);intersect=any((x,y) in visible for x in range(mins[0],maxs[0]+1) for y in range(mins[1],maxs[1]+1));bucket=tuple(map(int,np.floor((lo[:2]+hi[:2])*.5/cs).astype(int)))
 if not intersect:rejected.append({'source_ordinal':source_ordinal,'space':a['space'],'index':a['index'],'origin_cell':a['cell'],'whole_bounds_cell':list(bucket),'bounds':[lo.tolist(),hi.tolist()]});continue
 assert bucket in cells,(a['space'],a['index'],bucket,'not in existing1271 cell registry');assert all(abs(z-1)<1e-6 for z in s),('visible actor nonunit scale needs distance policy review',s)
 sid=0x40000000+source_ordinal
 row={'source_index':sid,'source_ordinal':source_ordinal,'space':a['space'],'space_name':a['name'],'source':a['path'],'slot':a['slot'],'record_index':a['index'],'entity_id':a['entity_id'],'source_flags':a['flags'],'record_hex':a['record_hex'],'translation':a['T'],'quaternion':a['quaternion'],'scale':a['scale'],'origin_cell':a['cell'],'whole_bounds_centroid_cell':list(bucket),'whole_bounds':[lo.tolist(),hi.tolist()],'parts':[]}
 for v,ix,e,g in parts:
  radius=float(np.linalg.norm(v['v'][:,:3].astype(float)-t,axis=1).max());run={'material':mapping[e['native_material_id']],'native_material':e['native_material_id'],'assembly':e['element'],'group':g['group'],'sphere':[*a['T'],radius],'min_sq':e['distance_min']**2,'max_sq':e['distance_max']**2,'source_index':sid,'original_flags':a['flags'],'distance_scale':1.0,'triangles':len(ix)//3,'vertices':len(v)}
  buckets[bucket].append((v,ix,run));row['parts'].append(run);cost[g['group']]+=len(ix)//3
 provenance.append(row)
assert len(provenance)==14,(len(provenance),'visible count changed');files=[];indexrows=[]
for cell,parts in sorted(buckets.items()):
 verts=[];indices=[];runs=[];vo=0;io=0
 for v,ix,r in parts:
  verts.append(v);indices.append(ix+vo);runs.append(struct.pack('<4I6fIf',r['material'],io,len(ix),r['original_flags'],*r['sphere'],r['min_sq'],r['max_sq'],r['source_index'],r['distance_scale']));vo+=len(v);io+=len(ix)
 V=np.concatenate(verts);I=np.concatenate(indices).astype('<u4');assert int(I.max())<len(V);header=struct.pack('<8s5I',b'OARGEO1\0',len(V),len(I),len(runs),76,48);assert len(header)==28;data=header+b''.join(runs)+V.tobytes()+I.tobytes();name=f'r{cell[0]}_{cell[1]}.bin';(W/name).write_bytes(data);lo=V['v'][:,:3].min(0);hi=V['v'][:,:3].max(0);indexrows.append(struct.pack('<iiII6f',*cell,len(I)//3,len(runs),*lo,*hi));files.append({'file':name,'cell':list(cell),'vertices':len(V),'triangles_all_lods':len(I)//3,'ranges':len(runs),'bytes':len(data),'sha256':sha(data),'bounds':[lo.tolist(),hi.tolist()]})
idx=struct.pack('<8s2IfI',b'OARGIDX1',len(files),299,1.,0)+b''.join(indexrows);assert len(idx)==24+40*len(files);(ST/'lamp-index.bin').write_bytes(idx)
# Row-only profile/MATS candidates; parent merges alongside independently reserved296/297.
NONE=0xffffffff;profile=struct.pack('<I8I12f',8,693,694,695,696,NONE,NONE,NONE,NONE,1.,1.,1.,0.,1.,20.,1.,0.,1.,1.,0.,0.);assert len(profile)==84;(ST/'material-298.native84.bin').write_bytes(profile);mats=struct.pack('<7I',0x10000000,693,694,695,696,NONE,NONE);assert len(mats)==28;(ST/'material-298.mats28.bin').write_bytes(mats)
profilemeta={'material_row':298,'native_material':654012,'family':8,'color':[1,1,1,0],'specular':[1,20,1,0],'uv':[1,1,0,0],'uv_semantics':'xy unity; zw material U/V scroll speeds multiplied by gameTime; both0 here','native_t':[693,694,695,696,NONE,NONE,NONE,NONE],'roles':['diffuse','normal','specular','emissive-mask'],'mats_flags':0x10000000,'alpha_test':False,'cutoff':0,'cull':'BACK; source cull2, captured pipeline backs','padding_alpha_not_read':True,'source_material':str(O/'source/initial_0.pak/654012.mat_bxml'),'legacy_other_rows':mapping};(ST/'material-298.json').write_text(json.dumps(profilemeta,indent=2))
# Native bridge fixture includes only the authored far group3, as proven in capture.
a=next(a for a in provenance if a['space']==431646 and a['record_index']==17);fixture=[];fixi=[];draws=[];vo=0;io=0
for v,ix,r in buckets[tuple(a['whole_bounds_centroid_cell'])]:
 if r['source_index']!=a['source_index'] or r['group']!=3:continue
 fixture.append(v);fixi.append(ix+vo);draws.append((r['material'],io,len(ix)));vo+=len(v);io+=len(ix)
V=np.concatenate(fixture);I=np.concatenate(fixi).astype('<u4');b=b'OAWE'+struct.pack('<III',len(V),len(I),len(draws))+b''.join(struct.pack('<III',*r) for r in draws)+V.tobytes()+I.tobytes();(ST/'bridge-lamp-authored.oawe').write_bytes(b)
manifest={'fab':540961,'source_stream':str(src),'source_stream_sha256':sha(raw),'source_fab':f['source'],'source_fab_sha256':f['sha256'],'source_actors_total':len(actors),'visible_actors':len(provenance),'visible_cell_filter_count':len(visible),'base_registry_cells':ncells,'base_registry_unchanged':True,'source_index_namespace':'0x40000000 + stable source actor ordinal','groups':groups,'material_rows':mapping,'new_material_row':298,'cost_triangles_by_lod_group':dict(cost),'stored_vertices':sum(r['vertices'] for r in files),'stored_triangles_all_lods':sum(r['triangles_all_lods'] for r in files),'stored_runs':sum(r['ranges'] for r in files),'stored_geometry_bytes':sum(r['bytes'] for r in files),'files':files,'index':{'file':'lamp-index.bin','sha256':sha(idx),'bytes':len(idx),'material_count':299,'header_distance_scale':1.},'actors':provenance,'excluded_actors':rejected,'limits':['Private staging only; no active asset/core/index writes.','Only source-authored540961 actors intersecting requested203 visible cells; this is not the full actor family importer.','All three source LOD groups stored; per-range raw-distance scale1 prevents simultaneous LODs.','Raw actor origin metric matches two captured lamp actors, unlike region quality scale.5; generalized settings beyond these actor fixtures not independently observed.','Other four material rows reuse existing profiles with their existing shader limitations.','Only textureemissive654012 has the newly exact PS838 contract.','Source actors can have entity_id0; stable provenance key includes space/header/record index.','Waterfalls untouched.']};(O/'lamp-stage-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:manifest[k] for k in ['source_actors_total','visible_actors','cost_triangles_by_lod_group','stored_vertices','stored_triangles_all_lods','stored_runs','stored_geometry_bytes']},indent=2));print('cells',len(files),'index',len(idx),'bridgefixture',len(b))
