# Shared character appearance assets

Private Windows stage: C:/Users/rwill/Documents/Opem Amalur/work/v50-character-complete/appearance-assets. No live engine, default assets, prior packs, original archives, database or saves changed. No Mac mirror.

## Integration

Compile oa_appearance.c and oa_appearance_selection.c, with oa_appearance_selection_data.h. Public headers: oa_appearance.h and oa_appearance_selection.h. Cache models/<FAB>.oaam by original FAB ID; lookup returns a borrowed oa_am_model. Caller owns CPU bytes and GPU surfaces/materials.

1. oa_ap_plan_build resolves profile, explicit CREATOR/GAMEPLAY form, original cosmetic SimType IDs and actual equipped item IDs. ID0 initializes from original source defaults/first hidden Ear; invalid IDs are rejected.
2. oa_ap_plan_pose consumes an explicit matching form/rig clip frame's raw local Q/T/S and fills every component's complete own skeleton. NULL selects the explicitly named source rest path. No ancestor collapse.
3. oa_am_surface_get returns native MID, canonical96B vertices, indexed triangles and exact source remaps. oa_ap_component_surface_visible admits authored near group1 for this close preview; it never submits all LOD aliases together.
4. oa_am_palette composes current component world bones with source remap TQS, then optional entity/world matrix. Supply complete per-surface palettes to the cosmetic renderer, plus separate entity-only direction rows for native unskinned B.
5. Resolve native material/texture IDs through ../materials. SkinTone/head/body diffuse overrides and colors remain explicit caller state; the plan supplies selected tattoo texture ID.

delivery-manifest.json hashes all runtime payloads:189 shared models,28 form/rig clips,5 C/header files;43,711,823B. Reuse by asset identity; no40 duplicated preset packs.

## Forms and animation

Eight creator Types use1507280(male)/1507282(female). Final Types669805..669808 use456813/611642. All four roots have64 joints. Components retain their own1..64 bones and source palettes(max31), including facial/hair/ear nodes.

clips/<rig>-<clip>.local-trs.bin has12B little-endian header(u32 joints,u32 frames,f32 fps), then frame-major/bone-major48B Qxyzw/Txyzw/Sxyzw. Raw Edge quaternion is retained; matrix conversion conjugates XYZ once. All28 clips have64 source channels and exactly unit XYZ scale.

| Role | Male | Female | Frames |
|---|---:|---:|---:|
| Ordinary Player idle |703318|1293793|101|
| Window Win_Face_Idle |1576362|1666387|271|
| Player walk |457557|656035|33|
| Player run |457536|655636|21|

Creator roots carry5 ordinary idle variants and window idle. Gameplay roots carry their own-rig decodes of these plus walk/run. Profile fields expose creator ordinary/window idle and gameplay idle/walk/run. Window state is an exact counted first-slot join: MotionSets1438362/1438379 key9624060 slot0, one variant/clip at file256. Player sets103195/666245 are actual full-rig references and contain the gameplay clips. Complete chooser/blend/transition/root-trajectory timing is not implemented; sampling/loop policy remains explicit.

creator-clip-receipt.json and form-clip-receipt.json preserve commands and hashes. Existing offline clip-bake.exe privately mapped PE sections and invoked pure Edge0111bf10; no game entrypoint/imports/UI/process/save activity.

## Native selection and pose evidence

Cached functions correspond to PE SHA16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314. Copied bodies/hashes: native-evidence/ and delivery manifest.

-00f268d0 copies Rendering+18/+1c/+20 to runtime+2c/+30/+34;00f76530 copies Stats+8 to runtime sex+28;00f5c080 selects male0/female1 model. All source rows resolve valid variants.
-00cf4c90 replaces a base attachment by exact slot key.00f11830 combines source zero-slot controls/base pairs;00f5ee50 builds base attachments by secondary slot key, ignoring unmatched keys.
-00f10660 resolves inventory primary/alternate aliases against ROOT maps first, falling back to Head only when absent. Female hair can attach to root while male hair uses Head.
-00d3c980/00d064d0 load FAB child-map blocks:12B parentBone/childBone/thirdRaw entries plus9B alias/slot/flag. All3093 retained third words are0.
-00d2dbc0 admits a child through00c8b130's mapped-child-index check.
-00d250c0→00ce26e0→00ccd2c0 copies mapped parent global TQS into child, then composes unmapped nonroot source locals under updated child parents.
-00cae460 composes weighted source remap with current bone and emits3x4. Rigid path uses bone/world without inverse bind.00ac5770/00ac4b10 establish quaternion convention.

