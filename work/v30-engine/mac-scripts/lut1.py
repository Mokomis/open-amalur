import subprocess,struct,re,os
from pathlib import Path
g=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
ID='1525613'
for n,a in (('DATA','DATA_0.pak'),('initial','initial_0.pak'),('patch','patch_0.pak')):
    b=open(f'outputs/{n}-archive-list.txt','rb').read();L=[x.strip() for x in b.decode('utf-16' if b[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines()]
    h=[x for x in L if x.startswith(ID)]
    print(a,h)
    if h:
        d=Path('work/v19-inputs')/a;d.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(g/'modding/pakfileunpacker.exe'),str(g/'data'/a),'unpack',str(Path.cwd()/d),*h],cwd=g/'modding',capture_output=True,timeout=200)
        for x in h:
            q=d/x;c=q.read_bytes();print(x,len(c),c[:48].hex())
            aid,w,hh,var=struct.unpack_from('<IHHB',c,0);mag=c[16:20]
            W,H,D_,fl,ty,fm,lut,ms,au,av,aw,lv=struct.unpack_from('<HHHHBBBBBBBB',c,20)
            print(dict(aid=aid,w=w,h=hh,var=var,magic=mag.hex(),W=W,H=H,D=D_,flags=fl,type=ty,format=fm,levels=lv))
