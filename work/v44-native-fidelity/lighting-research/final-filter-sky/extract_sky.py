from pathlib import Path
import json,ctypes,struct,hashlib,collections
p=Path(__file__).parent;src=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');index=json.loads((src/'capture-index.json').read_text());lib=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib');fn=lib.LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
res={}
with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb') as f:
 for name,mem,size in [('vertices',1884,11520),('indices',1886,3456)]:
  fill=[x for x in index['fills'] if x['memory']==mem][-1];f.seek(fill['file_offset']);stored=f.read(fill['stored_size'])
  if fill['compressed']:
   b=ctypes.create_string_buffer(fill['size']);assert fn(stored[36:],b,len(stored)-36,fill['size'])==fill['size'];raw=b.raw
  else:raw=stored[36:]
  assert len(raw)==size
  (p/f'sky-{name}.bin').write_bytes(raw);res[name]=dict(fill=fill,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
vs=[struct.unpack_from('<5f',(p/'sky-vertices.bin').read_bytes(),i*20) for i in range(576)];indices=struct.unpack('<1728H',(p/'sky-indices.bin').read_bytes());res['active_index_count']=1722;res['active_max_index']=max(indices[:1722]);res['vertex_count']=576;res['position_bounds']=[(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(5)];res['unique_z_counts']=collections.Counter(v[2] for v in vs);res['first_vertices']=vs[:40];res['first_indices']=indices[:40];res['last_vertices']=vs[-10:];res['last_indices']=indices[-40:]
(p/'sky-geometry.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
