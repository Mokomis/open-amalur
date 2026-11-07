"""Build assets/fx/fx.bin: the zone's placed effects from each space's 60-byte records at 0xd0, their emitter and particle tasks, and textures.
What each channel means was inferred from values across many effects (see the names below), not from game code. Lights and sounds in a cluster are not included here.
Usage: build_fx.py <out file>. Uses OA_ZONE."""
import collections,json,os,re,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent))
from fx_common import load_tasks,channels,cluster
OUTFILE=Path(sys.argv[1]);OUTFILE.parent.mkdir(parents=True,exist_ok=True)
root=Path.home()/"Documents/Opem Amalur"
source=(root/"work/v20-char/build_town.py").read_text()
os.environ["OA_TEXTURE_LIMIT"]="256"
_argv=sys.argv;sys.argv=["build_town.py","1",str(OUTFILE.parent)]
exec(source[:source.index("# Terrain sampler")])
sys.argv=_argv
if "decode_best" not in globals():
    a=source.index("def decode_best");b=source.index("def load_texture");exec(source[a:b])
ZONE=os.environ.get("OA_ZONE","dal")
C={int(k):str(v) for k,v in syms["cluster"].items()};T={int(k):str(v) for k,v in syms["task"].items()};Mat={int(k):str(v) for k,v in syms["material"].items()};Tex={int(k):str(v) for k,v in syms["texture"].items()}
rec=load_tasks()
spaces=[int(k) for k,v in syms["simspace"].items() if re.match(rf"out_{ZONE}_",str(v))]
places=[];skipped=collections.Counter()
for sid in spaces:
    f=extract([f"{sid}.space_bxml"]).get(f"{sid}.space_bxml")
    if f is None:continue
    d=f.read_bytes();pl=struct.unpack_from("<I",d,0)[0];b=d[8:8+pl]
    p,c=struct.unpack_from("<II",b,0xd0)
    for i in range(c):
        r=b[p-8+i*60:p-8+(i+1)*60];cid=struct.unpack_from("<I",r,52)[0]
        if cid not in C:skipped["no cluster"]+=1;continue
        v=struct.unpack_from("<12f",r,4);places.append((cid,v[0:3],v[4:8]))
print("placed clusters",len(places),collections.Counter(C[p[0]] for p in places).most_common(12),skipped)
files=extract([f"{k}.fxcluster_bxml" for k in {p[0] for p in places}])
def floats(ch,key,n):
    if key not in ch or len(ch[key][1])<n*4:return None
    return struct.unpack_from(f"<{n}f",ch[key][1])
def ints(ch,key,n):
    if key not in ch or len(ch[key][1])<n*4:return None
    return struct.unpack_from(f"<{n}i",ch[key][1])
SIZE=struct.pack("<I",0xec5a12)
def size_curve(q):
    i=q.find(SIZE)
    if i<0:return None
    # Curve header: name, three zero words, 1, 0, 1.0, key count, then time and value pairs with a tangent word.
    n=struct.unpack_from("<I",q,i+28)[0] if i+32<=len(q) else 0
    for o in range(i+4,min(i+60,len(q)-20),1):
        if struct.unpack_from("<I",q,o)[0]==2 and struct.unpack_from("<f",q,o+4)[0]==0 and struct.unpack_from("<f",q,o+12)[0]==0 and struct.unpack_from("<f",q,o+16)[0]==1:
            return struct.unpack_from("<f",q,o+8)[0],struct.unpack_from("<f",q,o+20)[0]
    return None
def gradient(p):
    # material, four hashes, a one, a zero, 1.0, then colour keys as time and ARGB, then alpha keys as time and value.
    o=32;nc=struct.unpack_from("<I",p,o)[0];o+=4
    if not 0<nc<=8:return None
    cols=[]
    for i in range(nc):
        t,w=struct.unpack_from("<fI",p,o);o+=8;cols.append((min(t,1.0),((w>>16)&255)/255,((w>>8)&255)/255,(w&255)/255))
    na=struct.unpack_from("<I",p,o)[0];o+=4
    if not 0<na<=8:return None
    al=[]
    for i in range(na):
        t,a=struct.unpack_from("<2f",p,o);o+=8;al.append((min(t,1.0),a))
    return cols,al
