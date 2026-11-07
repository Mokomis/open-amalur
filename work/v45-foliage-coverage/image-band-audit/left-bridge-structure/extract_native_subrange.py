from pathlib import Path
import json,struct,ctypes,hashlib
Q=Path(__file__).resolve().parent;C=Q.parent.parent/'2026-11-05/open-amalur-native-camera';I=json.loads((C/'capture-index.json').read_text());contract=json.loads((Q/'native-draw-contract.json').read_text());buffers={8611,8613};images={8630,8625,8615,8620};fn=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int;found=[]
with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb')as f:
 _,_,_,n=struct.unpack('<4sIII',f.read(16));f.seek(n*8,1);i=-1
 while h:=f.read(12):
  size,k=struct.unpack('<QI',h);i+=1;off=f.tell();d=f.read(min(size,48));kind=struct.unpack_from('<I',d)[0]&65535 if len(d)>=4 else 0;obj=struct.unpack_from('<Q',d,20)[0]if len(d)>=28 else None
  if k&0x7fffffff==3 and((kind==7 and obj in buffers)or(kind==8 and obj in images)):
   d+=f.read(size-len(d));nb=struct.unpack_from('<Q',d,28)[0]
   if kind==7:head=36;levels=None
   else:nm=struct.unpack_from('<I',d,44)[0];levels=struct.unpack_from('<%dQ'%nm,d,48);head=48+8*nm
   raw=d[head:]
   if k&0x80000000:
    out=ctypes.create_string_buffer(nb);assert fn(raw,out,len(raw),nb)==nb;raw=out.raw
   assert len(raw)==nb;name=f'{"buffer"if kind==7 else"image"}-{obj}.bin';(Q/name).write_bytes(raw);found.append(dict(object=obj,kind=kind,file=name,block=i,file_offset=off,bytes=nb,sha256=hashlib.sha256(raw).hexdigest(),level_sizes=levels))
  else:f.seek(size-len(d),1)
vb=(Q/'buffer-8611.bin').read_bytes();ib=(Q/'buffer-8613.bin').read_bytes();args=contract['draw']['args'];count=args['indexCount'];first=args['firstIndex'];off=contract['ib']['offset']+first*2;indices=struct.unpack_from('<%dH'%count,ib,off);ids=sorted(set(indices));positions=[struct.unpack_from('<3f',vb,contract['vb']['pOffsets'][0]+(ix+args['vertexOffset'])*48)for ix in ids];uv=[struct.unpack_from('<2f',vb,(ix+args['vertexOffset'])*48+12)for ix in ids];material=next(u for u in contract['draw']['uniforms']if u['binding']==0);world=next(u for u in contract['draw']['uniforms']if u['binding']==4);memory=(C/'memory-52.bin').read_bytes();(Q/'material-68274.bin').write_bytes(memory[material['offset']:material['offset']+256]);(Q/'world-68274.bin').write_bytes(memory[world['offset']:world['offset']+256]);meta=dict(resources=found,draw_index_offset_bytes=off,draw_index_bytes=count*2,whole_index_buffer_bytes=len(ib),index_min=min(indices),index_max=max(indices),unique_vertices=len(ids),whole_vertex_count=len(vb)//48,draw_referenced_vertex_count=len(ids),all_vertices_referenced=len(ids)==len(vb)//48,local_bounds_min=[min(p[k]for p in positions)for k in range(3)],local_bounds_max=[max(p[k]for p in positions)for k in range(3)],uv_min=[min(p[k]for p in uv)for k in range(2)],uv_max=[max(p[k]for p in uv)for k in range(2)],world_constants=struct.unpack('<64f',(Q/'world-68274.bin').read_bytes()),material_constants=struct.unpack('<64f',(Q/'material-68274.bin').read_bytes()))
(Q/'native-subrange-evidence.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
