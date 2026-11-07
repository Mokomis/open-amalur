from pathlib import Path
import json,struct,shutil,subprocess
r=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');j=json.loads((r/'camera-manifest.json').read_text());b=(r/'memory-52.bin').read_bytes();vp=json.loads((r/'shared-camera-records.json').read_text())[0]['vp'];relative=j['matrices'][0]['base'];rel=[];inputs=bytearray();expected=bytearray()
def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def mul(a,b):return [f32(((a[c]*b[4*row]+a[4+c]*b[4*row+1])+a[8+c]*b[4*row+2])+a[12+c]*b[4*row+3]) for row in range(4) for c in range(4)]
for m in j['matrices']:
 off=m['offset'];model=struct.unpack_from('<16f',b,off-128);want=struct.pack('<16f',*m['base']);chosen=vp
 if struct.pack('<16f',*mul(vp,model))!=want:
  assert struct.pack('<16f',*mul(relative,model))==want;chosen=relative;rel.append(off)
 inputs.extend(struct.pack('<32f',*(list(chosen)+list(model))));expected.extend(want)
(r/'matrix-real-producer-inputs.bin').write_bytes(inputs);(r/'matrix-real-producer-expected.bin').write_bytes(expected)
(r/'relative-projection-offsets.json').write_text(json.dumps(rel));print('Relative source offsets',rel)
# Keep prior 2623 corpus unchanged and add1598 real producer pairs in a separate4221 corpus.
(r/'matrix-proof-expanded-inputs.bin').write_bytes((r/'matrix-proof-inputs.bin').read_bytes()+inputs)
