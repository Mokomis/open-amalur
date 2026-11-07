"""The alpha cutoff of every cutout material in the zone, from its own material file: the word at +36 of materials using an alpha shader. Writes zone_cutoffs.json for build_textures.py."""
import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
z=root/"work/v22-stress/zone-dal";pk=root/"work/v22-stress/live-pack";M=json.loads((z/"zone_materials.json").read_text())["materials"]
shaders={int(k):str(v) for k,v in syms["shader"].items()}
byname={str(v).lower():int(k) for k,v in syms["material"].items()}
want=[(i,m) for i,m in enumerate(M) if m.get("a")]
print("cutout materials",len(want))
def info(mid):
    f=extract([f"{mid}.mat_bxml"]).get(f"{mid}.mat_bxml")
    if not f:return None
    b=f.read_bytes()
    if len(b)<48:return None
    words=set(struct.unpack_from(f"<{len(b)//4}I",b,0));return shaders.get(struct.unpack_from("<I",b,24)[0]),struct.unpack_from("<I",b,36)[0],words
out={};missing=[];seen=collections.Counter()
allids=None
for i,m in want:
    dn=str(syms["texture"].get(str(m["d"]),"")).lower();found=None
    for guess in (re.sub(r"_d\d*$","",dn),re.sub(r"_d\d*$","_01",dn),dn):
        mid=byname.get(guess)
        if mid:
            r=info(mid)
            if r and m["d"] in r[2]:found=(mid,r);break
    if not found:
        pre=re.sub(r"_d\d*$","",dn)[:8]
        for name,mid in byname.items():
            if name.startswith(pre):
                r=info(mid)
                if r and m["d"] in r[2] and (m["a"] in r[2]):found=(mid,r);break
    if found:
        mid,r=found;v=r[1] if 0<r[1]<256 else 128;out[str(i)]=v;seen[(r[0],v)]+=1
    else:missing.append(dn)
print("found",len(out),"missing",missing[:30]);print(seen.most_common(30))
(z/"zone_cutoffs.json").write_text(json.dumps(out))
print("cutoffs",len(out))
