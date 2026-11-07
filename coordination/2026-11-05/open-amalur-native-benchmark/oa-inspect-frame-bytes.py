import collections,json,struct
from pathlib import Path
p=Path('/private/tmp/oa-dalentarth-20261105.gfxr');size=p.stat().st_size
parts={'before_state':collections.Counter(),'state':collections.Counter(),'frame':collections.Counter()};fills={k:collections.Counter() for k in parts};calls={k:collections.Counter() for k in parts};markers=[];phase='before_state'
with p.open('rb') as f:
 fourcc,major,minor,nopts=struct.unpack('<4sIII',f.read(16));assert fourcc==b'GFXR' and major==0;f.seek(nopts*8,1)
 while f.tell()<size:
  at=f.tell();payload_size,kind=struct.unpack('<QI',f.read(12));assert payload_size<=size-f.tell(),(at,payload_size);data=f.read(min(payload_size,40));base=kind&0x7fffffff
  assert base in range(1,7),(at,hex(kind))
  if base==2:
   marker,frame=struct.unpack_from('<IQ',data);markers.append({'offset':at,'marker':marker,'frame':frame})
   phase='state' if marker==1 else 'frame'
  parts[phase]['blocks']+=1;parts[phase]['stored_payload_bytes']+=payload_size
  if base==3 and len(data)>=4:
   meta=struct.unpack_from('<I',data)[0]
   if meta&0xffff==2:
    thread,memory,offset,n=struct.unpack_from('<QQQQ',data,4);parts[phase]['fill_calls']+=1;parts[phase]['fill_bytes']+=n;fills[phase][memory]+=n
  if base==4:
   api=struct.unpack_from('<I',data)[0];calls[phase][api]+=1
  f.seek(at+12+payload_size)
 assert f.tell()==size
out={'file_bytes':size,'state_markers':markers,'parts':{k:dict(v) for k,v in parts.items()},'frame_top_fill_memory_ids':fills['frame'].most_common(8),'frame_api_count':sum(calls['frame'].values()),'frame_unique_api_ids':len(calls['frame'])}
Path('/private/tmp/oa-capture-frame-bytes.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
