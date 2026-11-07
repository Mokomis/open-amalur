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
    s=rep(s,"""    rows = bytearray()
    for i in range(frames * j):
        v = struct.unpack_from("<7f", b, 12 + i * 48)
""","""    rows = bytearray()
    # Some clips animate only the first joints of the rig; the others hold the rig's own rest pose.
    clip_joints = struct.unpack_from("<H", (inp / f"initial_0.pak/{cid}.anm_bxml").read_bytes(), 8 + 0xe)[0]
    rest = 4 + 0x18 + struct.unpack_from("<i", main, 4 + 0x18)[0]
    for i in range(frames * j):
        v = struct.unpack_from("<7f", b, 12 + i * 48) if i % j < clip_joints else struct.unpack_from("<7f", main, rest + (i % j) * 48)
""")
    s=rep(s,"""            for name in names:
                if name not in f or image is not None:
                    continue
                data = f[name].read_bytes()
                if data[16:20] != b"KEEN" or data[29] not in (1, 5):""","""            for name in names:
                if name not in f:
                    continue
                data = f[name].read_bytes()
                if data[16:20] != b"KEEN" or data[29] not in (1, 5):""")
    s=rep(s,"""                    if max(w, h) <= MAX_TEXTURE:
                        image = (w, h, bytes(__import__("keen_texture").decode_blocks(data[at:at + size], w, h, fmt)), name)
                        break
                    at += size
                    w, h = max(1, w // 2), max(1, h // 2)
        if image is None:
            continue""","""                    if max(w, h) <= MAX_TEXTURE:
                        if image is None or w > image[0]:
                            image = (w, h, bytes(__import__("keen_texture").decode_blocks(data[at:at + size], w, h, fmt)), name)
                        break
                    at += size
                    w, h = max(1, w // 2), max(1, h // 2)
        if image is None:
            continue""")
    return s
edit(R/"work/v20-char/build_character.py",bc)
print("ok")
