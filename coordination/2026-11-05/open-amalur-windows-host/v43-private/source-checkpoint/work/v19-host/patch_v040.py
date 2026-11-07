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
    s=rep(s,"        wq, wt = jworld[jindex[fnames[idx]]] if fnames[idx] in jindex else fworld[idx]\n","        wq, wt = jworld[joint] if cur != 0xffff else fworld[idx]\n")
    s=rep(s,"if err < 1 or fnames[idx] in jindex else","if err < 1 or cur != 0xffff else")
    s=rep(s,"# A part's own skeleton copy can sit apart from the rig; meshes are authored in rig space.","# A part's own skeleton copy can sit apart from the rig, and face joints the rig lacks follow the nearest joint it has; meshes are authored in rig space.")
    return s
edit(R/"work/v20-char/build_character.py",bc)
def ba(s):
    s=rep(s,'wq, wt = sk["world"][sk["index"][fnames[idx]]] if fnames[idx] in sk["index"] else fworld[idx]; iq = conj(wq); it = tuple(-x for x in rot(iq, wt))\n                err = max(abs(it[k] - inv_t[k]) for k in range(3))\n                entries.append((joint, it, iq) if err < 1 or fnames[idx] in sk["index"] else','wq, wt = sk["world"][joint] if cur != 0xffff else fworld[idx]; iq = conj(wq); it = tuple(-x for x in rot(iq, wt))\n                err = max(abs(it[k] - inv_t[k]) for k in range(3))\n                entries.append((joint, it, iq) if err < 1 or cur != 0xffff else')
    return s
edit(R/"work/v20-char/build_actors.py",ba)
print("ok")
