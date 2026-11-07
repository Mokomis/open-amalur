"""Summarize a captured frame: contexts, passes, render targets and constant buffers."""
import collections, json, struct, sys
from pathlib import Path

run = Path(sys.argv[1])
f = json.loads((run / "frame.json").read_text())
blob = (run / "frame.bin").read_bytes()
ev, tex = f["events"], f["textures"]
print("events", len(ev), "draws", f["draws"])
print("by ctx", collections.Counter(e.get("ctx") for e in ev).most_common(8))
print("kinds", collections.Counter(e["e"] for e in ev).most_common())
print("threads", collections.Counter(e.get("tid") for e in ev).most_common(8))
print("exec/finish", [(e["e"], e.get("ctx"), e.get("list")) for e in ev if e["e"] in ("exec", "finish")][:12])

# Per-context state replay: which RT, PS and CBs each draw used.
state = collections.defaultdict(lambda: {"rt": (), "ps": None, "pscb": {}, "vscb": {}, "srv": {}})
passes = []
def rtname(rt):
    out = []
    for r in rt:
        t = tex.get(r) if r else None
        out.append("%dx%d/f%s" % (t.get("w"), t.get("h"), t.get("fmt")) if t and "w" in t else str(r))
    return tuple(out)
slots = collections.Counter()
for e in ev:
    s = state[e.get("ctx")]
    k = e["e"]
    if k == "rt": s["rt"] = tuple(e["res"])
    elif k == "ps": s["ps"] = e["id"]
    elif k in ("pscb", "vscb"):
        for i, b in enumerate(e["bufs"]):
            s[k][e["start"] + i] = b
            if b: slots[(k, e["start"] + i, b["size"], b["buf"])] += 1
    elif k == "srv":
        for i, r in enumerate(e["res"]): s["srv"][e["start"] + i] = r
    elif k.startswith("draw"):
        key = (e.get("ctx"), s["rt"], s["ps"])
        if passes and passes[-1]["key"] == key: passes[-1]["n"] += 1
        else:
            passes.append({"key": key, "n": 1, "rt": rtname(s["rt"]), "ps": s["ps"], "cb": {i: (b["size"], b["buf"]) for i, b in s["pscb"].items() if b},
                           "srv": {i: rtname((r,))[0] for i, r in s["srv"].items() if r}})
print("pass runs", len(passes))
last = passes[-45:]
for p in last:
    print(p["n"], "rt", p["rt"], "ps", p["ps"], "cb", p["cb"], "srv", p["srv"])
print("--- CB slots")
for (st, slot, size, buf), n in sorted(slots.items(), key=lambda kv: (kv[0][0], kv[0][1], -kv[1]))[:50]:
    print(st, slot, size, buf, n)
print("--- CB data sources", collections.Counter((e["via"], e["size"]) for e in ev if e["e"] == "cbdata").most_common(25))
