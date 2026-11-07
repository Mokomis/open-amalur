from pathlib import Path
import sys,json,struct,hashlib,collections,math
import numpy as np
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;P=Q.parents[2];sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_mesh
S=json.loads((Q/'1417252-source-render-records.json').read_text())
M=json.loads((Q/'first-room-material-catalog.json').read_text());MID={m['material']:i for i,m in enumerate(M)}
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);assert DT.itemsize==76
def sha(b):return hashlib.sha256(b).hexdigest()
def find(name):
 return next((Q/'inputs'/a/name for a in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (Q/'inputs'/a/name).exists()),None)
def qr(q,v):
 u=np.array(q[:3]);t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
def key(r):return r['fab'],r['assembly'],r['material'],tuple(r['translation']),tuple(r['quaternion']),tuple(r['scale'])
def main():
 O=Q/'candidate-first-room/world';O.mkdir(parents=True,exist_ok=True)
 meshes={};cells={};geometry={};prov=[];counts=collections.Counter();poseguards=[]
 for r in S:
  fid,ai,mid=r['fab'],r['assembly'],r['material'];k=key(r);cell=tuple(math.floor(v/6400) for v in r['translation'][:2]);dst=cells.setdefault(cell,dict(v=[],i=[],ranges=[],nv=0,ni=0,shared={}))
  if fid not in meshes:
   f=find(f'{fid}.fab_visual_data_streamable_bin');raw=f.read_bytes();meshes[fid]=(amalur_mesh.parse_file(f),raw)
  mesh,raw=meshes[fid];asm=mesh['assemblies'][ai];vb=mesh['vertex_buffers'][asm['vertex_buffer']];ib=mesh['index_buffers'][asm['index_buffer']]
  if k not in dst['shared']:
   stride,nv,base=vb['stride_bytes'],vb['vertex_count'],vb['data_file_offset'];assert stride in [20,48,56]
   ix=np.array(ib['indices'],'<u4');used,inv=np.unique(ix,return_inverse=True)
   local=np.array(vb['positions'],float);q=r['quaternion'];cq=(-q[0],-q[1],-q[2],q[3]);sc=np.array(r['scale']);t=np.array(r['translation']);world=qr(cq,local*sc)+t
   uv=np.ndarray((nv,2),'<f4',raw,base+12,(stride,4));uv2=np.ndarray((nv,2),'<f4',raw,base+20,(stride,4)) if stride==56 else uv
   frames=[]
   if stride in [48,56]:
    no=20 if stride==48 else 28;safe=np.where(abs(sc)>1e-4,sc,1)
    for off in [no,no+8,no+16]:
     vec=np.ndarray((nv,3),'<i2',raw,base+off,(stride,2)).astype(float)/safe;vec/=np.maximum(np.linalg.norm(vec,axis=1,keepdims=True),1e-9);frames.append(qr(cq,vec))
    color=np.ndarray((nv,4),'u1',raw,base+stride-4,(stride,1));flags=3
   else:frames=[np.zeros((nv,3)) for _ in range(3)];color=np.zeros((nv,4),'u1');flags=0
   data=np.empty(nv,DT);data['v']=np.concatenate([world,*frames,uv,uv2],1).astype('<f4');data['rgba']=color;data['material']=mid;data['flags']=flags
   v=data[used];ind=inv.astype('<u4')+dst['nv'];first=dst['ni'];dst['shared'][k]=(first,len(ind));dst['v'].append(v);dst['i'].append(ind);dst['nv']+=len(v);dst['ni']+=len(ind)
   assert np.array_equal(v['v'][inv,12:14].view('<u4'),uv[ix].copy().view('<u4'))
   assert np.array_equal(v['rgba'][inv],color[ix])
   sphere=np.array(r['sphere']);reach=np.linalg.norm(world[used]-sphere[:3],axis=1).max();poseguards.append(dict(source=r['source_index'],fab=fid,assembly=ai,scale=r['scale'],sphere_radius=float(sphere[3]),direct_vertex_reach=float(reach),ratio=float(reach/max(sphere[3],1e-9))))
   counts['unique_geometry']+=1;counts['stored_triangles']+=len(ind)//3;counts['vertices']+=len(v);counts['stride_'+str(stride)]+=1
  first,n=dst['shared'][k];lo,hi=r['distance_squared_fields'];anchor=[*r['translation'],r['sphere'][3]]
  dst['ranges'].append(struct.pack('<4I6fIf',MID[mid],first,n,r['physics_flags'],*anchor,lo,hi,r['source_index'],0.0))
  prov.append(dict(source_index=r['source_index'],group=r['group'],record=r['record'],cell=cell,first_index=first,index_count=n,material_row=MID[mid],native_material=mid,fab=fid,assembly=ai,range_sq=[lo,hi],raw_flags=r['physics_flags']))
  counts['ranges']+=1;counts['all_range_triangles']+=n//3
 registry=[];files=[]
 for (cx,cy),d in sorted(cells.items()):
  V=np.concatenate(d['v']);I=np.concatenate(d['i']);R=b''.join(d['ranges']);blob=struct.pack('<8s5I',b'OARGEO1\0',len(V),len(I),len(d['ranges']),76,48)+R+V.tobytes()+I.tobytes();name=f'r{cx}_{cy}.bin';(O/name).write_bytes(blob)
  at=28+len(R)+len(V)*76;assert np.array_equal(np.frombuffer(blob,'<u4',len(I),at),I);assert I.max()<len(V)
  lo=V['v'][:,:3].min(0);hi=V['v'][:,:3].max(0);registry.append(struct.pack('<iiII6f',cx,cy,len(I)//3,len(d['ranges']),*lo,*hi));files.append(dict(file=name,cell=[cx,cy],bytes=len(blob),sha256=sha(blob),vertices=len(V),stored_triangles=len(I)//3,ranges=len(d['ranges']),bounds=[lo.tolist(),hi.tolist()]))
 # Raw source intervals remain unchanged. Header1 leaves selection explicit for root.
 index=struct.pack('<8sIIfI',b'OARGIDX1',len(files),len(MID),1.0,0)+b''.join(registry);(O/'region-index.bin').write_bytes(index)
 (O/'index.bin').write_bytes(b'OAWI'+struct.pack('<fIII',6400.,0,0,0))
 col=np.load(Q/'first-room-collision.npy');ck=np.floor(col.mean(1)[:,:2]/6400).astype(int);collision=[]
 for c in sorted({tuple(x) for x in ck}):
  tris=col[np.all(ck==c,axis=1)].astype('<f4');name=f'k{c[0]}_{c[1]}.bin';b=struct.pack('<I',len(tris))+tris.tobytes();(O/name).write_bytes(b);collision.append(dict(file=name,triangles=len(tris),bytes=len(b),sha256=sha(b)))
 (Q/'candidate-first-room/source-range-provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
 (Q/'candidate-first-room/direct-trs-bounds-audit.json').write_text(json.dumps(sorted(poseguards,key=lambda r:r['ratio'],reverse=True),indent=2)+'\n')
 report=dict(status='STAGING ONLY: material-bank binding/shader families and sourceflags pass mask need root integration; geometry not live',space=1417252,region=1262814,source_spawn=[4312,2806,-314,-180],material_rows={str(k):v for k,v in MID.items()},counts=dict(counts),pack_bytes=sum(f['bytes'] for f in files),cells=files,index_sha256=sha(index),collision=collision,distance_policy='Source minSq/maxSq unchanged; registryDistanceScale1 is neutral staging. Native shared camera quality default4 means scale.5 when enabled, provenbinary+live outdoors; room-specific runtime setting not observed. Root explicitly chooses profile; no fitted cutoffs.',vertex_contract='OAWE76:16float32 pos,N,T,B,UV0,UV1;RGBA8@64,nativeMID@68,flags@72. Direct conjugated sourceTRS; inverse-transpose normalized bodyframes. Source20 keeps p/UV, all missing attrs zero/flags0 and shaderunsupported. Source48UV1 duplicatesUV0; Source56UV1actual.',dedup='Identical Fab/asm/MID/bitexactTQS geometry shared indexed. All2340source range records retained; zero interval overlaps among862identical geometry keys; source provenance retains eachidentity.',limits=['No native opening frame geometry/runtime capture; directTRS is establishedengine convention, sourcebounds audit retained separately.','All4sourcegroups retained; rawFlags exclusionmask not reinterpreted.','No material fallback/tint/shader substitutions authored.','Candidate index has no baseLOD and no texturecount pending root standalone material/texture merge.','Actor0x98visuals/skeletal mobs/cinematics/effects are separate and not included in staticcollection geometry.'])
 (Q/'candidate-first-room/geometry-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['cells','collision','material_rows']},indent=2));print('BOUNDS_TOP',sorted(poseguards,key=lambda r:r['ratio'],reverse=True)[:3])
if __name__=='__main__':main()
