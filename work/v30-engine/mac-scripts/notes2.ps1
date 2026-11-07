$n=@'

v0.30.0 live load with real actors (2026-11-01, tablet native 2520x1680, Dalentarth). Replaces the v0.28 moving result, whose test loop left the world for part of its run.
World: terrain heights are signed int16 (build_town.py, build_veggie.py); 65535 alone marks a hole. terrain_fill2.py recovered 312 tiles from 21 unread chunks and placed 570 more from chunk headers and shared edges; 21,721 shared edges match, none differ. Backups: terrain-*.pkl.before-recovery. Actor height against terrain: median -1 cm. Still without terrain under them: 69 of 790 actors.
Actors: work/v20-char/build_actors.py -> work/v23-actors (136 models, 790 actors). Real: placed objects, 216 encounter records and their spawn points in space_bxml, encounter tables, monster groups, models, textures, clips. Authored: group choice weights, one member per point, all encounters active at once, stats, speeds, strike times, all behaviour (oa_actor_ai.c). Near characters use the capsule controller, far ones rays or none. No pathfinding for creatures.
Player: exploring uses human_idle/walk/run_01, fights use combat clips; playback rate from measured planted foot speed in every clip; sword hidden outside fights because no sheathed model exists. Start, stop, turn and slope clips not used.
Test walk: debug.opem.tour holds the virtual stick along work/v23-actors/route.bin (build_route.py, A* over a 2 m map from slope and collision) through exploration_update.
Results, 60 characters' worth of proxies removed, crowd 1, fx 300, shadows, 932 lights, 1 km view: uncapped 3 min mean 7.96 ms, p95 9.53, worst frame 14.44, GPU mean 6.94, max 8.76. Vsync 10 min interval p95 16.67, worst frame 33.26, typical worst per 4 s about 23, GPU mean 7.05, max 7.69, no frame over 40 ms. Peaks: 30 near, 40 bodies, 21 drawn, 13 chasing, actor update 2.5 ms. Battery 34.8-37.5 C, thermal 0-1 capped, 2 uncapped. PSS up to 610 MB. Walk: 0 airborne frames, 0 give-ups, 32 stops.
Not measured: player attacking in the load (combat stepping is off in profile mode; invulnerable), water, audio, real effects data, other zones. Route covers 29 legs, about 3.3 km; 144 stops were unreachable on its conservative map. APK 639 MB.
'@
Add-Content -Path work\CURRENT_STATE.txt -Value $n
Add-Content -Path outputs\scene-v19\PROGRESS.txt -Value $n
"written"
