from pathlib import Path
import struct,collections,json,platform
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';rows=[]
for p in (r/'work/scene-inputs-v07').glob('*/fab_init*.bin'):
 d=p.read_bytes();v,n=struct.unpack_from('<II',d);u=struct.unpack_from('<'+str(n*2)+'I',d,8);ids=u[:n];hs=u[n:]
 di={x:c for x,c in collections.Counter(ids).items() if c>1};dh={x:c for x,c in collections.Counter(hs).items() if c>1}
 rows.append(dict(file=str(p),version=v,count=n,bytes=len(d),duplicate_ids=list(di.items()),duplicate_hashes=list(dh.items()),pairs=[(i,h) for i,h in zip(ids,hs) if i in di or h in dh]))
p=r/'outputs/scene-v08/fab-catalog-duplicates.json';p.write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
