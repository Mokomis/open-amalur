import re
from pathlib import Path
R=Path.home()/"Documents/Opem Amalur";r=R/"work/v19-host"
def edit(f,fn):
    s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n");s=fn(s)
    if crlf:s=s.replace("\n","\r\n")
    f.write_bytes(s.encode())
def rep(s,a,b):
    assert a in s,a[:80]
    return s.replace(a,b,1)
def bc(s):
    s=rep(s,'(673754, "combat_idle"), (673863, "combat_walk"), (673928, "combat_run")]','(_anim("human_sword_idle_01"), "sword_idle"), (_anim("human_walk_01"), "sword_walk"), (_anim("human_run_01"), "sword_run")]')
    s=rep(s,"# Exploring uses the ordinary clips; 3 to 7 are the fight; 8 to 10 are the same movement in a fighting stance.","# From the Player motion set. 0 to 2 explore; 3 to 7 are the fight, still the NPC family; 8 to 10 carry the sword, which only changes the idle.")
    s=rep(s,'for fid, label in PARTS:\n    fab = extract(','''def assemblies_of(fid):
    vis = extract([f"{fid}.fab_visual_data_streamable_bin"])[f"{fid}.fab_visual_data_streamable_bin"]
    return [i for i, a in enumerate(amalur_mesh.parse_file(vis)["assemblies"]) if not a["unknown_u16_at2"]]
# The head keeps each surface apart, because skin and eyes have their own materials.
for fid, label, only in [(f, l, None) if l != "head" else (f, l, a) for f, l in PARTS for a in (assemblies_of(f) if l == "head" else [None])]:
    fab = extract(''')
    s=rep(s,"        wq, wt = fworld[idx]\n","        # A part's own skeleton copy can sit apart from the rig; meshes are authored in rig space.\n        wq, wt = jworld[jindex[fnames[idx]]] if fnames[idx] in jindex else fworld[idx]\n")
    s=rep(s,'''    for asm in r["assemblies"]:
        vb = r["vertex_buffers"][asm["vertex_buffer"]]''','''    for ai, asm in enumerate(r["assemblies"]):
        if only is not None and ai != only:
            continue
        vb = r["vertex_buffers"][asm["vertex_buffer"]]''')
    s=rep(s,'''        if vb["stride_bytes"] != 60:
            raise SystemExit(f"{fid}: stride {vb['stride_bytes']}")
''','''        st = vb["stride_bytes"]
        if st not in (56, 60, 64):
            raise SystemExit(f"{fid}: stride {st}")
        def score(offset):
            total = 0.0
            for i in range(0, vb["vertex_count"], max(1, vb["vertex_count"] // 40)):
                x = struct.unpack_from("<3h", raw, vb["data_file_offset"] + i * st + offset)
                total += abs(math.sqrt(sum((c / 32767) ** 2 for c in x)) - 1)
            return total
        normal_at = min((o for o in (32, 36, 40, 44) if o + 6 <= st), key=score)
''')
    s=rep(s,'a = vb["data_file_offset"] + i * 60','a = vb["data_file_offset"] + i * st')
    s=rep(s,'struct.unpack_from("<3h", raw, a + 32)]','struct.unpack_from("<3h", raw, a + normal_at)]')
    s=rep(s,'''    mid = mats[0] if mats else 0
''','''    mid = mats[0] if mats else 0
    if only is not None:
        # Per-surface material ids sit unaligned after the skeleton, one for each surface in order.
        ordered, at = [], struct.unpack_from("<I", fb, 0)[0] + 8
        while at + 4 <= len(fb):
            v = struct.unpack_from("<I", fb, at)[0]
            if v > 4096 and str(v) in syms["material"]:
                ordered.append(v); at += 4
            else:
                at += 1
        mid = ordered[only] if only < len(ordered) else mid
''')
    if not re.search(r"^import .*\bmath\b",s,re.M):s="import math\n"+s if not s.startswith('"""') else s.replace('\nimport ','\nimport math\nimport ',1)
    return s
edit(R/"work/v20-char/build_character.py",bc)
def ch(s):return rep(s," /* Human rigs only: the head stays up while the body leans into a run. */\n int level_head;\n","")
edit(r/"oa_character.h",ch)
def cc(s):
    s=rep(s," c->level_head=c->joints==64&&c->parents[21]==20&&c->parents[20]==19;\n","")
    a=s.index(" uint32_t j,i;float level[4]={0,0,0,1};if(!c->ready)return;");b=s.index(" for(j=0;j<c->joints;j++){float q[4]={0,0,0,0}")
    s=s[:a]+" uint32_t j,i;if(!c->ready)return;\n"+s[b:]
    s=rep(s,"\n  if(c->level_head&&(j==20||j==21)){float was[4];memcpy(was,c->world_q[j],16);qmul(c->world_q[j],level,was);}}","}")
    return s
edit(r/"oa_character.c",cc)
def ba(s):return rep(s,"            wq, wt = fworld[idx]; iq = conj(wq);","            wq, wt = sk[\"world\"][sk[\"index\"][fnames[idx]]] if fnames[idx] in sk[\"index\"] else fworld[idx]; iq = conj(wq);")
edit(R/"work/v20-char/build_actors.py",ba)
print("ok")
