# Native placed-object visuals â€” 2026-11-05

Continues v40 Windows custom-engine development and v41 placement decoding. Actual original bridge footage/frame remains the visual reference. This work does not resume the original-engine native port.

## Recovered path

- Reused the existing patch compiled-Type batch reader (27,350 members), SHA256 09dff529684d2deef530a418c11b0729fedb6b89f85e61cdd84f04f18942268c. Original Workbench bytes had already matched this runtime carrier.
- Reused native component kind 7 (PartRenderingBlueprint). Exported original routine 00f0cc50 converts the five reference fields +0x14..+0x24. Primary +0x14 has the previously established FAB role. The exported routine plus entry bytes are retained privately here; no original database or executable was modified.
- Mapping 2,562 Dalentarth placed records found 1,945 instances with direct rendering components, 1,743 with named primary FABs. Six missing types and 611 without direct rendering stay unresolved; no parent rendering inheritance was invented. This catalog includes characters and non-static objects, so it is not a count of newly supported static props.
- Selected six smashable crate types, six FABs, all with one unskinned stride-48 assembly and an identity rendering bind. All placements have unit scale. Native conjugated quaternion convention from v41 determines world rotation. No handmade offsets or visual nudges.
- All six FABs reference material 301326. Native texture slot table holds diffuse 298941 at slot0, white 250070 at slot1, specular 298943 at slot2, normal 298942 at slot3. Current custom-shader role assignment follows those texture symbols and the existing host shader convention; exact original shader behavior is not established.
- Larger KEEN carriers can stop above 4x4 (e.g. 2048 through 8). The bounded overlay reader honors stored mip count and requires exact span consumption; the old strict small-carrier decoder is unchanged. Base textures are decoded at <=1024 and lower mips generated for this desktop diagnostic, consistent with the existing custom pack policy. No source archive changed.

## Implementation and verification

map_object_visuals.py writes the private catalog. build_crate_overlay.py first proved five crate01 placements near the captured space. The original-camera image crate01-reference.png shows the missing foreground crate at its recovered position.

build_all_crates.py extends this to 213 unique native instances across Dalentarth, adding 170,264 triangles at each of the three existing stream detail levels in 40 cells (120 cell files). It reuses the current stream format and shader, appends one material and three RGBA8 texture chains, and updates bounds/counts. No C compilation is needed for this content change. All former draw records, vertices and indices in modified cells are byte-identical. Every added index is in range and all positions finite. The six crate FABs occur zero times in the existing static import groups; no already-baked crate geometry is duplicated. Evidence: all-crates-validation.json and all-crates-manifest.json.

Only Windows desktop assets are changed. Original files are preserved under before-all-crates; the first small experiment has its own before-world copy and was restored before the full overlay. No APK, tablet install, signing key, user save, original-engine database or original-game save was changed.

## Use / rollback

Close the custom preview cleanly before changing assets. From this folder:

- `python deploy_all_crates.py apply`: apply hash-checked desktop content.
- `python deploy_all_crates.py restore`: restore backed-up original pack and remove only exact generated new textures.

Both commands refuse an active preview and validate the whole file set before writes. They use temporary replacement per file; this is not a filesystem-wide atomic transaction. Do not interrupt deployment or modify the live pack from another chat. The preview is currently in reference-camera mode for validation; use the v40 launcher for normal walking after closing it.

Generated data, captures, game metadata, decoded binaries and native decompilation remain private, excluded from source commits.

## Limits

These are static reference visuals. Destruction, collision, loot, save-dependent state, triggers and original physics are not implemented by baking a mesh into a stream cell. The historical custom combat/AI is authored. Do not claim exact visual parity: terrain painting, vegetation, water, fog and lighting remain visibly different. No Android install or new performance measurement has been made. Do not infer Android performance from the readback Windows preview.


## Current deployed content — supersedes initial crate-only scope

build_static_props.py / deploy_static_props.py are now the current tools. They include 213 crates, 30 barrel01 instances and 8 urns: 251 objects, 180,472 added triangles per detail level, nine FABs, three native materials, nine texture chains, 42 cells / 126 cell LOD files, 138 changed files total. Validation: static-props-validation.json. Recovered objects use their exact stored placements; original packed world geometry remains byte-identical. All nine FABs occur zero times in the earlier baked static groups. The current before copy is before-static-props. For apply/restore use `python deploy_static_props.py apply` / `python deploy_static_props.py restore` with the preview closed. Earlier experiments were restored before this deployment and remain saved.

Static-props-reference.png is a fresh original-camera GPU capture. Runtime log shows the cells and textures loaded; runtime-verification.json records actual stream observation/errors. The known frame1 GL_INVALID_OPERATION persists; no subsequent GL/stream error was observed in this run. Do not interpret unsigned Windows audio_xruns or readback profile timing as Android measurements.

Barrel02 (FAB1425589, 16 placed instances) remains omitted: its rendering bind is a non-identity 15-degree rotation and the general native bind convention is not yet established. Its destroyed-state type is also omitted. Native bone binding must be traced before adding it; do not casually apply the historical reference candidate. Barrel/urn audit: barrel-urn-bind-audit.json.


## Collision experiment — prepared, NOT deployed

build_visual_collision.py derives optional static collision from recovered visual triangles. It removes 1,182 degenerate triangles and bins 179,290 triangles into 45 cells. All original collision bytes are preserved. Every affected 3x3 neighborhood stays within the controller's 300,000-triangle limit (peak 228,015). This is an authored static collision policy, not native physics/destruction recovery.

The controller probe compiled and ran. The first comparison relocated one spawn onto a crate, so it is not blocking proof. Same-start variants either hit an existing terrain edge or failed capsule-clearance selection. No useful integrated walking-block comparison was established. Logs are retained in collision-*-results.json; do not call these passes. Collision remains undeployed. deploy_visual_collision.py is available for a future focused check, but only the visual props are active. No tablet build/install was performed.

Non-identity local-bind investigation is bounded in NATIVE_BIND_NOTES.md. No rotated local geometry was added from an unproven convention. The current preview shows the fixed reference camera; the owned scheduled task is configured for normal town mode on its next launch.
