"""Copy or compare the game's save folder. Usage: state_manifest.py backup|compare <folder>"""
from pathlib import Path
import hashlib, json, shutil, sys

SAVES = Path(r"C:\Program Files (x86)\Steam\userdata\43149042\1041720")


def hashes(base):
    return {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(base.rglob("*")) if p.is_file()}


mode, folder = sys.argv[1], Path(sys.argv[2])
if mode == "backup":
    if folder.exists():
        raise SystemExit("Refusing to overwrite " + str(folder))
    shutil.copytree(SAVES, folder / "files")
    current = hashes(SAVES)
    if hashes(folder / "files") != current:
        raise SystemExit("Backup copy does not match the save folder")
    (folder / "manifest.json").write_text(json.dumps(current, indent=1))
    print("backed up", len(current), "files; copy verified")
else:
    before, after = json.loads((folder / "manifest.json").read_text()), hashes(SAVES)
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    print("files", len(after), "changed", changed)
