from pathlib import Path
import json,ctypes,struct
p=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');d=json.loads((p/'capture-index.json').read_text());fills=[x for x in d['fills'] if x['memory']==129];print('fills',fills)
lib=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib');fn=lib.LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
mem=bytearray(33554432)
with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb') as f:
 for x in fills:
  f.seek(x['file_offset']);b=f.read(x['stored_size']);buf=ctypes.create_string_buffer(x['size']);got=fn(b[36:],buf,len(b)-36,x['size']);assert got==x['size'];mem[x['offset']:x['offset']+x['size']]=buf.raw
for off in [36336,36408,36480,36552,36624,36696]:print(off,[struct.unpack_from('<5fI',mem,off+i*24) for i in range(3)])
Path('/private/tmp/oa-v44-lighting/ao-vertices.bin').write_bytes(mem[36336:36768])
