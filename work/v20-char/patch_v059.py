from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";h=root/"work/v19-host"
p=h/"android_scene.c";t=p.read_text(encoding="utf-8")
a='{extern int oa_stream_hide;oa_stream_hide=prop_int("debug.opem.hide",0);}'
assert a in t
t=t.replace(a,a+'prof_pulse=prop_int("debug.opem.pulse",0);',1)
b="static void prof_read(void){"
assert b in t
t=t.replace(b,"static int prof_pulse;\n"+b,1)
c="if(prof.walk&&playing){movement.move_y=1.f;c.walk_yaw=(float)(prof.walk-1)*.01745329f;}"
assert c in t
d=t.index(c);e=t.index("oa_combat_step(f,dt,",d)
# Test aid: the stick lets go every other pulse period (tenths of a second, real time), so starts and stops can be seen.
marker="/* Test aid: debug.opem.pulse lets go of the stick every other period, in tenths of a second, so starts and stops can be seen. */"
line_end=t.rfind("\n",d,e)
t=t[:e]+t[e:]
i=t.rfind("\n",0,e)
t=t[:i+1]+marker+"if(prof_pulse&&playing&&(monotonic_ms()/(prof_pulse*100))%2){movement.move_y=0;movement.move_x=0;}\n"+t[i+1:]
p.write_text(t,encoding="utf-8",newline="\n")
n=root/"work/CURRENT_STATE.txt"
note="""

2026-11-01 overnight notes (terrain, models, clips, effects)
- Complete terrain: every chunk key is a map position; Dalentarth is 2402 chunks, 35,387 tiles. Load re-measured on it: vsync 10 min p95 16.67 ms, worst frame 30 ms, GPU mean 7.91 ms, 0 hitches.
- Bug found: build_zone kept only instances whose reference had top bits 15. Those bits are not a filter; 1,843 Dalentarth model instances (standing stones, blended cliff rock, trees, barricades, walls) were being dropped. Low 28 bits are the model id for values 2-7 and 15. What the top bits mean is not known.
- Tan areas seen through the ground are the below-horizon sky colour showing through real terrain cuts.
- Player clips: Player motion set has run/walk starts and stops, turn entries, slope and lean poses and idle variations. All 64 joints. Turn clips carry no net rotation. Slope and lean poses are relative to an unknown reference; the difference within each pair is used.
- Effects: real data exists. initial_0.pak batch_1477/1658189/1946058/1966575.task_bxml hold (id,length) tables of emitter and particle tasks. Spaces place clusters in 60-byte records at slot 0xd0 (position at +4, quaternion at +20, cluster id at +52). Channel: class, name, 8 zero bytes, u32, 4 bytes, 1.0, payload at +28. Channel meanings are inferred from values, not from game code.
- Second zone: zone_start.py picks a test start from the median character (not a recovered spawn). rebuild_poe.cmd builds work/v24-zones/poe-*. town_live.inc and town_start.inc are per-zone copies.
"""
n.write_text(n.read_text(encoding="utf-8",errors="replace")+note,encoding="utf-8")
print("ok")
