"""Seal source-owned character cubes; no host/core/default or preview changes."""
from pathlib import Path
import json,hashlib,importlib.util,struct
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v49-character-create/character-ambient-audit'
sp=importlib.util.spec_from_file_location('v19_lighting_decode',ROOT/'work/v19-lighting/decode_scene_lighting.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def seal(role,source,envslot,cubeslot,setting=0):
 raw=source.read_bytes();blob=m.Blob(raw)
 envbase,envcount=blob.array(envslot);assert setting<envcount
 envbase+=setting*m.ENV_RECORD_BYTES
 cubebase,ncubes=blob.array(cubeslot)
 fields={}
 for n,delta in [('world',0x550),('character',0x560)]:
  fields[n]=[{'key':key,'value':blob.u32(envbase+delta+4*k),'payload_offset':envbase+delta+4*k,'file_offset':envbase+delta+4*k+8} for k,key in enumerate(m.KEYS)]
 indices={q['value'] for q in fields['character']};assert len(indices)==1
 index=indices.pop();assert index<ncubes
 at=cubebase+index*m.CUBE_ENTRY_BYTES
 faces=[]
 for f in range(6):
  a,n=blob.array(at+8*f);assert n==64;faces.append(a)
 bgra=b''.join(blob.payload[a:a+256] for a in faces);assert len(bgra)==1536
 rgba=bytearray(bgra);rgba[0::4],rgba[2::4]=bgra[2::4],bgra[0::4];rgba=bytes(rgba)
 stem=f'{role}-character-ambient'
 (OUT/f'{stem}.bgra').write_bytes(bgra);(OUT/f'{stem}.rgba').write_bytes(rgba)
 h=['/* SOURCE BGRA DWORD bytes; room_lighting.c requires R/B swap on upload. */',
    f'static const unsigned char oa_{role.replace("-","_")}_character_ambient_bgra[6][256]={{']
 h.extend('{'+','.join(map(str,bgra[f*256:f*256+256]))+'},' for f in range(6));h.append('};')
 (OUT/f'{stem}-bgra.inc').write_text('\n'.join(h)+'\n')
 return {'role':role,'source':str(source.relative_to(ROOT)),'source_sha256':sha(raw),'environment_table_payload_slot':envslot,'environment_index':setting,'environment_payload_offset':envbase,'cube_table_payload_slot':cubeslot,'cube_count':ncubes,'selected_character_cube':index,'explicit_time_fields':fields,'face_order':['+X','-X','+Y','-Y','+Z','-Z'],'face_texel_payload_offsets':faces,'face_texel_file_offsets':[a+8 for a in faces],'width':8,'height':8,'faces':6,'mip_levels':1,'bytes':1536,'authored_bgra_file':f'{stem}.bgra','authored_bgra_sha256':sha(bgra),'converted_rgba_file':f'{stem}.rgba','converted_rgba_sha256':sha(rgba),'first_bgra':list(bgra[:4]),'first_rgba':list(rgba[:4]),'source_to_upload':'Swap byte0/byte2 per texel, preserve all face order, rows, G and A. Do not sRGB-decode these UNORM bytes. No added mipmaps.'}
rows=[
 seal('opening-base',ROOT/'work/v48-opening/content-audit/inputs/patch_0.pak/1262814.region_bxml',0xf0,0xe8),
 seal('opening-start',ROOT/'work/v48-opening/content-audit/inputs/patch_0.pak/1417252.space_bxml',0xc0,0xb8,0)]
e=json.loads((ROOT/'work/v48-opening/lighting-selection-audit/lighting-selection-evidence.json').read_text())
assert rows[1]['source_sha256']==e['source_sha256']
assert rows[1]['environment_payload_offset']==e['environments'][0]['decoded']['source_offset']
assert rows[0]['source_sha256']=='c65e0a23a4edf3d0deaf5444d3785534351bee82e1c2d59e23bfa0b291b8ba2d'
out={'schema':'open-amalur.character-ambient-source.v1','resources':rows,
 'base_start_same_pixels':rows[0]['authored_bgra_sha256']==rows[1]['authored_bgra_sha256'],
 'native_channel_evidence':'Region431608 cubes2/3 after exactly R/B swap match captured world7496/7499 and character7502 across all1536 bytes; authored-character-cube-join.json',
 'opening_evidence_limit':'Source bytes and explicit selection fields proven. No original opening capture correlated here. Start setting0 belongs to Space1417252 local cube table imported at Space+B8 through dd0580/ce21d0; actual override mode/portal blending remains outside this pass. Parent owner-preferred BASE default unchanged.'}
(OUT/'opening-character-cubes.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'resources':[{'role':x['role'],'index':x['selected_character_cube'],'bgraSHA':x['authored_bgra_sha256'],'rgbaSHA':x['converted_rgba_sha256'],'firstBGRA':x['first_bgra'],'env':x['environment_payload_offset'],'faces':x['face_texel_payload_offsets']} for x in rows],'same':out['base_start_same_pixels']}))