Ordinary child pose branch is implemented. Previous-pose/additive preservation controlled by native instance bit8 is not invented; active expression/override state needs separate supplied state/pose.

All visible current cosmetic/Tatters scales are1. Starter Unarmed source scale.8 selects empty FAB1324209. Visible nonunit equipment is rejected until its native scale path is integrated.

## Model format

OAAM001 magic8 + six u32(version,fab,totalBytes,chunkCount,directoryOffset,reserved):32B. Directory entries16B(tag4,offset,count,stride).

| Chunk | Record |
|---|---|
| BONE64 | parent i32,hash u32,raw source Q/T/S48,8reserved |
| ASMB128 |16u32 then16f32 |
| VBUF32 | raw offset/length,stride,count,canonical offset/length,headerword,presence flags |
| IBUF16 | u32-index-byte offset,count,source IB offset/length |
| RAWV | exact source VB bytes |
| VERT96 | canonical vertex view |
| INDX | source indices widened exactly to u32 |
| RMAP52 | exact runtime TQS48+boneID |
| CMAP32 | pair start/count,alias,slot,flag,source offset,2reserved |
| CPAI12 | exact authored triples |

ASMB words0/1 VB/IB;2 MID;3 rigid bone;4/5 remap start/count;6 group mask;7 native weighted flag;8/9 source assembly/descriptor offsets;10 stride;11 declaration enum;12 source flags;13 shader;14 variant. Floats start sphereXYZ/radius then source min/max distances.

Canonical96 offsets:P0,J4bytes12,W3float16,UV0@28,UV1@36,N44,T56,B68,RGBA80,presenceFlags84,sourceVertex88,reserved92. Native signed joint declarations retained as raw bytes; all admitted values0..30 so canonical unsigned view preserves values. Source SNORM.xyz and native reconstructed fourth weight preserved without clamp.

Admitted native layouts:56/type17;60/type22;64/type25;68/type26. Raw68:UV1@32,N40,T48,B56,RGBA64, corroborated original declaration+exact type26 joins. Missing authored COLOR stays absent/zero; renderer's separate128 policy supplies proven native shared-white streams. Raw source never replaced.

## Validation and qualifications

production-loader-test.log:189 models,717 surfaces,0 unsupported;1,278 default/individual-option plans across both forms; head-dependent-validation.log extends this to4,868 total plans including every Head x Hair/Beard/Ear/Accessory pair; invalid IDs rejected;112 form-clip/profile plans and13,584 frames yield finite complete poses and valid endpoint/midpoint palettes.

independent-validation.json:184,956 vertices,900,633 indices,4,576 bones,5,448 remaps,3,093 child pairs independently match raw source. UV/TBN/RGBA/SNORM match declarations exactly. Independent source equations versus production C animated poses:max matrix difference3.302e-5; algebraic/native-source proof, not bit-identical native floating execution.

option-vetting-matrix.json/.csv:184 unique options,631 race/sex-compatible rows. Source/native layout/CPU checks are distinguished from original-game availability and visual comparison. Parent owns original-game comparison; no original game launched here.

Parent owns original effective-state-dependent resolution of5 historical preset errors. This loader accepts resolved original IDs and preserves raw source tables.

DLC false/true top-level extraction changes4 nonappearance tables, no appearance/default/preset tables. Source row+4 is condition_handle_raw, verified unchanged through native loader by independent creation-gameplay/availability-audit. Its archive-key join is now exact through original assetinfos.bin, record5695447: key330590315 maps to main_table.conditional_expression. Entry2 is native unconditionalTRUE/status0 for this current184-row catalogue; a generic availability implementation must still fail closed on unresolved references. No live original-game execution or claim about other DLC catalogues.
