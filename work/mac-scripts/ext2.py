import subprocess,re
from pathlib import Path
r=Path.home()/'Documents/Opem Amalur';g=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
def lst(n):
    b=(r/f'outputs/{n}-archive-list.txt').read_bytes();return [x.strip() for x in b.decode('utf-16' if b[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines() if x.strip()]
for n,a in [('DATA','DATA_0.pak'),('patch','patch_0.pak')]:
    names=[x for x in lst(n) if x.endswith('.region_bxml')]
    d=r/'work/v19-inputs'/a;d.mkdir(parents=True,exist_ok=True)
    for i in range(0,len(names),80):
        p=subprocess.run([str(g/'modding/pakfileunpacker.exe'),str(g/'data'/a),'unpack',str(d),*names[i:i+80]],cwd=g/'modding',capture_output=True,timeout=500)
        if p.returncode:print('fail',a,p.returncode)
    print(a,len(names),len(list(d.glob('*.region_bxml'))))
