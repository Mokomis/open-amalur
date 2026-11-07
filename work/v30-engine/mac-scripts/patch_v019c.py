from pathlib import Path
p = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"
t = p.read_bytes().decode()
a = t.index('{static const char *logged;if(door_prompt!=logged)')
b = t.index('if(!graphics_draw(&g,&mesh,&materials,&c,&movement,&interaction,room_lighting,door_prompt))')
t = t[:a] + t[b:]
p.write_bytes(t.encode())
print("removed debug log")
