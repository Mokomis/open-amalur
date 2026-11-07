import subprocess,sys,re,json,hashlib
from pathlib import Path
r=Path.home()/'Documents/Opem Amalur';g=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
def lst(n):
    b=(r/f'outputs/{n}-archive-list.txt').read_bytes();return [x.strip() for x in b.decode('utf-16' if b[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines() if x.strip()]
pat={'initial':r'(\.shader_bxml|\.sky_bxml|\.koalighting|\.koalightpalette|\.koaregion|\.koaspace|platform_shader|shader.*\.bin|always_loaded)','patch':r'(\.koalighting|\.koalightpalette|\.koaregion|\.koaspace|\.sky_bxml|shader|texture_metadata|always_loaded)','DATA':r'(\.koaregion|\.koaspace)'}
for n,a in [('initial','initial_0.pak'),('patch','patch_0.pak'),('DATA','DATA_0.pak')]:
    names=[x for x in lst(n) if re.search(pat[n],x,re.I)]
    d=r/'work/v19-inputs'/a;d.mkdir(parents=True,exist_ok=True)
    for i in range(0,len(names),60):
        c=[str(g/'modding/pakfileunpacker.exe'),str(g/'data'/a),'unpack',str(d),*names[i:i+60]]
        p=subprocess.run(c,cwd=g/'modding',capture_output=True,timeout=300)
        if p.returncode:print('fail',a,p.returncode,p.stderr[:200])
    print(a,len(names),len(list(d.iterdir())))
