"""Pack text sources written since the v0.14 checkpoint. No game data, saves or keys."""
import re, tarfile
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
OK = {".c", ".h", ".py", ".cmake", ".cmd", ".ps1", ".js", ".xml", ".inc", ".txt", ".md", ".cpp", ".json", ".java", ".sh"}
DIRS = ["work/v19-host", "work/v20-char", "work/v19-rollback", "work/v19-capture", "work/v09-textures"]
ONE = ["work/CURRENT_STATE.txt", "outputs/scene-v19/PROGRESS.txt", "outputs/scene-v19/live-capture-odarath.json", "outputs/scene-v19/lighting-provenance.json", "work/v20-town/town-receipt.json", "OPEN_AMALUR_LOCAL_BUILD_GUIDE.md"]
BAD = re.compile(r"(?i)state-before|\.sav|\.keystore|\.jks|\.pem|\.p12|signing|__pycache__|build-|/build/|symbols\.json|ui_symbols|strings\.json|sky_vs\.txt|save")
n = s = 0
with tarfile.open(root / "work/sync-v023.tar", "w") as t:
    files = [root / p for p in ONE if (root / p).exists()]
    for d in DIRS:
        files += [f for f in (root / d).rglob("*") if f.is_file()]
    for f in files:
        rel = f.relative_to(root).as_posix()
        if f.suffix.lower() in OK and f.stat().st_size < 1_500_000 and not BAD.search(rel):
            t.add(f, arcname=rel); n += 1; s += f.stat().st_size
print("packed", n, "files", s // 1024, "KB")
