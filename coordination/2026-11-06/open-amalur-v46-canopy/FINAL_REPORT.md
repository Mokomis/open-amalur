# Open Amalur v0.37: distant canopy resolved

The reported excess distant canopy at the bridge is fixed. Options → Canopy offers **Corrected** (default) and **Dense** (the preserved previous coverage). Both switch live and persist across application restarts on Windows and the OPPO tablet.

## Cause and native evidence

The custom importer rendered SPACE-owned leaves from surrounding, unloaded areas together. The offending leaf belonged to SOUTH 431642, source 198. Distance cutoffs were the wrong remedy.

Read-only inspection of the already-running, paused original game found its camera at exactly the retained reference position (8591.932617, -87036.03125, 6493.066406), with current SPACE 431646. Its actual registered static collections were REGION 0, WEST 431646 and transition 431650; SOUTH 431642 was absent before per-object culling. The executable SHA256 was16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314. No original-game input, process mutation, launch or save operation was performed.

Native ff08f0 passes literal depth 1 to fdce90. The ready queue fef1c0 decrements it and calls fdcf20 to load the other endpoint of each incident portal; depth 0 neighbors do not recurse. Thus the ordinary load rule is current SPACE plus undirected one-hop neighbors. The27 authored edges from 431608.region_bxml reproduce the live collection list exactly. c3e3e0 independently rejects static collections outside the current/visible SPACE entries. The native per-record metric is Euclidean placement distance squared divided by 4 in this live quality profile; it does not reject source 198 and was not used as a new cutoff.

Evidence: native-selection/REPORT.md; native-metric/REPORT.md and CURRENT_SPACE_REPORT.md; runtime/registered-collections.json and bounded raw read-only dumps. The source graph is derived from source c0 endpoints; c8 supplies the separate authored portal geometry. They are distinct164-byte layouts.

## Implementation and preservation

- New oa_canopy.c/.h reads the source graph, tracks explicit scene identity, and constructs its admitted area set. The existing source scene declares initial SPACE431638. The matched reference fixture explicitly supplies the original camera's SPACE 431646; its camera is overridden independently of the hidden player.
-175 leaf files now carry 400 source-area ranges. All 51,831 triangles,96,829 vertex records and index ordering are byte-identical to R3. Corrected filters area ownership in visible color and MAIN early-depth passes; Dense bypasses that filter. All 33 captured valid SPACE leaf draws remain admitted. Regional leaves remain independent.
- R3 shadow/proxy rendering is preserved. All other packaged assets are unchanged, including waterfall geometry, materials, textures and parameters. The waterfall rendering sources are unchanged. The owner-preferred waterfall style remains intentional.
- Menu choices retain existing preferences: settings files184/188/192 bytes are compatible. New saves append the current SPACE to the existing 88-byte prefix (92 bytes total). Old 88-byte saves load without guessing an arbitrary area: the declared scene-spawn location is recognized; otherwise dense fallback remains until a source portal establishes identity. Original 88-byte readers can read the new prefix.

## Verification

One batched Windows/ARM64 build passed with stable source hashes. Windows compilation took 2.34 s and ARM compilation 1.11 s. No source changes followed that build.

On the matched 1536×864 Windows reference, Dense preserves the prior GPU depth 16762614 at pixel 980,100. Corrected produces 16777215 (clear), exactly matching the original game. The corrected final color was 240,255,255 versus original 250,255,255; this does not claim complete lighting or pixel parity. Full source geometry remains available through Dense. Windows steady submitted draws were 2264 Dense and 1910 Corrected; these offscreen-host counts are not Android performance estimates.

The real Windows menu was operated with keyboard controls. Dense was saved, the app restarted, and actual renderer logs confirmed the persistent choice. An isolated real menu save wrote 92 bytes with SPACE 431646; loading it invoked the new restore hook with that same identity. No personal Windows user-data folder was used. A separate mouse-control experiment could not find the window and was abandoned after two attempts; keyboard validation completed successfully.

C sanitizer checks passed: 11,963 graph/parser/portal checks, including the actual source graph, all 27 finite portal rectangles in both directions, unknown-identity recovery, truncations and 10,000 mutations; 248 save compatibility checks; and the independent settings compatibility harness. Independent review also verified exact ownership of every triangle and all 33 positive native fixtures.

On tablet 99cc517a, v0.37/code 39 was installed with the existing signer. The installed APK hash matched the Windows package. Touching Options → Canopy switched Corrected to Dense, actual draw logs changed accordingly, and Dense persisted through a full application restart. Steady renderer counters at the unchanged tablet view showed 353 rejected leaf runs in Corrected and 0 in Dense, with queued 0. This verifies native ARM execution of the selector; the tablet view differs in camera/aspect from the exact Windows reference. No sustained FPS claim is made. A first restart-log assertion expected the once-only startup message after it had rotated out of the verbose log ring; ongoing renderer counters and the 192-byte persisted setting supplied the valid evidence instead.

## Delivered artifact and safety

Windows APK: outputs/scene-v46/open-amalur-v0.37-arm64.apk, 1,020,379,126 bytes.

SHA256: 8a817ab01b48aa96ad1e7b1957f4e6816d9f4beba84534e3d6287b94e60a419f.

ARM library SHA256: f1d23227a1e342b871aef6554861f4ddc4d69e1ef4a0ae654f1a8dc60c614fb2.

Signer SHA256: c47ba7823090afa66297683d7be45c2df8d7c37e1443bcece168f5b915e9344f.

The tablet's original save was never overwritten. Its 88-byte SHA remains 13734501b6cdbd25fbe8fa8202226ea084382755d2522ee46d0b985045e85f11. After testing, its original 184-byte settings were restored exactly: 27665629f70cf1902ed4e5bec8daadcd6cdb5dfef857dfd3a0430ab475af0c55. Temporary properties and USB stay-awake were restored; the app is stopped and the tablet is Dozing again. Corrected is the default when its original preferences are next loaded.

The authoritative Windows project remains outside Git. The original key, Ghidra databases, game files, FEX work, all prior builds, dense geometry, and staging/backups were preserved. The original Windows launcher task remains on the normal town scene. The Qwen service/configuration was not changed. No game-derived data, executable, APK, key or private analysis was uploaded to GitHub.

## Scope limits and next maintenance

This resolves the reported distant canopy admission error. It does not claim complete original-engine fidelity or all-zone PVS parity. Finite-portal character crossing is an explicit reconstruction policy, not a decompiled native actor implementation. Native per-neighbor portal clipping, complete authored per-tree LOD selection, and the 73 previously withheld scaled leaf transforms remain separate work. The corrected mode adds no fitted distance factor, capture-specific tree whitelist or tree-ID exclusion.

Build next with work/v46-canopy/build_renderer_batch.py after a source batch. The one-shot package recipe is package_android_v037.py; use a new output revision for future packages. Do not rerun historical one-shot integration/ownership scripts over live assets. Keep all original game-derived assets and analysis private.
