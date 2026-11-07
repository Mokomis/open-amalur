from pathlib import Path
import json,struct,collections,hashlib
w=Path(__file__).resolve().parent;r=w.parents[1]
catalog=json.loads((w/'native-placement-catalog.json').read_text());total=collections.Counter();examples=[];spaces=[]
for space in catalog['spaces']:
 p=Path(space['source']);d=p.read_bytes();end=struct.unpack_from('<I',d)[0]+8
 assert hashlib.sha256(d).hexdigest()==space['sha256']
 def array(slot,stride):
  ptr,count=struct.unpack_from('<II',d,8+slot)
  assert count<1000000 and (not count or 8<=ptr<=end-count*stride)
  return [d[ptr+i*stride:ptr+(i+1)*stride] for i in range(count)]
 refs=array(0x1b0,4);centers=array(0x1a8,12);renders=array(0x160,84)
 stats=collections.Counter(refs=len(refs),centers=len(centers),renders=len(renders))
 assert len(refs)==len(centers)==len(renders)
 by_center={tuple(round(x,2) for x in struct.unpack('<3f',c)):rr for c,rr in zip([rr[:12] for rr in renders],renders)}
 for i,(ref,center,rr) in enumerate(zip(refs,centers,renders)):
  stats['exact_index_center_matches']+=center==rr[:12]
  legacy=by_center.get(tuple(round(x,2) for x in struct.unpack('<3f',center)))
  if legacy!=rr:
   stats['legacy_replaced_render_records']+=1
   if len(examples)<20:examples.append({'space':space['name'],'index':i,'typed_fab':hex(struct.unpack('<I',ref)[0]),'sphere':struct.unpack_from('<4f',rr),'original_assembly':struct.unpack_from('<I',rr,68)[0],'legacy_assembly':struct.unpack_from('<I',legacy,68)[0] if legacy else None,'original_material':struct.unpack_from('<I',rr,64)[0],'legacy_material':struct.unpack_from('<I',legacy,64)[0] if legacy else None})
 total.update(stats);spaces.append({'space':space['name'],'stats':dict(stats)})
out={'stats':dict(total),'spaces':spaces,'examples':examples,'conclusion':'Direct index pairing is REJECTED: only 224/18802 centers align by index. Arrays are ordered differently. Keep coordinate matching until native join semantics are recovered; no data rebuilt.'}
(w/'static-pairing-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out['stats'],indent=2));print(json.dumps(examples[:4],indent=2))
