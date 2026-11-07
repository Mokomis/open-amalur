from pathlib import Path
import json,hashlib,sys,struct
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v15';e=json.loads((o/'rea-runtime-early/trace_status.json').read_text())['structuredContent'];messages=[m.get('payload',{}) for m in e['normalized_result']['messages']]
loaded=[m for m in messages if m.get('event')=='selected_runtime_type' and m['id']==230417];assert loaded and all(x['object']==loaded[0]['object'] for x in loaded)
object_pointer=loaded[0]['object'];entries=[m for m in messages if m.get('event')=='type_reader_entry' and m['type_object']==object_pointer and 'complete_source_hex' in m];assert entries
raws={bytes.fromhex(m['complete_source_hex']) for m in entries};assert len(raws)==1;raw=next(iter(raws));assert len(raw)==408
sys.path[:0]=[str(r/'work/v07-bxml'),str(r/'work/v13-properties')]
from compiled_type import decode_compiled_type
cm=json.loads((r/'outputs/scene-v13/component-map.json').read_text());names={p['kind']:p['tables'][0]['name'] for p in cm['components']};decoded=decode_compiled_type(raw,names)
assert decoded['parent_key_u32']==226948 and decoded['script_key_u32']==237033
assert [p['kind'] for p in decoded['components']]==[p['kind'] for p in loaded[0]['parts']]
target=r/'work/v15-properties/native-workbench-230417.bin'
if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve differing capture')
target.write_bytes(raw)
proof=dict(status='complete real native-reader input decoded; compact conversion remains unresolved',capture_sha256=hashlib.sha256(raw).hexdigest(),capture_bytes=len(raw),native_type_id=230417,native_type_object=object_pointer,evidence_id=e['evidence_id'],readers=[dict(entry_kind=x['entry_kind'],source=x['source'],type_object=x['type_object'],type_vtable=x['type_vtable'],stack=x['stack']) for x in entries],native_snapshot=loaded[0],decoded=decoded,compact_source=dict(bytes=33,sha256='502a854c3f09c5226468542c3c0d0ea2c85bd28b0435bd93c3dd99523e024207',relationship='same type/parent/script and runtime object identity; byte-format conversion not yet located'))
(o/'native-workbench-decoded.json').write_text(json.dumps(proof,indent=2));print(json.dumps(dict(bytes=len(raw),sha256=proof['capture_sha256'],parent=decoded['parent_key_u32'],script=decoded['script_key_u32'],components=[dict(kind=p['kind'],name=p['native_name'],reference_keys=p.get('reference_keys_u32')) for p in decoded['components']],readers=proof['readers']),indent=2))
