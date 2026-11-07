from pathlib import Path
import hashlib,json,re
p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\modding\pakfileunpacker.exe')
b=p.read_bytes();rows=[]
for term in [b'simtype',b'bxml',b'compiled',b'serialize']:
 for m in re.finditer(re.escape(term),b,re.I):
  start=max(0,b.rfind(b'\0',0,m.start())+1);end=b.find(b'\0',m.start());rows.append(dict(term=term.decode(),offset=hex(m.start()),text=b[start:min(end,start+300)].decode('ascii','replace')))
r=dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),strings=rows)
out=Path.home()/'Documents/Opem Amalur/outputs/scene-v14-astra/unpacker-strings.json';out.write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
