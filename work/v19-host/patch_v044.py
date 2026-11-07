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
    s=rep(s,"""    # Some clips animate only the first joints of the rig; the others hold the rig's own rest pose.
""","""    # Some clips carry 52 joints. Bone offsets show the first 52 follow the rig's order, except that 11 to 14, 16 and 33 decode to other bones' data
    # (not understood: joints 11 to 14 repeat 17 to 20). Those, and the joints past 51, hold the rig's own rest pose, so the right foot does not animate in these swings.
    broken = (11, 12, 13, 14, 16, 33) if clip_joints_of(cid) < j else ()
""")
    s=rep(s,"""    clip_joints = struct.unpack_from("<H", (inp / f"initial_0.pak/{cid}.anm_bxml").read_bytes(), 8 + 0xe)[0]
""","""    clip_joints = clip_joints_of(cid)
""")
    s=rep(s,"""struct.unpack_from("<7f", b, 12 + i * 48) if i % j < clip_joints else struct.unpack_from""","""struct.unpack_from("<7f", b, 12 + i * 48) if i % j < clip_joints and i % j not in broken else struct.unpack_from""")
    s=rep(s,"""for cid, name in CLIPS:
    baked = out / f"baked/{cid}.bin\"""","""def clip_joints_of(cid):
    return struct.unpack_from("<H", (inp / f"initial_0.pak/{cid}.anm_bxml").read_bytes(), 8 + 0xe)[0]
for cid, name in CLIPS:
    baked = out / f"baked/{cid}.bin\"""")
    return s
edit(R/"work/v20-char/build_character.py",bc)
print("ok")
