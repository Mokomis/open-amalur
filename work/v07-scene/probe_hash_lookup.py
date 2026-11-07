from pathlib import Path
import struct,json,hashlib
root=Path.home()/'Documents'/'Opem Amalur';tab=struct.unpack('<50I',bytes.fromhex(json.loads((root/'outputs/bytecode-reader/v07-hash-table.json').read_text())['ranges'][0]['raw_hex']))
def hashname(s):
 b=s.encode('ascii').lower();return sum(tab[i%50]*v+tab[v%50]*(i+1) for i,v in enumerate(b))&0xffffffff
d=(root/'work/scene-inputs-v07/initial_0.pak/inputdeviceaction_init.bin').read_bytes();u=struct.unpack('<'+str(len(d)//4)+'I',d);n=u[1];ids=u[2:2+n];hashes=u[2+n:]
rows=[]
for name in ['LedgerLaunchMap','Ledger','LedgerMap','none','None','Action','Jump']:
 h=hashname(name);rows.append({'name':name,'hash':h,'matches':[{'index':i,'id':ids[i]} for i,v in enumerate(hashes) if v==h]})
r={'header':u[:2],'shape_exact':len(d)==8+n*8,'unique_hashes':len(set(hashes)),'hash_table':list(tab),'lookups':rows}
(root/'outputs/scene-v07/input-action-name-probe.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
