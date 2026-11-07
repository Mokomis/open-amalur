import json,ctypes,struct,collections
from pathlib import Path
r=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');j=json.loads((r/'capture-index.json').read_text());fn=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int]
for mem in [52,60,7801]:
 matches=[x for x in j['fills'] if x['memory']==mem];a=matches[-1]
 with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb') as f:f.seek(a['file_offset']);d=f.read(a['stored_size'])
 out=ctypes.create_string_buffer(a['size']);assert fn(d[36:],out,len(d)-36,a['size'])==a['size'];(r/('memory-'+str(mem)+'.bin')).write_bytes(out.raw)
b=(r/'memory-52.bin').read_bytes()
for phase in [93,97,99]:
 ds=[d for d in j['draws'] if d['phase']==phase]
 print('phase',phase,'firstdraw',ds[0]['index'])
 for u in ds[0]['uniforms']:
  if u['binding']==68:
   print(u)
   for row in range(min(u['range']//16,16)):print(row,struct.unpack_from('<4f',b,u['offset']+row*16))
