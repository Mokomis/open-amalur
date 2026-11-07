from pathlib import Path
import sys,json,struct,collections
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;sys.path.insert(0,str(Q));import content_sources as C
P=C.ROOT
sys.path[:0]=[str(P/'work/v07-mesh'),str(P/'work/v19-lighting'),str(P/'work/v20-char')]
import amalur_mesh,decode_scene_lighting as D,native_instances as N

def read_collection(path):
 raw,b=C.graph(path);rows=[]
 for g,(refs,ph,render) in enumerate([(0x128,0x148,0x150),(0x130,0x158,0x160),(0x138,0x168,0x170),(0x140,0x178,0x180)]):
  aa,bb,cc=C.arr(raw,b,refs,16),C.arr(raw,b,ph,80),C.arr(raw,b,render,84);assert len(aa)==len(bb)==len(cc)
  for i,(a,h,r) in enumerate(zip(aa,bb,cc)):
   fab=struct.unpack_from('<I',a,8)[0];mid,asm=struct.unpack_from('<II',r,64)
   rows.append(dict(source_index=len(rows),group=g,record=i,fab=fab,name=C.SYMS['fab'].get(str(fab)),material=mid,material_name=C.SYMS['material'].get(str(mid)),assembly=asm,translation=struct.unpack_from('<3f',r,16),quaternion=struct.unpack_from('<4f',r,32),scale=struct.unpack_from('<3f',r,48),sphere=struct.unpack_from('<4f',r),distance_squared_fields=struct.unpack_from('<2f',h,64),physics_flags=struct.unpack_from('<I',h,72)[0],physics_collection_ordinal=struct.unpack_from('<I',h,76)[0],reference_record_hex=a.hex(),physics_record_hex=h.hex(),render_record_hex=r.hex(),ref_slot=refs,bounds_slot=ph,render_slot=render))
 return rows

def run():
 inv=json.loads((Q/'room-inventory.json').read_text());summary=[]
 for room in inv:
  sid=room['space'];f=Q/f'inputs/patch_0.pak/{sid}.space_bxml';raw,b=C.graph(f);rows=read_collection(f)
  (Q/f'{sid}-source-render-records.json').write_text(json.dumps(rows,indent=2)+'\n')
  actors=N.parse_space(raw);(Q/f'{sid}-native-placements.json').write_text(json.dumps(actors,indent=2)+'\n')
  lights=D.decode_space_lights(raw);(Q/f'{sid}-lighting.json').write_text(json.dumps(lights,indent=2)+'\n')
  summary.append(dict(space=sid,region=room['region'],rows=len(rows),fabs=len({r['fab'] for r in rows}),materials=len({r['material'] for r in rows}),actors=actors['count'],lights=len(lights['lights'])))
 for rid in [549773,1262814]:
  f=Q/f'inputs/patch_0.pak/{rid}.region_bxml'
  if not f.exists():f=next((Q/'inputs').glob(f'*/{rid}.region_bxml'))
  raw,b=C.graph(f);dec=D.decode_region(raw);(Q/f'{rid}-lighting.json').write_text(json.dumps(dec,indent=2)+'\n')
  edges=[]
  for i,r in enumerate(C.arr(raw,b,0xc0,164)):
   a,z=struct.unpack_from('<2I',r,156);edges.append(dict(index=i,from_space=a,to_space=z,from_name=C.SYMS['simspace'].get(str(a)),to_name=C.SYMS['simspace'].get(str(z)),raw_hex=r.hex()))
  (Q/f'{rid}-portal-graph.json').write_text(json.dumps(dict(region=rid,source=str(f.relative_to(P)),edges=edges),indent=2)+'\n')
 (Q/'content-catalog.json').write_text(json.dumps(summary,indent=2)+'\n');print('ROOMS',summary)
 rows=json.loads((Q/'1417252-source-render-records.json').read_text());fabs=sorted({r['fab'] for r in rows});mids=sorted({r['material'] for r in rows})
 fs=C.extract([f'{i}.fab_visual_data_streamable_bin' for i in fabs]+[f'{i}.fab_bxml' for i in fabs]+[f'{i}.mat_bxml' for i in mids]);meshes=[]
 for fab in fabs:
  key=f'{fab}.fab_visual_data_streamable_bin'
  if key not in fs:meshes.append(dict(fab=fab,error='no archive stream'));continue
  try:
   m=amalur_mesh.parse_file(fs[key]);rr=[r for r in rows if r['fab']==fab];tri=sum(m['index_buffers'][m['assemblies'][r['assembly']]['index_buffer']]['index_count']//3 for r in rr)
   meshes.append(dict(fab=fab,name=C.SYMS['fab'][str(fab)],source=str(fs[key].relative_to(P)),source_sha256=m['input_sha256'],bytes=fs[key].stat().st_size,assemblies=len(m['assemblies']),strides=sorted({v['stride_bytes'] for v in m['vertex_buffers']}),render_rows=len(rr),all_range_triangles=tri))
  except Exception as e:meshes.append(dict(fab=fab,error=str(e)))
 mats=[]
 for mid in mids:
  f=fs.get(f'{mid}.mat_bxml')
  if not f:mats.append(dict(material=mid,error='no source'));continue
  raw=f.read_bytes();sh,alpha,cull,cut=struct.unpack_from('<4I',raw,24);refs=[]
  for off in range(0,len(raw)-3,4):
   t=struct.unpack_from('<I',raw,off)[0]
   if str(t) in C.SYMS['texture'] and t not in [x['asset'] for x in refs]:refs.append(dict(asset=t,name=C.SYMS['texture'][str(t)],file_offset=off))
  mats.append(dict(material=mid,name=C.SYMS['material'][str(mid)],source=str(f.relative_to(P)),source_sha256=C.hashlib.sha256(raw).hexdigest(),shader=sh,shader_name=C.SYMS['shader'].get(str(sh)),alpha_test=alpha,cull=cull,cutoff_byte=cut,texture_references=refs,raw_hex=raw.hex()))
 (Q/'first-room-mesh-catalog.json').write_text(json.dumps(meshes,indent=2)+'\n');(Q/'first-room-material-catalog.json').write_text(json.dumps(mats,indent=2)+'\n')
 print('MESHES',len(meshes),'ERRORS',[x for x in meshes if 'error' in x],'TRIS',sum(x.get('all_range_triangles',0) for x in meshes),'STRIDES',collections.Counter(str(x.get('strides')) for x in meshes));print('MATERIALS',len(mats),collections.Counter(x.get('shader_name','ERROR') for x in mats))
if __name__=='__main__':run()
