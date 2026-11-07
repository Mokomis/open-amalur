"""Join captured ambient pixels to authored Region cube records by bytes,
using the independently decoded selected environment's explicit two fields."""
from pathlib import Path
import json,hashlib,importlib.util,struct
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v49-character-create/character-ambient-audit'
spec=importlib.util.spec_from_file_location('v19_lighting_decode',ROOT/'work/v19-lighting/decode_scene_lighting.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
source=ROOT/'work/v20-inputs/patch_0.pak/431608.region_bxml';raw=source.read_bytes();blob=mod.Blob(raw)
cubes=mod.decode_cubes(blob)
captures={i:(OUT/f'image-{i}-tight.rgba').read_bytes() for i in [7496,7499,7502]}
allmatches={}
authored={}
for cube in cubes:
 pixels=b''.join(blob.payload[a:a+256] for a in cube['face_texel_offsets'])
 rgba=bytearray(pixels)
 rgba[0::4],rgba[2::4]=pixels[2::4],pixels[0::4]
 rgba=bytes(rgba);authored[cube['index']]=rgba
 for image,cap in captures.items():
  if rgba==cap:allmatches.setdefault(image,[]).append({'cube_index':cube['index'],'transform':'R/Bswap only; face/row order unchanged','source_face_payload_offsets':cube['face_texel_offsets'],'sha256':hashlib.sha256(rgba).hexdigest()})
noon=json.loads((ROOT/'work/v43-scene-fidelity/lighting-research/authored-noon.json').read_text())['Noon']
world=noon['ambient_cube_index'];character=noon['character_ambient_cube_index']
assert authored[world['value']]==captures[7496]
assert authored[character['value']]==captures[7502]
for role,item in [('world',world),('character',character)]:
 assert struct.unpack_from('<I',blob.payload,item['source_offset'])[0]==item['value']
 data=authored[item['value']]
 (OUT/f'authored-{role}-noon.rgba').write_bytes(data)
 if role=='character':
  h=['/* Generated from Region431608 Noon.character_ambient_cube_index; nativeRGBA byte identity proven. */','static const unsigned char oa_character_ambient_noon[6][256]={']
  for face in range(6):h+=['{'+','.join(str(x) for x in data[face*256:(face+1)*256])+'},']
  h+=['};'];(OUT/'character_ambient_noon.inc').write_text('\n'.join(h)+'\n')
out={'source':str(source),'source_sha256':hashlib.sha256(raw).hexdigest(),'cube_count':len(cubes),'explicit_environment_fields':{'world':world,'character':character},'capture_source_byte_matches':allmatches,'character_7502_equals_world_7496':captures[7502]==captures[7496],'cube7499_equals7496':captures[7499]==captures[7496],'character_first_rgba':list(captures[7502][:4]),'world_first_rgba':list(captures[7496][:4]),'policy':'Portable bytes come from authored source, not copied capture. Do not fix world+1 or ordinal; read explicit active environment character field. R/B conversion matches actualRGBA views; no other remap.'}
(OUT/'authored-character-cube-join.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
