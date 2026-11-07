import collections,re,struct,math,subprocess
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/audio3.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
names=["ambient_city_lp__windbedlp.ksdf","ambient_city_lp__citybed.ksdf","collision_footstep_player__bootgrittystonewalk19.ksdf","motion_brownie__brownieteeth7.ksdf","collision_weapons_use_blade__swordatckring2.ksdf"]
got=extract(names)
for n,p in got.items():
    b=p.read_bytes();P(n,len(b),b[:128].hex());P("  ascii",[x.decode() for x in re.findall(rb"[A-Za-z_][A-Za-z0-9_ .\-/]{3,}",b[:600])][:14],{m.decode():b.find(m) for m in (b"RIFF",b"WAVE",b"fmt ",b"data",b"OggS",b"vorbis",b"FSB",b"XMA2",b"seek",b"xWMA",b"KSDF",b"SNDF",b"FORK",b"Opus",b"MPEG",b"\xff\xfb") if b.find(m)>=0})
    H=collections.Counter(b[256:]);ent=-sum(v/len(b)*math.log2(v/len(b)) for v in H.values());P("  entropy",round(ent,2))
out.close()
