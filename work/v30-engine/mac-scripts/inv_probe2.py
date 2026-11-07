import re, struct, subprocess
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
ref = root / "references"
for rp in ["Doezer--KOARR-Modding","Kender2--amalur","DevCortez--KoaModFramework","ZucchiniZap--AmalurBxmlConverter","mburbea--ModelSwapper"]:
    d = ref/rp
    hits = [p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file() and ".git" not in p.parts and "obj" not in p.parts and "bin" not in p.parts and p.suffix.lower() in (".md",".txt",".cs",".py",".cpp",".h",".json",".xml",".csv") ]
    print("##", rp, len(hits), hits[:14])
    for f in hits:
        try: t=(d/f).read_text(errors="replace")
        except: continue
        if re.search(r"simtype_init|simtype_bxml|SimType", t):
            for m in list(re.finditer(r".{0,90}(simtype_init|simtype_bxml).{0,120}", t))[:3]: print("   ",f,":",m.group(0).strip()[:230])
dest = root/"work/v21-ui/simtype"; dest.mkdir(parents=True, exist_ok=True)
for pak,names in (("initial_0",["simtype_init.bin","symbol_table_simtype.bin"]),("patch_0",["simtype_init.bin"])):
    d=dest/pak; d.mkdir(exist_ok=True)
    subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data"/f"{pak}.pak"),"unpack",str(d),*names],cwd=g/"modding",capture_output=True,timeout=120)
    for n in names:
        p=d/n
        print(pak,n,p.exists() and p.stat().st_size)
L=(root/"outputs/initial-archive-list.txt").read_text(errors="replace").split()
print([x for x in L if "_init" in x][:30])
print([x for x in L if x.endswith((".bxml",".bin")) and re.search("item|inventory|loot|weapon|armor|buff",x)][:20])
for pak in ("patch_0","initial_0"):
    p=dest/pak/"simtype_init.bin"
    if p.exists():
        b=p.read_bytes()
        print(pak,"head",b[:64].hex())
        for tid in (252852,125871,206059,1327249):
            pat=struct.pack("<I",tid);i=b.find(pat);print(tid,"at",i,b[max(0,i-16):i+48].hex() if i>=0 else "")
