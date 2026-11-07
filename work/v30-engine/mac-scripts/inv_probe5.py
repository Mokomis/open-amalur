import re, struct, subprocess, json, collections
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
dest=root/"work/v21-ui/simtype/bins"; dest.mkdir(parents=True,exist_ok=True)
L=(root/"outputs/initial-archive-list.txt").read_text(errors="replace").split()
P=(root/"outputs/patch-archive-list.txt").read_text(errors="replace").split()
print([x for x in L if 'simtype' in x and x.endswith(('.bin','.txt','.bundle','.simtype_bxml')) and 'duplicate' not in x][:30])
sim=[x for x in L if x.endswith('.simtype_bxml') and 'duplicate' not in x]
print(sim[:30])
bins=[x for x in L if x.endswith('.bin') and 'duplicate' not in x and not x.startswith(('symbol_table','english','german','french','italian','spanish','japanese','russian'))]
print(len(bins),[x for x in bins if not re.search(r'_init|\d',x)][:60])
print('patch simtype-related',[x for x in P if 'simtype' in x and not x.endswith('visual_data_bundle')][:12])
pick=[x for x in sim[:6]]+[x for x in bins if re.search(r'simtype|item|inventory|loot|^gameplay|stats|balance|weapon|armor|budget',x) and not x.startswith('symbol')][:24]
subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data/initial_0.pak"),"unpack",str(dest),*pick],cwd=g/"modding",capture_output=True,timeout=120)
pat=[struct.pack("<I",252852),struct.pack("<I",125871)]
for p in sorted(dest.iterdir(),key=lambda p:-p.stat().st_size)[:30]:
    b=p.read_bytes()
    print(p.name,len(b),b[:16].hex(),'hits',[b.find(x) for x in pat])
# Enumerate whole archives for files that contain the id, among moderate-size non-bundle types.
ext=collections.Counter(x.rsplit('.',1)[-1] for x in L); print(ext.most_common(70))
