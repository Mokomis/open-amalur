"""Survey archive contents for what a playable character needs."""
import collections, re
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
all_names = {}
for n in ("DATA", "initial", "patch"):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    names = [x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip()]
    all_names[n] = names
    c = collections.Counter(Path(x).suffix for x in names)
    print(n, len(names), c.most_common(40))
game = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\data")
print("paks", [(p.name, p.stat().st_size // 1048576) for p in sorted(game.glob("*.pak"))][:40])
pat = re.compile(r"anim|skel|rig|hkx|havok|player|hero|race|male|female|human|dokkalfar|almain|varani|ljosalfar|armor|actor|motion|locomot|controller|behav", re.I)
for n, names in all_names.items():
    hits = [x for x in names if pat.search(x) and not re.fullmatch(r"\d+\.\w+", x)]
    print("---", n, "named hits", len(hits))
    print(hits[:70])
