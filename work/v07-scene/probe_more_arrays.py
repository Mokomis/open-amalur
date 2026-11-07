from pathlib import Path
import struct,json,sys,re
root=Path.home()/'Documents'/'Opem Amalur';d=(root/'work/scene-inputs-v07/DATA_0.pak/524859.space_bxml').read_bytes();p=d[8:];ids=set()
for n in ['initial','DATA']:
 raw=(root/f'outputs/{n}-archive-list.txt').read_bytes();t=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
 for l in t.splitlines():
  m=re.fullmatch(r'(\d+)\.fab_bxml',l.strip())
  if m:ids.add(int(m[1]))
rows=[]
for slot,stride in [(0x98,80),(0x148,80),(0x150,84),(0x158,80),(0x160,84),(0x178,80),(0x180,84),(0x210,104),(0xb0,100),(0xd0,0)]:
 target,count=struct.unpack_from('<II',p,slot);o=target-8
 row={'slot':hex(slot),'target_file':target,'count':count,'assumed_stride':stride,'first_records':[]}
 if stride and target+count*stride<=len(d):
  hits={}
  for j in range(0,stride,4):
   values=[struct.unpack_from('<I',p,o+i*stride+j)[0] for i in range(count)];good=[v for v in values if v in ids]
   if good:hits[str(j)]={'matches':len(good),'unique':sorted(set(good))}
  row['fab_matches_by_offset']=hits
  for i in range(min(count,2)):
   raw=p[o+i*stride:o+(i+1)*stride];row['first_records'].append({'u32':list(struct.unpack('<'+str(stride//4)+'I',raw)),'f32':list(struct.unpack('<'+str(stride//4)+'f',raw))})
 rows.append(row)
(root/'outputs/scene-v07/more-arrays-probe.json').write_text(json.dumps(rows,indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='first_records'} for r in rows],indent=2))
