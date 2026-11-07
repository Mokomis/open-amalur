# Initial door pose: bounded source check

No source-backed conclusion that the closed starting door uses FAB rest or animationframe0 was obtained.

Observed:
-Exact GOR1790948 and Type1789987 select FAB1789717 and script1794170; GOR transform and all flags preserved in the parent manifest.
-Type1789987 has PartAnimation(kind4) bytes0400000000000000 in its8B component span. Native00efcf40 copies its scalar+4; PartAnimation00ef69a0 copies that field into instance+24. The authored value is0, but that scalar's motion/state meaning is not assigned.
-Recovered Door_Std_WOS_Start.on_creation tests ACTOR.has_been_looted and, when false, schedules timer25843434 after100. It does not directly select a motion or frame. on_interact defers loot_skeleton by Chest.m_OPEN_ANIM_TIME, but does not prove the initial graphic pose. Exact on_creation script copy and original script SHA are preserved.
-Motion-set1789863 source header has5 motion keys(open,close,openidle,CloseIdle,Loot) and same animation1789841 referenced twice. This supplies named motion choices, not a decoded initial/default-state selector.
-Animation1789841 raw header contains floats3.3329999446868896 and29.999998092651367 at+0c/+10; their likelyduration/rate roles are not independently established here. No frame decoder/sampling was implemented.

Unresolved:
Native initial motion selection/actor gateway state and motion-set node ranges/flags are still needed to know whether the original closed door uses rest, sampled0, CloseIdle or another authored segment. Neither names nor the raw animation's presence selects one.
Keep native-rest preview separately selectable/quarantined. Do not label it 'closed-original' or assume frame0. No live original inputs/capture or arbitrary pose fitting were performed.
