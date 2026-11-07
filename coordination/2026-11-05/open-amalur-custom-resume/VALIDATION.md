# Resume validation — 2026-11-05

Windows host: ROBMACHINEX. Existing custom-engine Windows targets built successfully (Ninja: no work to do). Six batches executed freshly; results and stdout/stderr are saved alongside this file. Menu/save tests used a separate test-data folder, not game saves.

| Suite | Exit | Seconds | Log |
|---|---:|---:|---|
| input | 0 | 0.031 | input.log |
| actor-ai | 0 | 0.016 | actor-ai.log |
| navigation | 0 | 0.015 | navigation.log |
| audio | 0 | 0.032 | audio.log |
| menu-inventory-save | 0 | 0.062 | menu-inventory-save.log |
| character-combat | 0 | 0.75 | character-combat.log |

These exercise portable logic and assets; they do not validate a Windows rendered scene, original-game behavior, physical input or tablet runtime. The existing renderer is Android-only. No tablet install, launch or save change was performed.
