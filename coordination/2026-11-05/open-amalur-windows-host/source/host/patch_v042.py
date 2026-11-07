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
    s=rep(s,"    _, refs = texture_for(mid)\n    order = sorted(refs,","""    # These two surfaces need blending or a flat black the renderer has no material for.
    if syms["material"].get(str(mid)) in ("eye_shadow", "mouth_black"):
        continue
    _, refs = texture_for(mid)
    # White tint layers are not a surface's colour.
    refs = [x for x in refs if "par_color" not in x[1]] or refs
    order = sorted(refs,""")
    s=rep(s,"""        if image is None:
            continue
        tex_index[cand[0]] = len(textures)""","""        if image is None:
            # Non-square textures: walk the stored levels by the header's own mip count.
            for name in names:
                if name not in f or image is not None:
                    continue
                data = f[name].read_bytes()
                if data[16:20] != b"KEEN" or data[29] not in (1, 5):
                    continue
                w, h, fmt, mips = *struct.unpack_from("<HH", data, 20), data[29], struct.unpack_from("<H", data, 35)[0]
                at, block = 38, 8 if fmt == 1 else 16
                for _ in range(mips):
                    size = ((w + 3) // 4) * ((h + 3) // 4) * block
                    if at + size > len(data):
                        break
                    if max(w, h) <= MAX_TEXTURE:
                        image = (w, h, bytes(__import__("keen_texture").decode_blocks(data[at:at + size], w, h, fmt)), name)
                        break
                    at += size
                    w, h = max(1, w // 2), max(1, h // 2)
        if image is None:
            continue
        tex_index[cand[0]] = len(textures)""")
    return s
edit(R/"work/v20-char/build_character.py",bc)
print("ok")
