import struct,glob,os,json,collections,math
import xml.etree.ElementTree as ET
ER=0xf0;K=['Midnight','Dawn','Noon','Dusk']
def load(f):
    b=open(f,'rb').read();pl,fx=struct.unpack('<II',b[:8]);p=b[8:8+pl]
    return p,{struct.unpack_from('<I',b,8+pl+i)[0] for i in range(0,fx,4)}
recs={}
for f in glob.glob('work/v19-inputs/DATA_0.pak/*.region_bxml')+glob.glob('work/v19-inputs/patch_0.pak/*.region_bxml'):
    try:p,fxs=load(f);ptr,c=struct.unpack_from('<II',p,ER)
    except Exception:continue
    recs[f]=(p[ptr-8:ptr-8+0x570],p,fxs)
XML={}
for f in glob.glob('work/v19-inputs/initial_0.pak/*.koalighting'):
    b=open(f,'rb').read()
    if not b.startswith(b'<?xml'):continue
    o=ET.fromstring(b).find('DataObject');s=o.find("value[@name='settings']")
    if s is None:continue
    d={}
    for k in s:
        for v in k:
            t=v.attrib['type'];n=v.attrib['name'];kn=k.attrib['name']
            if t=='float':d[(kn,n)]=float(v.text)
            elif t.endswith('HdrColorRgb'):
                for c in v:d[(kn,n+'.'+c.attrib['name'])]=float(c.text)
            elif t=='float4':
                for i,x in enumerate(v.text.split()):d[(kn,n+'.%d'%i)]=float(x)
            else:d[(kn,n)]=v.text
    dd=o.find("value[@name='directional_light_direction']")
    if dd is not None and dd.text:
        for i,x in enumerate(dd.text.split()):d[('',"dir.%d"%i)]=float(x)
    fl=o.find("value[@name='flags']");d[('','flags')]=int(fl.text) if fl is not None else None
    XML[os.path.basename(f)]=d
# Solve: for every numeric XML field+key, offsets in record where value matches, intersect across all region-preset pairs chosen by anchor score
anchor=[('fog_start',0x280),('fog_density',0x290),('post_bloom_scale',0x2a0),('post_bloom_cutoff',0x2b0),('bloom_exposure_level',0x330),('bloom_strength',0x360)]
pairs=[]
for f,(r,_,_) in recs.items():
    best=None
    for n,d in XML.items():
        s=0
        for ki,k in enumerate(K):
            for nm,off in anchor:
                if (k,nm) in d and abs(struct.unpack_from('<f',r,off+4*ki)[0]-d[(k,nm)])<1e-5*(abs(d[(k,nm)])+1):s+=1
        if best is None or s>best[0]:best=(s,n)
    if best and best[0]==24:pairs.append((f,best[1]))
print('anchor pairs',len(pairs),'distinct presets',len({n for _,n in pairs}))
cand={}
nfl=0x570//4
for f,n in pairs:
    r=recs[f][0];vals=struct.unpack('<%df'%nfl,r);d=XML[n]
    for key,x in d.items():
        if not isinstance(x,float):continue
        s={4*i for i,y in enumerate(vals) if abs(y-x)<=1e-5*(abs(x)+1e-3)}
        cand[key]=cand[key]&s if key in cand else s
for key in sorted(cand,key=lambda k:(min(cand[k]) if cand[k] else 9999,k)):
    print(key,[hex(x) for x in sorted(cand[key])][:6])
# full-field distinction for shop
sf=[f for f in recs if f.endswith('524912.region_bxml')]
print('shop files',sf)
r=recs[sf[0]][0];vals=struct.unpack('<%df'%nfl,r)
for n in sorted(XML):
    if 'gorhart' in n or 'dok' in n:
        d=XML[n];mis=[]
        ok=0
        for key,x in d.items():
            if isinstance(x,float):
                if cand.get(key) and any(abs(vals[o//4]-x)<=1e-5*(abs(x)+1e-3) for o in cand[key]):ok+=1
                elif cand.get(key):mis.append((key,x))
        print(n,'ok',ok,'mis',mis[:10],'flags',d.get(('','flags')))
json.dump({str(k):sorted(v) for k,v in cand.items()},open('outputs/scene-v19/field-solve-1.json','w'),indent=0)
