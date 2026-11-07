from pathlib import Path
import json,struct,ctypes,hashlib,collections
R=Path(__file__).resolve().parent;A=json.loads((R/'active-water-bindings.json').read_text());want={b for d in A if d['draw']['phase']==108 and d['draw']['pipeline']!=7551 for b in [d['vertex_buffers']['pBuffers'][0],d['index_buffer']['buffer']]};fn=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int;meta=[]
with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb') as f:
 _,_,_,n=struct.unpack('<4sIII',f.read(16));f.seek(n*8,1);i=-1
 while h:=f.read(12):
  size,k=struct.unpack('<QI',h);i+=1;off=f.tell();d=f.read(min(size,36))
  if k&0x7fffffff==3 and len(d)>=36 and struct.unpack_from('<I',d)[0]&0xffff==7 and struct.unpack_from('<Q',d,20)[0] in want:
   _,thread,dev,buffer,bytes_=struct.unpack('<IQQQQ',d);d+=f.read(size-len(d));raw=d[36:]
   if k&0x80000000:
    out=ctypes.create_string_buffer(bytes_);assert fn(raw,out,len(raw),bytes_)==bytes_;raw=out.raw
   assert len(raw)==bytes_;(R/'resources'/f'buffer-{buffer}.bin').write_bytes(raw);info=dict(buffer=buffer,block=i,file_offset=off,stored_bytes=size,bytes=bytes_,sha256=hashlib.sha256(raw).hexdigest());meta.append(info)
  else:f.seek(size-len(d),1)
for d in A:
 if d['draw']['phase']==108 and d['draw']['pipeline']!=7551:
  vb=d['vertex_buffers']['pBuffers'][0];raw=(R/'resources'/f'buffer-{vb}.bin').read_bytes();stride=d['vertex_buffers']['pStrides'][0];colors=collections.Counter(tuple(raw[i+44:i+48]) for i in range(0,len(raw),stride));print(d['draw']['index'],vb,'stride',stride,'vertex_colors',colors.most_common(12))
(R/'buffer-provenance.json').write_text(json.dumps(meta,indent=2))
