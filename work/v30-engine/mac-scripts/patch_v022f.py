from pathlib import Path
host = Path.home() / "Documents/Opem Amalur/work/v19-host"
p = host / "android_scene.c"
t = p.read_bytes().decode()
old = "const float place[3]={2600.f,-63500.f,5170.f};"
assert t.count(old) == 2
t = t.replace(old, "const float place[3]={OA_FOE_SPAWN_X,OA_FOE_SPAWN_Y,5170.f};")
a = "static const char *const oa_door_prompts[2]="
assert t.count(a) == 1
t = t.replace(a, "/* Authored spawn in the open field ahead of the door, because the bandit has no pathfinding. */\n#define OA_FOE_SPAWN_X 2000.f\n#define OA_FOE_SPAWN_Y -61700.f\n" + a)
p.write_bytes(t.encode())
print("ok")
