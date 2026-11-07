from pathlib import Path
host = Path.home() / "Documents/Opem Amalur/work/v19-host"
p = host / "tests/input_stubs/android/keycodes.h"
t = p.read_bytes().decode()
t = t.replace("\nAKEYCODE_F=34,AKEYCODE_BUTTON_X=99,", "")
assert "AKEYCODE_F" not in t
t = t.replace("AKEYCODE_L=40,", "AKEYCODE_F=34,AKEYCODE_BUTTON_X=99,AKEYCODE_L=40,", 1)
p.write_bytes(t.encode())
p = host / "android_scene.c"
t = p.read_bytes().decode()
a = "if(f->play_player>=0)oa_character_play(&c.character,f->play_player,f->hold_player,f->play_player_rate);"
assert t.count(a) == 1
t = t.replace(a, "if(f->stop_player)oa_character_stop(&c.character);if(f->stop_foe)oa_character_stop(&c.foe);\n                    " + a)
p.write_bytes(t.encode())
print("ok")
