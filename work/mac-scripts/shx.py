"""Decompress aPLib-packed DXBC shaders embedded in koa.exe into outputs/scene-v19/shaders (derived, private)."""
import re,struct,os,json,ctypes,hashlib,sys
EXE=r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe'
c=open(EXE,'rb').read()
def aplib(s,p,out_size):
    d=bytearray();d.append(s[p]);p+=1
    tag=0;bits=0;lastoff=0;lwm=0
    def gb():
        nonlocal tag,bits,p
        if bits==0:tag=s[p];p+=1;bits=8
        b=(tag>>7)&1;tag=(tag<<1)&255;bits-=1;return b
    def gam():
        v=1
        while True:
            v=v*2+gb()
            if not gb():return v
    while len(d)<out_size:
        if not gb():
            d.append(s[p]);p+=1;lwm=0;continue
        if not gb():
            o=gam()
            if lwm==0 and o==2:
                o=lastoff;n=gam()
            else:
                o-=3 if lwm==0 else 2
                o=(o<<8)|s[p];p+=1;n=gam()
                if o>=32000:n+=1
                if o>=1280:n+=1
                if o<128:n+=2
                lastoff=o
            for _ in range(n):d.append(d[-o])
            lwm=1;continue
        if not gb():
            b=s[p];p+=1;n=2+(b&1);o=b>>1
            if o==0:break
            lastoff=o
            for _ in range(n):d.append(d[-o])
            lwm=1;continue
        o=0
        for _ in range(4):o=o*2+gb()
        d.append(d[-o] if o else 0);lwm=0
    return bytes(d),p
heads=[]
for m in re.finditer(b'D\x00XBC',c):
    i=m.start()
    us,one,cs=struct.unpack_from('<III',c,i-12)
    heads.append((i,us,one,cs))
print('headers',len(heads),'one=1',sum(h[2]==1 for h in heads))
os.makedirs('outputs/scene-v19/shaders',exist_ok=True)
rows=[];bad=0
for i,us,one,cs in heads:
    if not 32<us<4000000:bad+=1;continue
    try:d,e=aplib(c,i,us)
    except Exception as ex:bad+=1;continue
    if len(d)!=us or d[:4]!=b'DXBC':bad+=1;continue
    h=hashlib.sha1(d).hexdigest()[:16]
    open(f'outputs/scene-v19/shaders/{i:08x}_{h}.dxbc','wb').write(d)
    rows.append(dict(file_offset=i,uncompressed=us,compressed=cs,consumed=e-i,sha1=h))
print('ok',len(rows),'bad',bad,'consumed==cs',sum(r['consumed']==r['compressed'] for r in rows))
json.dump(rows,open('outputs/scene-v19/shader-blobs.json','w'),indent=0)
