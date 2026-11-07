from pathlib import Path
import struct,json
root=Path.home()/'Documents'/'Opem Amalur';d=(root/'work/scene-inputs-v07/initial_0.pak/inputdeviceaction_init.bin').read_bytes();u=struct.unpack('<'+str(len(d)//4)+'I',d);n=u[1];print('header',u[:10],'count',n,'length',len(d),'middle',u[2+n:2+n+12],'tail',u[-8:]);rows=[]
base=root/'references/ZucchiniZap--AmalurBxmlConverter/bin/Debug/net10.0-windows/symbol_tables'
for p in base.glob('*.csv'):
 for l in p.read_text(encoding='utf-8-sig').splitlines():
  if 'LedgerLaunchMap' in l:print(p.name,l)
