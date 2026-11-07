from pathlib import Path
import struct,json,hashlib
root=Path.home()/'Documents'/'Opem Amalur';tab=struct.unpack('<50I',bytes.fromhex(json.loads((root/'outputs/bytecode-reader/v07-hash-table.json').read_text())['ranges'][0]['raw_hex']))
def hashname(s):
 b=s.encode('ascii').lower();return sum(tab[i%50]*v+tab[v%50]*(i+1) for i,v in enumerate(b))&0xffffffff
import argparse
ap=argparse.ArgumentParser();ap.add_argument('snapshot',type=Path);ap.add_argument('names',nargs='+');a=ap.parse_args()
d=a.snapshot.read_bytes();u=struct.unpack('<'+str(len(d)//4)+'I',d);n=u[1];assert u[0]==1 and len(d)==8+n*8;ids=u[2:2+n];hashes=u[2+n:]
rows=[{'name':name,'hash':hashname(name),'matches':[ids[i] for i,h in enumerate(hashes) if h==hashname(name)]} for name in a.names]
p=root/'outputs/scene-v08'/f'{a.snapshot.stem}-name-lookup.json';p.write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
