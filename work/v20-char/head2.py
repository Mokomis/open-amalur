import json,re,struct,collections
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
fabs={int(k):str(v) for k,v in syms["fab"].items()}
heads=[(k,v) for k,v in fabs.items() if re.search(r"head|face|neck|scalp|hair",v,re.I)]
print("named",len(heads),[v for k,v in heads if re.search(r"(^|_)(alm|hum|human|male|m_)|male",v,re.I)][:50])
def ext(fid):
    fs=extract([f"{fid}.fab_visual_data_streamable_bin"]);vis=fs.get(f"{fid}.fab_visual_data_streamable_bin")
    if not vis:return None
    m=amalur_mesh.parse_file(vis);raw=vis.read_bytes();out=[]
    for a in m["assemblies"]:
        if a["unknown_u16_at2"]:continue
        vb=m["vertex_buffers"][a["vertex_buffer"]];st=vb["stride_bytes"];b=vb["data_file_offset"];zs=[struct.unpack_from("<f",raw,b+i*st+8)[0] for i in range(vb["vertex_count"])];xs=[struct.unpack_from("<f",raw,b+i*st)[0] for i in range(vb["vertex_count"])]
        out.append((vb["vertex_count"],round(min(zs)),round(max(zs)),round(min(xs)),round(max(xs))))
    return out
bc=(root/"work/v20-char/build_character.py").read_text()
print([l.strip()[:190] for l in bc.splitlines() if re.search(r"HEADS|BODY|PARTS|head|neck",l)][:16])
for n in ("promo_melee_nonset_head","majestic_head","04_rogue_nonset_unique_head","03_silk_head","promo_magic_set_head"):
    k=next((k for k,v in fabs.items() if v==n),None);print(n,k,ext(k) if k else None)
# Heads people really wear: what the townsfolk bundles use.
seen=collections.Counter()
for nm in ("npc_dal_alm_declanmalus","npc_dal_alm_jeddakerning","npc_dal_var_agarth","citizen_gorhart_alm_male_1366811_sq77crowd","bandit_redlegion_daggers_m_03"):
    sid=next((int(k) for k,v in syms["simtype"].items() if v==nm),None)
    if not sid:continue
    d=extract([f"{sid}.bundle"])[f"{sid}.bundle"].read_bytes();ids=list(dict.fromkeys(struct.unpack_from(f"<{(len(d)-16)//4}I",d,16)))
    r=[]
    for v in ids:
        if "fab_visual_data_streamable_bin" in files_by_id.get(v,[]) and v not in (467100,456813,611642):
            e=ext(v)
            if e:r.append((v,fabs.get(v),e[:2]))
    print(nm,r[:12])
# Materials on the npc parts
print("head/neck material names",[str(v) for v in syms["material"].values() if re.search(r"head|neck|face|skin",str(v),re.I)][:40])
print("player report", (root/"work/v20-char").glob("character-report*") and [p.name for p in (root/"work/v20-char").glob("character*")])
