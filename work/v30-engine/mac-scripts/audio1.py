import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/audio1.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
names=sorted(x for L in listing.values() for x in L if x.endswith("koarsoundbank"));sm=sorted(x for L in listing.values() for x in L if x.endswith("koarsoundmap"));P(len(names),names[:40],sm)
P("in",{k:sum(1 for x in v if x.endswith('koarsoundbank')) for k,v in listing.items()})
got=extract(names[:60]+sm)
sz=[]
for n,p in list(got.items())[:60]:
    b=p.read_bytes();sz.append((len(b),n))
sz.sort();P("sizes",sz[:4],sz[-4:])
for s,n in sz[len(sz)//2:len(sz)//2+2]+sz[-1:]:
    b=got[n].read_bytes();P(n,s,b[:96].hex());P(" ascii",[x.decode() for x in re.findall(rb"[A-Za-z_][A-Za-z0-9_ .\-/]{4,}",b[:4096])][:30]);P(" magic hits",{m.decode():b.find(m) for m in (b"RIFF",b"WAVE",b"BKHD",b"DIDX",b"FSB5",b"FSB4",b"OggS",b"fmt ",b"data",b"XMA2",b"xWMA",b"AKPK",b"FEV1",b"RIFX",b"KBNK") if b.find(m)>=0})
exe=(g/"koa.exe").read_bytes()
P("exe",{m.decode():exe.count(m) for m in (b"FMOD",b"fmod",b"Wwise",b"AkSound",b"XAudio",b"xaudio2",b"Miles",b"XACT",b"koarsoundbank",b"KOAR",b".fsb",b".fev",b"DirectSound",b"dsound",b"xWMA",b"X3DAudio",b"Vorbis",b"vorbis")})
P([x.decode() for x in re.findall(rb"[A-Za-z_:\\/.]{0,30}(?:soundbank|SoundBank|FMOD|Vorbis)[A-Za-z_:\\/. ]{0,50}",exe)][:40])
imp=[x.decode() for x in re.findall(rb"[A-Za-z0-9_]{3,}\.(?:dll|DLL)",exe)];P(sorted(set(imp)))
out.close()
