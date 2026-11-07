from pathlib import Path
p = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"
t = p.read_bytes().decode()
old = "if(!graphics_draw(&g,&mesh,&materials,&c,&movement,&interaction,room_lighting,door_prompt))"
assert t.count(old) == 1
t = t.replace(old, '{static const char *logged;if(door_prompt!=logged){logged=door_prompt;LOGI("Door prompt %s world=%d feet=(%.1f %.1f %.1f)",door_prompt?door_prompt:"none",world,c.body.feet[0],c.body.feet[1],c.body.feet[2]);}}\n                ' + old)
p.write_bytes(t.encode())
print("ok")
