"""Package a stress APK: swaps the Gorhart scene set, sets its hash, rebuilds, renames the APK."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"; host = root/"work/v19-host"; t = root/"work/v20-town"; keep = root/"work/v22-stress/base"
d = Path(sys.argv[1]); tag = sys.argv[2]; names = ("town_scene.bin","town_materials.bin","town_collision.bin")
if not keep.exists():
    keep.mkdir(parents=True)
    for n in names+("town-receipt.json",): shutil.copy2(t/n, keep/n)
    shutil.copy2(host/"town_identity.h", keep/"town_identity.h")
src = keep if tag=="base" else d
for n in names: shutil.copy2(src/n, t/n)
sha = json.loads((src/"town-receipt.json").read_text())["scene_sha256"]
idf = host/"town_identity.h"; x = idf.read_text(); y = re.sub(r"[0-9a-f]{64}", sha, x); idf.write_text(y); print("identity", y.strip()[:120])
r = subprocess.run(["cmd","/c",r"work\v19-host\build_validate.cmd"],cwd=root); print("build", r.returncode)
if r.returncode: sys.exit(1)
r = subprocess.run([sys.executable,str(host/"package_android.py")],cwd=root,capture_output=True,text=True); print("package", r.returncode, r.stdout[-200:])
apk = root/"outputs/scene-v19/opem-amalur-scene-v0.25-arm64.apk"; out = root/f"work/v22-stress/apk-{tag}.apk"; shutil.copy2(apk,out); print(out.name, out.stat().st_size//1048576,"MB")
