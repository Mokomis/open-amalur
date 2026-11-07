from pathlib import Path
R=Path.home()/"Documents/Opem Amalur"
def edit(f,fn):
    s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n");s=fn(s)
    if crlf:s=s.replace("\n","\r\n")
    f.write_bytes(s.encode())
def rep(s,a,b):
    assert a in s,a[:80]
    return s.replace(a,b,1)
def bc(s):
    s=rep(s,'''    if len(tables) != len(surfaces):
        raise SystemExit(f"{fid}: {len(tables)} joint tables for {len(surfaces)} surfaces")
    pal = tables[only]
''','''    # Stray matches can add tables; then the longest is the one that was meant.
    pal = tables[only] if len(tables) == len(surfaces) else max(tables, key=len)
''')
    s=rep(s,"entries.append((joint, it, iq) if err < 1 else (joint, tuple(inv_t), conj(tuple(inv_q))))","entries.append((joint, it, iq) if err < 1 or fnames[idx] in jindex else (joint, tuple(inv_t), conj(tuple(inv_q))))")
    return s
edit(R/"work/v20-char/build_character.py",bc)
def ba(s):
    s=rep(s,'''        if len(tables) != len(mesh["assemblies"]):
            skipped.append((fid, "tables", len(tables), len(mesh["assemblies"]))); continue
''','''        if not tables:
            skipped.append((fid, "no tables")); continue
''')
    s=rep(s,"            pal = tables[ai]\n","            # Stray matches can add tables; then the longest is the one that was meant.\n            pal = tables[ai] if len(tables) == len(mesh[\"assemblies\"]) else max(tables, key=len)\n")
    return s
edit(R/"work/v20-char/build_actors.py",ba)
print("ok")
