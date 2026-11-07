from pathlib import Path
R=Path.home()/"Documents/Opem Amalur"
def edit(f,fn):
    s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n");s=fn(s)
    if crlf:s=s.replace("\n","\r\n")
    f.write_bytes(s.encode())
def rep(s,a,b):
    assert a in s,a[:80]
    return s.replace(a,b,1)
PAL='''def palettes(fb, joints):
    """Every joint table in file order. There is one per surface, lower detail copies included."""
    tables, start = [], 0
    while start < len(fb) - 52:
        chain, at = [], start
        while at + 52 <= len(fb):
            s = struct.unpack_from("<3f", fb, at + 32)
            q = struct.unpack_from("<4f", fb, at + 16)
            count, idx = struct.unpack_from("<II", fb, at + 44)
            if not all(abs(x - 1) < .02 for x in s) or abs(sum(x * x for x in q) - 1) > .02 or idx >= joints or count > 300:
                break
            chain.append((idx, struct.unpack_from("<3f", fb, at), q))
            at += 52
        if chain:
            tables.append(chain); start = at
        else:
            start += 1
    return tables


'''
def bc(s):
    s=rep(s,"# The head keeps each surface apart, because skin and eyes have their own materials.\nfor fid, label, only in [(f, l, None) if l != \"head\" else (f, l, a) for f, l in PARTS for a in (assemblies_of(f) if l == \"head\" else [None])]:","# Each surface is its own part: it has its own joint table and its own material.\nfor fid, label, only in [(f, l, a) for f, l in PARTS for a in assemblies_of(f)]:")
    s=rep(s,"    pal = palette(fb, n)\n","    tables = palettes(fb, n)\n    surfaces = amalur_mesh.parse_file(fab[f\"{fid}.fab_visual_data_streamable_bin\"])[\"assemblies\"]\n    if len(tables) != len(surfaces):\n        raise SystemExit(f\"{fid}: {len(tables)} joint tables for {len(surfaces)} surfaces\")\n    pal = tables[only]\n")
    s=rep(s,"def assemblies_of(fid):",PAL+"def assemblies_of(fid):")
    return s
edit(R/"work/v20-char/build_character.py",bc)
def ba(s):
    s=rep(s,"def model_parts(ids, sk):",PAL+"def model_parts(ids, sk):")
    a=s.index("        pal = palette(fb, n)\n");b=s.index("        payload_end = struct.unpack_from(\"<I\", fb, 0)[0] + 8; mats, at = [], payload_end")
    block=s[a:b]
    s=s[:a]+"        tables = palettes(fb, n)\n        raw = vis.read_bytes()\n        if len(tables) != len(mesh[\"assemblies\"]):\n            skipped.append((fid, \"tables\", len(tables), len(mesh[\"assemblies\"]))); continue\n"+s[b:]
    s=rep(s,"            if asm[\"unknown_u16_at2\"]: continue\n            vb = mesh[\"vertex_buffers\"][asm[\"vertex_buffer\"]]; ib =","""            if asm["unknown_u16_at2"]: continue
            pal = tables[ai]
            if not pal or len(pal) > 96:
                skipped.append((fid, "palette", len(pal))); continue
            entries = []
            for idx, inv_t, inv_q in pal:
                cur = idx
                while cur != 0xffff and fnames[cur] not in sk["index"]:
                    cur = fpar[cur]
                joint = sk["index"][fnames[cur]] if cur != 0xffff else 1
                wq, wt = sk["world"][sk["index"][fnames[idx]]] if fnames[idx] in sk["index"] else fworld[idx]; iq = conj(wq); it = tuple(-x for x in rot(iq, wt))
                err = max(abs(it[k] - inv_t[k]) for k in range(3))
                entries.append((joint, it, iq) if err < 1 or fnames[idx] in sk["index"] else (joint, tuple(inv_t), conj(tuple(inv_q))))
            vb = mesh["vertex_buffers"][asm["vertex_buffer"]]; ib =""")
    return s
edit(R/"work/v20-char/build_actors.py",ba)
print("ok")
