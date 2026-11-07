"""Bounded selected-scene object records. Unknown fields remain explicit."""
from pathlib import Path
import struct,json,hashlib,math,sys,csv
r=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(r/'work/v07-bxml'));from amalur_blob import parse_bytes
b=(r/'work/scene-inputs-v07/DATA_0.pak/524859.space_bxml').read_bytes();blob=parse_bytes(b);slots={s['slot_payload_offset'] for s in blob['slots']};end=8+blob['header']['payload_bytes'];ptr,count=struct.unpack_from('<II',b,8+0x210)
assert 0x210 in slots and count<=4096 and ptr>=8 and ptr+count*104<=end
symbols=r/'references/ZucchiniZap--AmalurBxmlConverter/bin/Release/net10.0-windows/symbol_tables'
types={int(x['id']):x['value'] for x in csv.DictReader((symbols/'simtype.csv').open(encoding='utf-8-sig'))};rows=[];ids=set()
for i in range(count):
 at=ptr+i*104;nameptr,instance=struct.unpack_from('<2I',b,at)
 if at-8 not in slots or not 8<=nameptr<end:raise ValueError('Object name relocation')
 finish=b.find(b'\0',nameptr,min(end,nameptr+1024))
 if finish<0:raise ValueError('Object name length')
 name=b[nameptr:finish].decode('utf-8');position=struct.unpack_from('<4f',b,at+8);quat=struct.unpack_from('<4f',b,at+24);scale=struct.unpack_from('<3f',b,at+40);flags,tid=struct.unpack_from('<2I',b,at+52)
 if instance in ids or not instance or any(not math.isfinite(x) for x in (*position,*quat,*scale)) or any(abs(x)>1000000 for x in position[:3]) or abs(sum(x*x for x in quat)-1)>.001:raise ValueError('Object identity/transform bounds')
 ids.add(instance);rows.append(dict(index=i,instance_id=instance,name=name,position_xyz=list(position[:3]),position_w=position[3],quaternion_xyzw=list(quat),scale_xyz=list(scale),flags=flags,type_id=tid,type_name=types.get(tid),owner_candidate=struct.unpack_from('<I',b,at+68)[0],faction_candidate=struct.unpack_from('<I',b,at+72)[0],global_ref_candidate=struct.unpack_from('<I',b,at+80)[0],unknown_words={str(off):struct.unpack_from('<I',b,at+off)[0] for off in [60,64,76,84,88,92,96,100]},raw_hex=b[at:at+104].hex()))
o=dict(source_sha256=hashlib.sha256(b).hexdigest(),native_stride_evidence='fdc910 root0x210 stride0x68',field_status='Names from relocated strings, IDs/types/transforms corroborated with symbol tables and existing placement form; native per-field consumer pending.',objects=rows,object_count=len(rows),limitations=['No object is spawned or scripted by this inventory.','Owner/faction/global-reference interpretations remain candidates.','Activity markers are included; not every entry is an interactable.'])
(r/'outputs/scene-v12/scene-objects.json').write_text(json.dumps(o,indent=2));print(json.dumps(dict(count=len(rows),names=[x['name'] for x in rows]),indent=2))
