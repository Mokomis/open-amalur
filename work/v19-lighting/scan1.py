import struct,glob,os,re,math,collections
import xml.etree.ElementTree as ET
R='work/v19-inputs/initial_0.pak/'
# xml schema census
fields=collections.Counter();keys=collections.Counter();flags=collections.Counter();cubes=collections.Counter();xmlc=0;binc=[]
presets={}
for f in glob.glob(R+'*.koalighting'):
    b=open(f,'rb').read()
    if not b.startswith(b'<?xml'):binc.append((os.path.basename(f),len(b)));continue
    xmlc+=1;t=ET.fromstring(b);o=t.find('DataObject');s=o.find("value[@name='settings']")
    if s is None:keys['<none>']+=1;continue
    for k in s:
        keys[k.attrib['name']]+=1
        for v in k:fields[(v.attrib['type'],v.attrib['name'])]+=1
    fl=o.find("value[@name='flags']");flags[fl.text if fl is not None else None]+=1
    presets[os.path.basename(f)]=o
print('xml',xmlc,'bin',binc);print(keys);print(flags)
for k,v in fields.most_common():print(v,k)
# find any preset's direction vector / floats in compiled files
def fl(x):return struct.pack('<f',float(x))
needles={}
for n,o in presets.items():
    d=o.find("value[@name='directional_light_direction']")
    if d is not None and d.text:
        v=d.text.split()
        needles[fl(v[0])+fl(v[1])+fl(v[2])]=n
print('needles',len(needles))
hits=collections.Counter()
scan=glob.glob(R+'*.sky_bxml')+glob.glob(R+'*.bin')+glob.glob('work/scene-inputs-v07/DATA_0.pak/*bxml')
for f in scan:
    b=open(f,'rb').read()
    for nd,n in needles.items():
        i=b.find(nd)
        if i>=0:print('HIT',os.path.basename(f),hex(i),n);hits[n]+=1
print('scanned',len(scan),'hits',sum(hits.values()))
# sky census
sz=collections.Counter(os.path.getsize(f) for f in glob.glob(R+'*.sky_bxml'));print('sky sizes',sz.most_common(8))
# region float layout
b=open('work/scene-inputs-v07/DATA_0.pak/524912.region_bxml','rb').read();pl,fx=struct.unpack('<II',b[:8]);p=b[8:8+pl]
print('fixups',[hex(struct.unpack_from('<I',b,8+pl+i)[0]) for i in range(0,min(fx,160),4)])
for off in range(0,pl-12,4):
    a=struct.unpack_from('<3f',p,off)
    if all(math.isfinite(x) for x in a) and abs(math.sqrt(sum(x*x for x in a))-1)<1e-4 and all(abs(x)<1 and abs(x)>1e-3 for x in a):print('unit',hex(off),a)
print(p[0x50:0xb0].hex())
