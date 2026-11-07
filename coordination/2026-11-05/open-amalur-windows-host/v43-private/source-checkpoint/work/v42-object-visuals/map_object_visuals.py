from pathlib import Path
import sys,json,struct,hashlib,collections,math
r=Path(__file__).resolve().parents[1].parent;w=Path(__file__).resolve().parent
sys.path[:0]=[str(r/p) for p in ['work/v07-bxml','work/v13-properties','work/v15-properties']]
from native_type_catalog import index_batch,member_bytes,decode_type
names={x['kind']:x['tables'][0]['name'] for x in json.loads((r/'outputs/scene-v13/component-map.json').read_text())['components']}
batch=(r/'work/scene-inputs-v09/patch_0.pak/134225858_ksmt.batch').read_bytes();assert hashlib.sha256(batch).hexdigest()=='09dff529684d2deef530a418c11b0729fedb6b89f85e61cdd84f04f18942268c';index=index_batch(batch)
syms=json.loads((r/'work/v20-inputs/symbols.json').read_text());catalog=json.loads((r/'work/v41-world-objects/native-placement-catalog.json').read_text());sids={x['space_id'] for x in catalog['spaces']}
placed=catalog['records']+[x for x in catalog['global_records'] if x['space_id'] in sids];types={};stats=collections.Counter();instances=[]
def get_type(key):
 if key in types:return types[key]
 if key not in index['members']:return None
 raw=member_bytes(batch,index['members'][key]);d=decode_type(raw,names)
 parts=[]
 for part in d['components']:
  if part['kind']!=7:continue
  at=8+part['payload_offset'];end=8+struct.unpack_from('<I',raw)[0];assert at+0x28<=end
  refs=[struct.unpack_from('<I',raw,at+off)[0] for off in range(0x14,0x28,4)]
  parts.append({'payload_offset':part['payload_offset'],'references_14_18_1c_20_24':refs,'primary_fab':refs[0],'primary_fab_name':syms['fab'].get(str(refs[0]))})
 row={'type_id':key,'type_name':syms['simtype'].get(str(key)),'parent_type_id':d['parent_key_u32'],'flags':d['type_flags_u32'],'components':[p['kind'] for p in d['components']],'rendering':parts,'sha256':d['input_sha256']};types[key]=row;return row
for x in placed:
 row=get_type(x['type_id']);stats['instances']+=1
 if not row:stats['missing_type']+=1;continue
 rend=row['rendering']
 if rend:
  stats['direct_rendering_instances']+=1
  for rr in rend:
   if rr['primary_fab_name']:stats['named_primary_instances']+=1
  instances.append({**x,'rendering':rend})
 else:stats['without_direct_rendering']+=1
out={'batch_sha256':index['input_sha256'],'evidence':['00f0cc50 (reference resolution, fields +0x14..+0x24)','existing Workbench type rendering proof'],'stats':dict(stats),'types':list(types.values()),'instances':instances,'limitations':['Direct rendering components only; no inferred parent inheritance','Primary +0x14 is the previously recovered FAB role; other references remain named only by offsets','Does not instantiate gameplay or apply meshes yet']}
(w/'direct-rendering-catalog.json').write_text(json.dumps(out,indent=2));print(json.dumps(out['stats'],indent=2))
eye=[8591.932617,-87036.03125,6493.066406]
for x in sorted(instances,key=lambda x:math.dist(x['position'],eye))[:15]:print(x['type_name'],round(math.dist(x['position'],eye)),x['rendering'])
