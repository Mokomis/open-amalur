"""Seal world peers to the separately selected character cubes; source assets only."""
from pathlib import Path
import importlib.util,json,hashlib
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v49-character-create/character-ambient-audit'
sp=importlib.util.spec_from_file_location('m',ROOT/'work/v19-lighting/decode_scene_lighting.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
d=json.loads((OUT/'opening-character-cubes.json').read_text());rows=[]
for char in d['resources']:
 blob=m.Blob((ROOT/char['source']).read_bytes());assert blob.sha256==char['source_sha256']
 selected=char['explicit_time_fields']['world'];indices={x['value'] for x in selected};assert len(indices)==1
 index=indices.pop();a,n=blob.array(char['cube_table_payload_slot']);assert index<n
 faces=[blob.array(a+48*index+8*f)[0] for f in range(6)]
 bgra=b''.join(blob.payload[x:x+256] for x in faces);rgba=bytearray(bgra)
 rgba[0::4],rgba[2::4]=bgra[2::4],bgra[0::4];rgba=bytes(rgba)
 stem=char['role']+'-world-ambient'
 for ext,data in [('bgra',bgra),('rgba',rgba)]:(OUT/f'{stem}.{ext}').write_bytes(data)
 h=['/* SOURCE BGRA DWORD bytes; room_lighting.c requires R/B swap on upload. */',f'static const unsigned char oa_{char["role"].replace("-","_")}_world_ambient_bgra[6][256]={{']
 h.extend('{'+','.join(map(str,bgra[f*256:(f+1)*256]))+'},' for f in range(6));h.append('};');(OUT/f'{stem}-bgra.inc').write_text('\n'.join(h)+'\n')
 rows.append({'role':char['role'],'source':char['source'],'source_sha256':char['source_sha256'],'environment_payload_offset':char['environment_payload_offset'],'cube_table_payload_slot':char['cube_table_payload_slot'],'selected_world_cube':index,'explicit_time_fields':selected,'face_texel_payload_offsets':faces,'face_texel_file_offsets':[x+8 for x in faces],'face_order':char['face_order'],'width':8,'height':8,'faces':6,'mip_levels':1,'bytes':len(bgra),'authored_bgra_file':stem+'.bgra','authored_bgra_sha256':hashlib.sha256(bgra).hexdigest(),'converted_rgba_file':stem+'.rgba','converted_rgba_sha256':hashlib.sha256(rgba).hexdigest(),'first_bgra':list(bgra[:4]),'first_rgba':list(rgba[:4])})
expected='ec33749a7ff2170480dabcac78bb702c386b0174429451ef2d28e70820a91985'
assert all(x['authored_bgra_sha256']==expected for x in rows)
out={'schema':'open-amalur.world-ambient-source.v1','resources':rows,'base_start_same_pixels':rows[0]['authored_bgra_sha256']==rows[1]['authored_bgra_sha256'],'parent_reported_preview_bgra_sha256':expected,'all_match_parent_reported_preview':all(x['authored_bgra_sha256']==expected for x in rows),'qualification':'Both independent authored source world selections yield identical pixels. Parent reported its preview embedded hash; this script compares that supplied value, does not read or modify preview assets. No original-opening capture proof or profile activation.'}
(OUT/'opening-world-cubes.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