types=[];type_of={};textures=[];tex_of={};stats=collections.Counter()
def texture(mid):
    mf=extract([f"{mid}.mat_bxml"]).get(f"{mid}.mat_bxml")
    if mf is None:return None
    data=mf.read_bytes();refs=[]
    for i in range(0,len(data)-3,4):
        v=struct.unpack_from("<I",data,i)[0]
        if v in Tex and v not in refs:refs.append(v)
    if not refs:return None
    key=tuple(refs[:2])
    if key in tex_of:return tex_of[key]
    best=decode_best(refs[0])
    if best is None:return None
    w,h,rgba=best
    im=Image.frombytes("RGBA",(w,h),bytes(rgba))
    if len(refs)>1 and Tex[refs[1]].lower().endswith("_a"):
        m=decode_best(refs[1])
        if m:im.putalpha(Image.frombytes("RGBA",(m[0],m[1]),bytes(m[2])).split()[1].resize((w,h)))
    if max(w,h)>256:im=im.resize((min(w,256),min(h,256)),Image.LANCZOS)
    tex_of[key]=len(textures);textures.append(im);return tex_of[key]
def make_type(e,pk):
    q=rec.get(pk)
    if q is None:stats["no particle task"]+=1;return None
    ph=channels(q);ch=channels(rec[e]) if e in rec else {}
    if 0xc15a4d not in ph:stats["no material channel"]+=1;return None
    at=q.find(struct.pack("<II",0xcab781,0xc15a4d))
    if at<0:stats["no material channel"]+=1;return None
    mp=q[at+28:];mid=struct.unpack_from("<I",mp,0)[0];mn=Mat.get(mid,"")
    try:g=gradient(mp)
    except struct.error:g=None
    if g is None:stats["no gradient"]+=1;return None
    tx=texture(mid)
    if tx is None:stats["no texture"]+=1;return None
    s=size_curve(q)
    if s is None:stats["no size"]+=1;return None
    period=ints(ch,0x8f5a8,2) or (0,0)
    burst=ints(ch,0x1213fe6,1) if 0x1213fe6 in ch and ch[0x1213fe6][0]==0x132c1a2 else (1,)
    box=floats(ch,0xa23835,3) or (0,0,0);off=floats(ch,0x16fd0a,3) or (0,0,0);rnd=floats(ch,0xaa49cd,3) or (0,0,0)
    dirn=floats(ch,0xef2d2c,3) or (0,0,1);speed=(floats(ch,0x7a2a92,1) or floats(ph,0x11c0f9f,1) or (0,))[0]
    l=np.array(dirn);n=float(np.linalg.norm(l));l=l/n if n>1e-5 else np.array((0,0,1.0))
    life=ints(ph,0x886fdd,2) or (1000,0)
    cell=struct.unpack_from("<4f2I",ph[0x486ba9][1]) if 0x486ba9 in ph and len(ph[0x486ba9][1])>=24 else (0,1,0,1,1,1)
    spin=ints(ph,0xdf6b8,2) or (0,0)
    t=[tx,1.0 if "_add" in mn else 0.0,period[0]/1000,period[1]/1000,max(burst[0],1),*box,*off,*(l*speed),*rnd,life[0]/1000,life[1]/1000,float(s[0]),float(s[1]),float(max(cell[4],1)),float(max(cell[5],1)),float(spin[0]),float(spin[1])]
    cols,al=g
    cols=(cols+[cols[-1]]*4)[:4];al=(al+[al[-1]]*6)[:6]
    for c_ in cols:t+=list(c_)
    for a_ in al:t+=list(a_)
    assert len(t)==25+16+12,len(t)
    stats["types"]+=1;return t
out_places=[]
for cid,pos,q in places:
    b=files.get(f"{cid}.fxcluster_bxml")
    if b is None:continue
    kids,_=cluster(b.read_bytes())
    for kind,e,pk in kids:
        if kind!=0x6ed2b0:stats["other child"]+=1;continue
        key=(e,pk)
        if key not in type_of:
            t=make_type(e,pk);type_of[key]=len(types) if t else -1
            if t:types.append(t)
        if type_of[key]>=0:out_places.append((*pos,float(type_of[key]),*q))
print("emitters placed",len(out_places),"types",len(types),"textures",len(textures),stats)
blob=bytearray(b"OAFX0001"+struct.pack("<IIII",len(textures),len(types),len(out_places),53))
for im in textures:
    im=im.convert("RGBA");blob+=struct.pack("<II",*im.size)+im.tobytes()
for t in types:blob+=struct.pack("<53f",*t)
for p in out_places:blob+=struct.pack("<8f",*p)
OUTFILE.write_bytes(blob);print("bytes",len(blob),OUTFILE)
for i,t in enumerate(types[:8]):print(i,[round(x,2) for x in t[:25]])
