import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/enc_probe.py").read_text()
exec(src[:src.index("encs={")])
encs={int(k):str(v) for k,v in s["encounter"].items()}
sp={int(k):str(v) for k,v in s["simspace"].items() if v=="out_dal_north_03"}
k=next(iter(sp));b=get(f"{k}.space_bxml")
print("head",struct.unpack_from("<16I",b,0))
offs=[o for o in range(0,len(b)-3) if struct.unpack_from("<I",b,o)[0] in encs]
print(len(offs),"aligned4",sum(o%4==0 for o in offs))
def floats(o,span=96):
    r=[]
    for a in range(o-span,o+span,4):
        if a<0:continue
        x,y,z=struct.unpack_from("<3f",b,a)
        if 100<abs(x)<130000 and 100<abs(y)<130000 and -2000<z<30000 and x==x: r.append((a-o,round(x),round(y),round(z)))
    return r
for o in offs[:14]:
    print(o,encs[struct.unpack_from("<I",b,o)[0]],"hex",b[o-48:o+48].hex())
    print("  floats",floats(o)[:6])
# names of strings near
txt=re.findall(rb"[A-Za-z_][A-Za-z0-9_ ]{5,}",b[offs[0]-4000:offs[0]+4000])
print(txt[:60])
# gap structure of offsets
print("gaps",[offs[i+1]-offs[i] for i in range(min(30,len(offs)-1))])
