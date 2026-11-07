from pathlib import Path
host = Path.home() / "Documents/Opem Amalur/work/v19-host"
p = host / "android_scene.c"
t = p.read_bytes().decode()
a = "c.foe.facing=f->foe_facing;c.move_scale=f->player_locked?0.f:1.f;"
assert t.count(a) == 1
t = t.replace(a, a + '\n                    if(now-c.foe_log_ms>1500){c.foe_log_ms=now;LOGI("Fight foe=%d foe_at=(%.0f %.0f %.0f) me=(%.0f %.0f %.0f) hp=%.0f/%.0f detour=%.2f err=%s",(int)f->foe,c.foe.feet[0],c.foe.feet[1],c.foe.feet[2],c.body.feet[0],c.body.feet[1],c.body.feet[2],f->player_hp,f->foe_hp,c.foe_detour,fight_error);}')
a = "    int foe_ready;\n"
assert t.count(a) == 1
t = t.replace(a, "    int foe_ready;\n    int64_t foe_log_ms;\n")
p.write_bytes(t.encode())
print("ok")
