import struct,re,sys,collections,hashlib,os,json
p=sys.argv[1]; d=open(p,'rb').read()
print('file',p,len(d)/1e6,'MB sha256',hashlib.sha256(d).hexdigest()[:16])
pe=struct.unpack_from('<I',d,0x3c)[0]; m,ns,ts=struct.unpack_from('<HHI',d,pe+4); oh=struct.unpack_from('<H',d,pe+20)[0]; o=pe+24
magic=struct.unpack_from('<H',d,o)[0]; print('machine',hex(m),'opt',hex(magic),'timestamp',ts)
imgbase=struct.unpack_from('<Q',d,o+24)[0]; print('imagebase',hex(imgbase),'dllchars',hex(struct.unpack_from('<H',d,o+70)[0]))
nd=struct.unpack_from('<I',d,o+108)[0]; dirs=[struct.unpack_from('<II',d,o+112+8*i) for i in range(nd)]
secs=[]; 
for i in range(ns):
    s=o+oh+40*i; n=d[s:s+8].rstrip(b'\0').decode('latin1'); vs,va,rs,rp=struct.unpack_from('<IIII',d,s+8); ch=struct.unpack_from('<I',d,s+36)[0]; secs.append((n,vs,va,rs,rp,ch)); print(f' sec {n:10} vsize {vs/1e6:8.2f}MB raw {rs/1e6:8.2f}MB chars {ch:#x}')
def off(rva):
    for n,vs,va,rs,rp,ch in secs:
        if va<=rva<va+max(vs,rs): return rva-va+rp
    return None
def cstr(rva):
    x=off(rva); return d[x:d.index(b'\0',x)].decode('latin1')
# imports
imp=collections.OrderedDict(); a=dirs[1][0]; 
if a:
    x=off(a)
    while True:
        ilt,_,_,nm,iat=struct.unpack_from('<IIIII',x and d,x)
        if not nm: break
        name=cstr(nm); fs=[]; t=off(ilt or iat)
        while True:
            v=struct.unpack_from('<Q',d,t)[0]
            if not v: break
            fs.append('ord%d'%(v&0xffff) if v>>63 else cstr((v&0x7fffffff)+2)); t+=8
        imp[name]=fs; x+=20
print('imports',sum(map(len,imp.values())))
for k,v in imp.items(): print(' ',k,len(v), ','.join(v[:6]) if len(v)<=6 else ','.join(v[:6])+',...')
json.dump(imp,open(sys.argv[2]+'/imports.json','w'),indent=0)
# functions via .pdata
if dirs[3][1]:
    x=off(dirs[3][0]); n=dirs[3][1]//12; starts=set(); sizes=[]
    for i in range(n):
        b,e,u=struct.unpack_from('<III',d,x+12*i)
        if u&1: continue
        starts.add(b); sizes.append(e-b)
    sizes.sort(); print('pdata entries',n,'distinct function starts',len(starts),'median size',sizes[len(sizes)//2],'p90',sizes[int(len(sizes)*.9)],'total code MB',sum(sizes)/1e6)
print('debug dir',dirs[6],'export dir',dirs[0],'tls',dirs[9],'loadcfg',dirs[10],'securitysize',dirs[4][1])
# debug/pdb
x=off(dirs[6][0]) if dirs[6][1] else None
if x:
    for i in range(dirs[6][1]//28):
        c=struct.unpack_from('<IIHHIIII',d,x+28*i); 
        if c[3]==2:
            r=d[c[7]:c[7]+c[5]]; print('CV',r[:4],r[24:].split(b'\0')[0])
# strings
strs=set(m.group(0).decode('latin1') for m in re.finditer(rb'[ -~]{5,}',d))
print('ascii strings',len(strs))
rtti=[s for s in strs if s.startswith('.?AV') or s.startswith('.?AU')]; print('rtti type names',len(rtti))
json.dump(sorted(rtti),open(sys.argv[2]+'/rtti.json','w'),indent=0)
paths=sorted(s for s in strs if re.search(r'\.(cpp|c|h|inl)$',s,re.I) or re.search(r'[A-Za-z]:\\.*\\',s))
print('source-like paths',len(paths)); 
json.dump(paths,open(sys.argv[2]+'/paths.json','w'),indent=0)
for s in paths[:40]: print('   ',s[:110])
kw=['Havok','hk','Scaleform','GFx','Bink','FMOD','Wwise','SpeedTree','Lua 5','lua_','Edge','PhysX','SpeedTree','Gamebryo','Umbra','Kynapse','Euphoria','Morpheme','Steam','Denuvo','D3D11','ID3D11','DXGI','XInput','Xbox','Forge','Miles','Vorbis','zlib','lzma','oodle','Oodle','Trinigy','Vision','Rad Game','Beast','Simplygon','Enlighten','Granny','Pix','PerfHUD','NvAPI','AGS','Awesomium']
for k in kw:
    h=[s for s in strs if k in s]
    if h: print(f' kw {k}: {len(h)} e.g. {[x[:70] for x in h[:3]]}')
