from pathlib import Path
import json,struct
root=Path.home()/'Documents'/'Opem Amalur'
for name in ['524859.bundle','524912.bundle']:
 p=root/'work/scene-inputs-v07/initial_0.pak'/name;d=p.read_bytes();print(name,len(d),d[:100]);print(struct.unpack_from('<'+str(min(80,len(d)//4))+'I',d))
