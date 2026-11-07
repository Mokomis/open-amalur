from pathlib import Path
import json,struct,csv,hashlib,collections
r=Path.home()/'Documents/Opem Amalur';source=r/'work/scene-inputs-v07/DATA_0.pak/524859.space_bxml';b=source.read_bytes();assert hashlib.sha256(b).hexdigest()=='775fb38b3fd9ff67ed3181579e935c70b33bd6831ccebf744ce4b2f6cd590143'
pointer,count=struct.unpack_from('<II',b,8+0x90);end=struct.unpack_from('<I',b,8+0x98)[0];assert count==36 and (end-pointer)==count*108
lookups={};symbols=r/'references/ZucchiniZap--AmalurBxmlConverter/bin/Release/net10.0-windows/symbol_tables'
for name in ['simtype','luascript','globalobjectref','lua_script_path']:
 p=symbols/(name+'.csv')
 if p.exists():lookups[name]={int(x['id']):x['value'] for x in csv.DictReader(p.open(encoding='utf-8-sig'))}
records=[];hits=collections.Counter()
for i in range(count):
 raw=b[pointer+i*108:pointer+(i+1)*108];matches=[]
 for off in range(0,108,4):
  word=struct.unpack_from('<I',raw,off)[0]
  if word<=1 or word==0xffffffff:continue
  for kind,table in lookups.items():
   if word in table:matches.append(dict(offset=off,id=word,kind=kind,name=table[word]));hits[f'{kind}+{off}']+=1
 records.append(dict(index=i,file_offset=pointer+i*108,words=list(struct.unpack('<27I',raw)),matches=matches))
o=dict(scope='Exact selected root0x90/count36/stride108 spans; field semantics not yet established',source_sha256=hashlib.sha256(b).hexdigest(),array_pointer=pointer,count=count,stride=108,symbol_hits=dict(hits),records=records)
(r/'outputs/scene-v12/object-inventory.json').write_text(json.dumps(o,indent=2));print(json.dumps(dict(symbol_hits=dict(hits),records=[dict(index=x['index'],matches=x['matches']) for x in records]),indent=2))
