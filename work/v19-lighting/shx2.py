"""Decompress multi-block aPLib DXBC shaders from koa.exe, disassemble with D3DCompiler_47, index reflection names (derived, private)."""
import re,struct,os,json,ctypes,hashlib,sys,collections,shutil
EXE=r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe'
c=open(EXE,'rb').read()
def aplib(s,p,limit):
    start=p;d=bytearray();d.append(s[p]);p+=1;tag=0;bits=0;lastoff=0;lwm=0
    def gb():
        nonlocal tag,bits,p
        if bits==0:tag=s[p];p+=1;bits=8
        b=(tag>>7)&1;tag=(tag<<1)&255;bits-=1;return b
    def gam():
        v=1
        while True:
            v=v*2+gb()
            if not gb():return v
    while True:
        if not gb():
            d.append(s[p]);p+=1;lwm=0;continue
        if not gb():
            o=gam()
            if lwm==0 and o==2:o=lastoff;n=gam()
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
        if len(d)>limit:raise ValueError('overrun')
    return bytes(d),p-start
OUT='outputs/scene-v19/shaders';shutil.rmtree(OUT,ignore_errors=True);os.makedirs(OUT)
rows=[];bad=[];seen={}
for m in re.finditer(b'D\x00XBC',c):
    i=m.start();done=False
    for N in range(1,40):
        h=i-8-4*N
        us,n=struct.unpack_from('<II',c,h)
        if n!=N or not 32<us<8000000:continue
        sz=struct.unpack_from('<%dI'%N,c,h+8)
        try:
            out=b'';p=i
            for z in sz:
                d,e=aplib(c,p,0x40000);out+=d;p+=z
        except Exception:continue
        if len(out)==us and out[:4]==b'DXBC':
            s=hashlib.sha1(out).hexdigest()[:16];seen.setdefault(s,out)
            rows.append(dict(file_offset=i,header=h,uncompressed=us,blocks=N,sizes=list(sz),sha1=s));done=True;break
    if not done:bad.append(hex(i))
print('blobs',len(rows),'unique',len(seen),'bad',len(bad),bad[:8])
dll=ctypes.WinDLL(r'C:\Windows\System32\D3DCompiler_47.dll')
class B(ctypes.Structure):pass
B._fields_=[]
def dis(b):
    blob=ctypes.c_void_p()
    hr=dll.D3DDisassemble(ctypes.c_char_p(b),ctypes.c_size_t(len(b)),ctypes.c_uint(0),None,ctypes.byref(blob))
    if hr:return None
    vt=ctypes.cast(blob,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    gp=ctypes.WINFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p)(vt[3]);gs=ctypes.WINFUNCTYPE(ctypes.c_size_t,ctypes.c_void_p)(vt[4])
    return ctypes.string_at(gp(blob),gs(blob)).decode('latin1')
idx={};ok=0
for s,b in seen.items():
    open(f'{OUT}/{s}.dxbc','wb').write(b)
    t=dis(b)
    if t is None:continue
    ok+=1;open(f'{OUT}/{s}.asm','w',encoding='latin1').write(t)
    tp=re.search(r'^\s*(vs|ps|gs|cs|hs|ds)_\d_\d',t,re.M)
    names=re.findall(r'^//\s+(?:float\d?(?:x\d)?|int\d?|uint\d?|bool|struct)\s+([A-Za-z_]\w*)(?:\[\d+\])?;',t,re.M)
    cb=re.findall(r'^// cbuffer (\w+)',t,re.M);res=re.findall(r'^// (\w+)\s+(?:sampler|texture|cbuffer)\s',t,re.M)
    idx[s]=dict(type=tp.group(1) if tp else '?',cbuffers=cb,vars=sorted(set(names)),res=res,lines=t.count('\n'),bytes=len(b))
json.dump(rows,open('outputs/scene-v19/shader-blobs.json','w'),indent=0);json.dump(idx,open('outputs/scene-v19/shader-index.json','w'),indent=0)
print('disassembled',ok,collections.Counter(v['type'] for v in idx.values()))
cb=collections.Counter(x for v in idx.values() for x in v['cbuffers']);print(cb.most_common(30))
vs=collections.Counter(x for v in idx.values() for x in v['vars']);print(len(vs));print(' '.join(f'{k}:{n}' for k,n in vs.most_common(220)))
