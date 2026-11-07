from pathlib import Path
import json, struct, re
root = Path.home() / "Documents/Opem Amalur"
host = root / "work/v19-host"
syms = json.loads((root / "work/v20-inputs/symbols.json").read_text())
mid = next(k for k, v in syms["material"].items() if v == "02_steel_sword_1h")
for a in ("patch_0.pak", "initial_0.pak"):
    p = root / "work/v20-inputs" / a / f"{mid}.mat_bxml"
    if p.exists():
        d = p.read_bytes()
        print("sword material", a, [syms["texture"][str(v)] for v in (struct.unpack_from("<I", d, i)[0] for i in range(0, len(d) - 3, 4)) if str(v) in syms["texture"]])
        break
def edit(name, pairs):
    f = host / name
    t = f.read_bytes().decode()
    for old, new in pairs:
        assert t.count(old) == 1, old[:70]
        t = t.replace(old, new)
    f.write_bytes(t.encode())
edit("exploration_overlay.c", [
 ("rect(o,w*.5f-180*s,14*s,360*s,20*s,dark);rect(o,w*.5f-176*s,18*s,352*s*health[0],12*s,red);", "rect(o,135*s,14*s,300*s,20*s,dark);rect(o,139*s,18*s,292*s*health[0],12*s,red);"),
 ("rect(o,w*.5f-140*s,40*s,280*s,16*s,dark);rect(o,w*.5f-136*s,43*s,272*s*health[1],10*s,orange);", "rect(o,135*s,40*s,240*s,16*s,dark);rect(o,139*s,43*s,232*s*health[1],10*s,orange);"),
])
edit("android_scene.c", [
 ("c.foe.facing=f->foe_facing;c.move_scale=f->player_locked?0.f:1.f;", '''c.foe.facing=f->foe_facing;c.move_scale=f->player_locked?0.f:1.f;
                    {static int64_t logged;if(now-logged>1000){float dx=c.foe.feet[0]-c.body.feet[0],dy=c.foe.feet[1]-c.body.feet[1];logged=now;LOGI("Fight state foe=%d dist=%.0f v=(%.0f %.0f) hp=%.0f/%.0f valid=%d grounded=%d err=%s",(int)f->foe,sqrtf(dx*dx+dy*dy),f->foe_vx,f->foe_vy,f->player_hp,f->foe_hp,c.foe_body.valid,c.foe_body.grounded,fight_error);}}'''),
 ("oa_combat *f=&c.combat;char fight_error[256];", 'oa_combat *f=&c.combat;char fight_error[256]="";'),
])
print("ok")
