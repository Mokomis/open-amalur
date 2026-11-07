import struct,re,sys,collections,json
p,out=sys.argv[1],sys.argv[2]; d=open(p,'rb').read()
pe=struct.unpack_from('<I',d,0x3c)[0]; ns=struct.unpack_from('<H',d,pe+6)[0]; oh=struct.unpack_from('<H',d,pe+20)[0]; o=pe+24
imgbase=struct.unpack_from('<I',d,o+28)[0]; ep=struct.unpack_from('<I',d,o+16)[0]; dc=struct.unpack_from('<H',d,o+70)[0]
nd=struct.unpack_from('<I',d,o+92)[0]; dirs=[struct.unpack_from('<II',d,o+96+8*i) for i in range(nd)]
print('imagebase',hex(imgbase),'entry',hex(ep),'dllchars',hex(dc),'LARGEADDRESSAWARE',bool(struct.unpack_from('<H',d,pe+22)[0]&0x20),'ASLR',bool(dc&0x40))
secs=[]
for i in range(ns):
    s=o+oh+40*i; n=d[s:s+8].rstrip(b'\0').decode('latin1'); vs,va,rs,rp=struct.unpack_from('<IIII',d,s+8); secs.append((n,vs,va,rs,rp))
def off(rva):
    for n,vs,va,rs,rp in secs:
        if va<=rva<va+max(vs,rs): return rva-va+rp
def cstr(rva):
    x=off(rva); return d[x:d.index(b'\0',x)].decode('latin1')
imp=collections.OrderedDict(); x=off(dirs[1][0])
while True:
    ilt,_,_,nm,iat=struct.unpack_from('<IIIII',d,x)
    if not nm: break
    fs=[]; t=off(ilt or iat)
    while True:
        v=struct.unpack_from('<I',d,t)[0]
        if not v: break
        fs.append('ord%d'%(v&0xffff) if v>>31 else cstr((v&0x7fffffff)+2)); t+=4
    imp[cstr(nm)]=fs; x+=20
print('import dlls',len(imp),'functions',sum(map(len,imp.values())))
for k,v in imp.items(): print(f'  {k:28}{len(v):5}  '+','.join(v[:5]))
json.dump(imp,open(out+'/imports.json','w'),indent=0)
print('export',dirs[0],'tls',dirs[9],'loadcfg',dirs[10],'cert',dirs[4][1],'clr',dirs[14] if nd>14 else None)
if dirs[0][1]:
    x=off(dirs[0][0]); nn=struct.unpack_from('<I',d,x+24)[0]; print('exports named',nn)
if dirs[6][1]:
    x=off(dirs[6][0])
    for i in range(dirs[6][1]//28):
        c=struct.unpack_from('<IIHHIIII',d,x+28*i)
        if c[3]==2: r=d[c[7]:c[7]+c[5]]; print('CV pdb',r[24:].split(b'\0')[0].decode('latin1'))
# .text function estimate: direct call targets and standard prologues
t=[s for s in secs if s[0]=='.text'][0]; base=t[2]; code=d[t[4]:t[4]+t[3]]; n=len(code); tg=set()
for m in re.finditer(rb'\xe8',code):
    i=m.start()
    if i+5>n: break
    r=struct.unpack_from('<i',code,i+1)[0]; a=i+5+r
    if 0<=a<n: tg.add(a)
pro=set(m.start() for m in re.finditer(rb'(?<=[\xcc\xc3\x90])(?:\x55\x8b\xec|\x53\x8b\xdc|\x83\xec|\x81\xec|\x56\x8b\xf1|\x51\x56|\x56\x57)',code))
# vtable entries: pointers in .rdata into .text
rd=[s for s in secs if s[0]=='.rdata'][0]; rdb=d[rd[4]:rd[4]+rd[3]]; vt=set()
for i in range(0,len(rdb)-4,4):
    v=struct.unpack_from('<I',rdb,i)[0]-imgbase-base
    if 0<=v<n and (v==0 or code[v-1] in (0xcc,0xc3,0xc2,0x90,0xe9,0x00) ): vt.add(v)
print('text MB',round(n/1e6,2),'call targets',len(tg),'prologue hits',len(pro),'rdata code ptrs',len(vt),'union call+rdata',len(tg|vt),'union all',len(tg|vt|pro))
print('sse?', 'addps',code.count(b'\x0f\x58'),'mulps',code.count(b'\x0f\x59'),'x87 fld',code.count(b'\xd9\x05'))
strs=set(m.group(0).decode('latin1') for m in re.finditer(rb'[ -~]{5,}',d))
ws=set(m.group(0).decode('utf-16le') for m in re.finditer(rb'(?:[ -~]\x00){5,}',d))
print('ascii',len(strs),'utf16',len(ws))
rtti=sorted(s for s in strs if s.startswith(('.?AV','.?AU')))
print('rtti names',len(rtti)); json.dump(rtti,open(out+'/rtti.json','w'),indent=0)
ns_=collections.Counter()
for s in rtti:
    q=s[4:].rstrip('@').split('@'); ns_[q[-1] if len(q)>1 else '(global)']+=1
print('top rtti namespaces',ns_.most_common(25))
all_=strs|ws
for k in ['Bullet','btCollision','btDynamics','Bink','Scaleform','GFx','Havok','FMOD','Wwise','SpeedTree','hlsl','HLSL','.fxo','D3D10','D3D11','IDXGI','vs_5_0','ps_5_0','vs_4_0','ps_4_0','CreateFile','GetAsyncKeyState','RawInput','QueryPerformance','steam','Lua 5','lua_State','EdgeAnim','Edge','ThreadPool','Fiber','XAudio','DirectSound','dsound','MSVC','Microsoft Visual C','Visual Studio']:
    h=[s for s in all_ if k in s]
    if h: print(f'  kw {k}: {len(h)} e.g. {[x[:60] for x in sorted(h)[:3]]}')
