import json
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";h=root/"work/v19-host";wc=root/"work/v20-char"
def sub(p,pairs):
    t=p.read_text(encoding="utf-8")
    for a,b in pairs:
        assert a in t,a
        t=t.replace(a,b)
    p.write_text(t,encoding="utf-8",newline="\n")
sub(h/"oa_character.h",[("OA_CHAR_MAX_JOINTS=96,OA_CHAR_MAX_PALETTE=64,","OA_CHAR_MAX_JOINTS=128,OA_CHAR_MAX_PALETTE=96,")])
sub(h/"oa_character_gl.c",[("uniform vec4 bones[192];","uniform vec4 bones[288];")])
sub(wc/"build_zone.py",[
 ('("grass", "for_terrain_grass01_d"), ("rock", "for_terrain_rock01_d"), ("cliff", "for_terrain_cliff01_d")','("grass", f"{TP}_terrain_grass01_d"), ("rock", f"{TP}_terrain_rock01_d"), ("cliff", f"{TP}_terrain_cliff01_d")'),
 ('n=[tex_id("for_terrain_grass01_n"), tex_id("for_terrain_rock01_n"), tex_id("for_terrain_cliff01_n")]','n=[tex_id(f"{TP}_terrain_grass01_n"), tex_id(f"{TP}_terrain_rock01_n"), tex_id(f"{TP}_terrain_cliff01_n")]'),
 ('d=tex_id("for_flora_grass01_d"), a=tex_id("for_flora_grass01_a")','d=tex_id(f"{TP}_flora_grass01_d"), a=tex_id(f"{TP}_flora_grass01_a")'),
 ('ZONE = __import__("os").environ.get("OA_ZONE", "dal")','ZONE = __import__("os").environ.get("OA_ZONE", "dal")\n# Each zone has its own ground set; which of them goes where is still chosen by slope, not by the game\'s paint maps.\nTP = {"dal": "for", "poe": "pln", "det": "det", "ala": "ala", "klu": "klu"}[ZONE]'),
])
sub(wc/"rebuild_poe.cmd",[("ZONE >","ZONE >")])
# Erathell's existing arrays: change only the ground and grass entries, then redo textures.
syms=json.loads((root/"work/v20-inputs/symbols.json").read_text())["texture"];byname={str(v):int(k) for k,v in syms.items()}
z=root/"work/v24-zones/poe-zone/zone_materials.json";m=json.loads(z.read_text());T=m["materials"][m["terrain"]];G=m["materials"][m["grass"]]
print("before",[syms.get(str(x)) for x in T["d"]],syms.get(str(G["d"])))
T["d"]=[byname[f"pln_terrain_{b}01_d"] for b in ("grass","rock","cliff")];T["n"]=[byname.get(f"pln_terrain_{b}01_n") for b in ("grass","rock","cliff")]
G["d"]=byname["pln_flora_grass01_d"];G["a"]=byname.get("pln_flora_grass01_a")
print("after",T,G);z.write_text(json.dumps(m))
print("ok")
