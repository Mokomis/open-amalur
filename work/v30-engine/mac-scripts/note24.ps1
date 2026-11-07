$note=@'

V0.21.0 PEOPLE (2026-10-31): versionCode 22, APK outputs/scene-v19/opem-amalur-scene-v0.21-arm64.apk sha256 starts ab2f2175bc50b1e0. work/v20-char/build_npcs.py builds work/v20-town/town_npcs.bin: 12 people from gor records in space 431638 within 56 m of the door. Gor: space +8, position +24, then 0,0,0 and scale in these records, so authored yaw is not recovered; simtype id is the first word found in the simtype symbols. Each simtype has <id>.bundle listing its FABs; many FAB names are not in symbols. Clips: human_idle_01 457525 with human_skel_npc 467100, Human_NPC_Idle_01_F 1356710 with human_skel_f 611642.
FAB facts: assembly u16 at +2 of 32768 = lower LOD. Per-assembly material ids are unaligned u32 after the skeleton payload, one per assembly in order, skipping ids at or below 4096. Palette records can be unaligned. Stride 56, 60 and 64 share pos, joints, weights, uv at +24; normal at +32 or +40 by unit-length test. The shader reads three weights and derives the fourth; build_character and build_npcs now do too (this caused long bars when sum < 1 at world coordinates near -62000).
Authored or missing: hair and beard colour is neutral brown because the game tints them; eye_shadow, face_acc and eyelash skipped (need blending); weapons skipped; no walking, schedules, dialogue, or collision with people. Yaw 0 for all. Frame interval 17.7 ms in a short town run.
Windows host files are edited in place by patch scripts, and scp from Mac scratchpad overwrites build scripts: patch local copies too.
'@
Add-Content -Encoding UTF8 'work\CURRENT_STATE.txt' $note
Add-Content -Encoding UTF8 'outputs\scene-v19\PROGRESS.txt' $note
'noted'
