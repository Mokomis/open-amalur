import re,struct,json,collections
from pathlib import Path
p=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_actors.py").read_text()
source=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(source[:source.index("SKELS = {}")])
sim={str(v):int(k) for k,v in syms["simtype"].items()}
fab={str(v).lower():int(k) for k,v in syms["fab"].items()}
anim=sorted(str(v) for v in syms["animation"].values())
for nm,pat in (("ettin_brute","ettin"),("giantrat_a","rat"),("giantspider_venomspitter","spider"),("sprite_champion_of_flame","sprite")):
    i=sim[nm];d=extract([f"{i}.bundle"])[f"{i}.bundle"].read_bytes();ids=list(dict.fromkeys(struct.unpack_from(f"<{(len(d)-16)//4}I",d,16)))
    print("==",nm,"rag",[syms["ragdoll"][str(v)] for v in ids if str(v) in syms["ragdoll"]])
    for v in ids:
        if "fab_visual_data_streamable_bin" in files_by_id.get(v,[]):
            f=extract([f"{v}.fab_bxml"]).get(f"{v}.fab_bxml")
            try:
                J=skeleton(f.read_bytes())[0]; pal=len(palette(f.read_bytes(),J))
            except Exception as e: J=repr(e)[:30];pal=None
            print("  fab",v,syms["fab"].get(str(v)),"joints",J,"palette",pal)
    cl=[a for a in anim if re.search(pat,a,re.I) and re.search("idle",a,re.I)][:8];print("  idle clips",cl)
    ci=next(int(k) for k,v in syms["animation"].items() if str(v) in cl) if cl else None
    if ci:
        b=extract([f"{ci}.anm_bxml"]).get(f"{ci}.anm_bxml")
        if b: print("  clip joints",struct.unpack_from("<H",b.read_bytes(),8+0xe)[0])
print([k for k in fab if re.search("ettin|rat_|spider",k)][:20])
