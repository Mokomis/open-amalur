from pathlib import Path
import ctypes,hashlib,json,struct
source=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera')
capture=Path('/private/tmp/oa-dalentarth-20261105.gfxr')
out=Path(__file__).resolve().parent
index=json.loads((source/'capture-index.json').read_text())
fill=[x for x in index['fills'] if x['memory']==52][-1]
assert fill['offset']==0 and fill['size']==33554432 and fill['compressed']
with capture.open('rb') as f:
 f.seek(fill['file_offset']);stored=f.read(fill['stored_size'])
# Existing oa-extract-uniforms.py established the FillMemory metadata is36bytes.
fn=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe
fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
buf=ctypes.create_string_buffer(fill['size'])
assert fn(stored[36:],buf,len(stored)-36,fill['size'])==fill['size']
mem=buf.raw
assert mem==(source/'memory-52.bin').read_bytes(), 'Existing full memory snapshot differs'
records=[]
for name,offset,size,draw,phase,pipeline,module in [
 ('bloom-extract',1764928,16,73280,119,7584,1851),
 ('lut-generator',1765632,64,73395,134,7599,1855),
 ('merge',1765696,48,73404,135,7603,1858),
 ('final-filter',1765760,48,73411,136,7607,1860)]:
 b=mem[offset:offset+size];(out/(name+'.bin')).write_bytes(b)
 records.append(dict(name=name,memory=52,offset=offset,bytes=size,draw_index=draw,phase=phase,pipeline=pipeline,fragment_shader_module=module,float_values=struct.unpack('<%df'%(size//4),b),sha256=hashlib.sha256(b).hexdigest()))
meta=dict(capture=str(capture),capture_bytes=capture.stat().st_size,capture_sha256=hashlib.sha256(capture.read_bytes()).hexdigest(),index_sha256=hashlib.sha256((source/'capture-index.json').read_bytes()).hexdigest(),fill_record=fill,stored_payload_sha256=hashlib.sha256(stored).hexdigest(),decompressed_memory_sha256=hashlib.sha256(mem).hexdigest(),existing_full_memory_equal=True,records=records)
(out/'post-constants.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(dict(existing_full_memory_equal=True,capture_sha256=meta['capture_sha256'],records=records),indent=2))
