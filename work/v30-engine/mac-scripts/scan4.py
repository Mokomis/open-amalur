import struct,glob,os,json,collections
import xml.etree.ElementTree as ET
def load(f):
    b=open(f,'rb').read();pl,fx=struct.unpack('<II',b[:8]);p=b[8:8+pl]
    return p,{struct.unpack_from('<I',b,8+pl+i)[0] for i in range(0,fx,4)}
p,fxs=load('work/scene-inputs-v07/DATA_0.pak/524912.region_bxml')
offs=[o for o in sorted(fxs) if o<0x400 and struct.unpack_from('<I',p,o)[0]==0x33cc]
print('env ptr root slot',[hex(o) for o in offs]);ER=offs[0]
print('around',[hex(x) for x in struct.unpack_from('<8I',p,ER-16)])
regs={}
for f in glob.glob('work/v19-inputs/DATA_0.pak/*.region_bxml')+glob.glob('work/v19-inputs/patch_0.pak/*.region_bxml'):
    try:
        p,fxs=load(f);ptr,c=struct.unpack_from('<II',p,ER)
    except Exception as e:print('ERR',f,e);continue
    regs[f]=(p,ptr-8,c,ER in fxs)
print('regions',len(regs),'count dist',collections.Counter(v[2] for v in regs.values()),'slot is fixup',collections.Counter(v[3] for v in regs.values()))
good={f:v for f,v in regs.items() if v[3] and v[2]>=1 and v[1]+0x570<=len(v[0])}
print('good',len(good))
M=[('fog_color',0x240,'c'),('fog_start',0x280,'f'),('fog_density',0x290,'f'),('post_bloom_scale',0x2a0,'f'),('post_bloom_cutoff',0x2b0,'f'),('post_brightness',0x2c0,'f'),('post_focal_distance',0x300,'f'),('post_focal_radius',0x310,'f'),('post_motion_blur',0x320,'f'),('bloom_exposure_level',0x330,'f'),('bloom_min_luminance',0x340,'f'),('bloom_max_luminance',0x350,'f'),('bloom_strength',0x360,'f')]
XML={}
K=['Midnight','Dawn','Noon','Dusk']
for f in glob.glob('work/v19-inputs/initial_0.pak/*.koalighting'):
    b=open(f,'rb').read()
    if not b.startswith(b'<?xml'):continue
    o=ET.fromstring(b).find('DataObject');s=o.find("value[@name='settings']")
    if s is None:continue
    d={}
    for k in s:
        for v in k:
            t=v.attrib['type'];n=v.attrib['name']
            if t=='float':d[(k.attrib['name'],n)]=float(v.text)
            elif t.endswith('HdrColorRgb'):d[(k.attrib['name'],n)]=[float(c.text) for c in v]
    XML[os.path.basename(f)]=d
best=[]
for f,(p,o,c,_) in good.items():
    r=[]
    for n,d in XML.items():
        s=t=0
        for ki,k in enumerate(K):
            for name,off,ty in M:
                if (k,name) not in d:continue
                t+=1
                x=d[(k,name)]
                if ty=='f':
                    y=struct.unpack_from('<f',p,o+off+4*ki)[0];s+=abs(x-y)<1e-5*(abs(x)+1)
                else:
                    y=struct.unpack_from('<3f',p,o+off+16*ki);s+=all(abs(a-b)<1e-5 for a,b in zip(x,y))
        if t:r.append((s/t,s,t,n))
    r.sort(reverse=True);best.append((r[0],os.path.basename(f),r[1][3] if len(r)>1 else ''))
best.sort(reverse=True)
print('exact matches',sum(1 for b in best if b[0][0]==1),'>=0.9',sum(1 for b in best if b[0][0]>=.9),'of',len(best))
for b in best[:25]:print(b)
sh=[b for b in best if b[1]=='524912.region_bxml'];print('shop',sh)
print(json.dumps({'sample':[(os.path.basename(f),hex(v[1]),v[2]) for f,v in list(good.items())[:5]]}))
