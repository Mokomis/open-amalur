"""Read-only comparison of the changed save and Steam cache with the pre-capture backup."""
import datetime, difflib, hashlib
from pathlib import Path
live = Path(r"C:\Program Files (x86)\Steam\userdata\43149042\1041720")
back = Path.home() / "Documents/Opem Amalur/work/v19-capture/state-before/files"
rel = r"remote\autocloud\save\svd_fmt_1_0.sav"
a, b = (back / rel).read_bytes(), (live / rel).read_bytes()
print("backup", len(a), hashlib.sha256(a).hexdigest()[:16], "live", len(b), hashlib.sha256(b).hexdigest()[:16])
print("live modified", datetime.datetime.fromtimestamp((live / rel).stat().st_mtime), "backup copy modified", datetime.datetime.fromtimestamp((back / rel).stat().st_mtime))
print("now", datetime.datetime.now())
n = min(len(a), len(b))
d = [i for i in range(n) if a[i] != b[i]]
print("differing bytes", len(d), "of", n, "first", d[:1], "last", d[-1:])
runs = []
for i in d:
    if runs and i - runs[-1][1] <= 16:
        runs[-1][1] = i
    else:
        runs.append([i, i])
print("regions", len(runs), [(hex(s), e - s + 1) for s, e in runs[:12]])
print("header backup", a[:48].hex())
print("header live  ", b[:48].hex())
for p in sorted((live / r"remote\autocloud\save").glob("*.sav"), key=lambda p: -p.stat().st_mtime)[:3]:
    print(p.name, datetime.datetime.fromtimestamp(p.stat().st_mtime))
A = (back / "remotecache.vdf").read_text(errors="replace").splitlines()
B = (live / "remotecache.vdf").read_text(errors="replace").splitlines()
print("--- remotecache changes")
for l in difflib.unified_diff(A, B, lineterm="", n=0):
    print(l.strip()[:120])
