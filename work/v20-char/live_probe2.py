import collections,json,re,struct,subprocess,sys,zlib,math
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"; inp=root/"work/v20-inputs"
sys.path[:0]=[str(root/"work/v19-lighting")]
import decode_scene_lighting as D
s=json.loads((inp/"symbols.json").read_text())
vb=(inp/"DATA_0.pak/431658.veggie_streamable_bin").read_bytes()
n=struct.unpack_from("<I",vb,0)[0];print("n",n,struct.unpack_from("<6I",vb,0))
# Walk blocks: u32 raw, u32 comp, data
out=bytearray();o=4;blocks=0;errs=0
while o+8<=len(vb) and blocks<200000:
    a,c=struct.unpack_from("<II",vb,o)
    if vb[o+8:o+10]==b"\x78\x9c" or vb[o+8:o+9]==b"\x78":
        try:
            d=zlib.decompress(vb[o+8:o+8+c]);out+=d;o+=8+c;blocks+=1;continue
        except Exception as e:
            pass
    # try offset 12-byte headers
    a,b_,c=struct.unpack_from("<III",vb,o)
    if vb[o+12:o+13]==b"\x78":
        try:
            d=zlib.decompress(vb[o+12:o+12+c]);out+=d;o+=12+c;blocks+=1;continue
        except Exception: pass
    errs+=1;break
print("blocks",blocks,"raw",len(out),"stopped at",o,"of",len(vb),vb[o:o+24].hex())
if len(out)<1000:
    # fall back: scan for every zlib header using decompressobj
    pos=0;out=bytearray();cnt=0
    while True:
        i=vb.find(b"\x78\x9c",pos)
        if i<0:break
        try:
            do=zlib.decompressobj();d=do.decompress(vb[i:i+200000]);out+=d;pos=i+len(vb[i:i+200000])-len(do.unused_data);cnt+=1
        except Exception: pos=i+2
    print("scan blocks",cnt,"raw",len(out))
d=bytes(out);(root/"work/v21-ui/live/veggie.raw").write_bytes(d)
print(d[:256].hex())
words=[struct.unpack_from("<I",d,i)[0] for i in range(0,min(len(d),400),4)];print(words[:60])
fl=[round(struct.unpack_from("<f",d,i)[0],2) for i in range(0,min(len(d),400),4)];print(fl[:60])
ids={}
for c,mp in s.items():
    if isinstance(mp,dict):
        for k,nm in mp.items(): ids.setdefault(int(k),f"{c}:{nm}")
hits=collections.Counter()
for o2 in range(0,len(d)-4,4):
    w=struct.unpack_from("<I",d,o2)[0]
    if w>1000 and w in ids and ids[w].split(":")[0] in("fab","material","simtype","texture"): hits[ids[w]]+=1
print("id hits",hits.most_common(30))
# Look for repeated struct stride by float autocorrelation in the raw data
samp=np.frombuffer(d[:2000000],'<f4') if False else None
t=(inp/"DATA_0.pak/431658.terrain_bin").read_bytes()
print("terrain_bin head",struct.unpack_from("<8I",t,0),struct.unpack_from("<f",t,20))
for nm in ("veggie","Veggie","flora"):
    print(nm,[str(v) for v in s["material"].values() if nm.lower() in str(v).lower()][:30])
# Lights per space
tot=0;rows=[]
for k,v in s["simspace"].items():
    if not re.match(r"out_dal_(north|south|west|tran)_",str(v)):continue
    p=None
    for a in("patch_0.pak","initial_0.pak","DATA_0.pak"):
        q=inp/a/f"{k}.space_bxml"
        if q.exists():p=q;break
    if not p:continue
    try:
        L=D.decode_space_lights(p.read_bytes());items=L if isinstance(L,list) else L.get("lights",L)
        rows.append((str(v),len(items)));tot+=len(items)
        if rows and len(rows)==1:print("light sample",items[:1] if isinstance(items,list) else list(items)[:3])
    except Exception as e:rows.append((str(v),repr(e)[:50]))
print("lights",tot,rows[:24])
