# Well of Souls opening content — staged only

First playable room: SPACE1417252 / REGION1262814. Later LAB549780 is a different scene. Original cinematic script1411319 sets post-character-creation spawn (4312,2806,-314,-180). Only room1 has collision under this XY, with nearest floor Z=-314.79069,0.79cm below spawn. Lua/services agent owns the cinematic/quest behavior.

## Runnable-format portable preview

Asset root: work/v48-opening/content-audit/portable-preview/. The parent's asset-root adapter should serve its world/ directory. No live promotion or GPU launch was performed. portable-preview/preview-manifest.json has local IDs, all exclusions and SHA values.

| File | Existing reader format |
|---|---|
| world/index.bin | OAWI20B header +70 empty-base48B cells; baseLOD triangles0, no c-files requested |
| world/region-index.bin | OARGIDX1 24B header +13 rows40B; materialCount29, neutral distanceScale1 |
| world/rCX_CY.bin | OARGEO1 28B header +48Branges +OAWE76 indexed vertices +u32 indices |
| world/materials.bin | u32 count29 +29 rows28B |
| world/native-materials.bin | OANM001-null8B +u32 count29 +29 rows84B |
| world/t0.bin..t97.bin | OATX RGBA8, explicit <=512 authored mip tails, no resizing/generated mipmaps |
| world/kCX_CY.bin | 70 files: u32 triangle count +float32 XYZ triangles;42,044 source triangles |
| world/lighting.bin | Deliberately absent, per parent: OALG native globals are not source SkyLightColor; room universality unproven |
| environment/ | Authored room environment for parent's new scene reader |

Preview world size170,549,416B. Retained1,148 source ranges,482,509 stored triangles and1,275,865 all-range triangle references; authored exclusive ranges must not draw simultaneously. Full76B vertex records and index-triangle vertex sequences for retained geometry are byte-identical to the full candidate.

Supported materials:22 dot3,5 dot3alpha,1 vertexblend,1 vertexblendmodifiedmask, existing families1/3/4. Parameters come from exact typed/hash records, and actual source texture slot numbers. Alpha uses raw source slot1 GREEN through native t6 with original cutoff. Source cull NONE/BACK enum0/2 is independent of alpha. MID474330 has a source asset0 slot retained as NONE; native null-binding fallback behavior was not separately observed.

Explicit exclusions:1,127 unsupported-family ranges/741,973 all-range triangles (25 source MIDs), plus65 nonunit-transform ranges/26,827 triangles. All nonunit transforms are quarantined, not just the51 sphere outliers. No unknown shader is replaced by a generic/tinted approximation.

## Preserved full candidate and texture evidence

candidate-first-room/world/ retains all four source collections:2,340 ranges,862 shared geometry keys,869,763 vertices,768,886 stored triangles and75,442,004 geometry bytes. geometry-manifest.json, source-range-provenance.json, direct-trs-bounds-audit.json and first-room-assembly-range-audit.json preserve uncertainty. This candidate lacks material banks and is not independently ready to load.

candidate-first-room/textures-native-bc/ has166 full authored BC1/BC3 chains,365.83MiB. textures-portable-512/ has166 RGBA source mip tails,184.48MiB. textures-cube-native/ preserves9 six-face source carriers. One format2 blank is unsupported, not called a real decoded replacement. texture-stage-manifest.json records per-level SHA values and independent scalar-vs-Pillow sample checks on each portable mip. Full2.30GiB RGBA expansion was not emitted; Android GLES BC support is not assumed.

Source minSq/maxSq and lower raw flags remain unchanged. Identical Fab/assembly/MID/TQS keys have zero interval overlap. Neutral registry scale1 is explicit staging; native shared quality default4/effective scale0.5 is known from binary/outdoor runtime, but no opening runtime setting was observed. Current generic stream reader does not reproduce every native per-pass exclusion mask; flags are retained, not reinterpreted.

## Authored environment

portable-preview/environment/environment-manifest.json includes REGION1262814's base profile and separate shipped base/start/cinematic XML profiles. point-lights.bin: OALP108-null8B,u32 count113,u32 stride108, then unchanged native records. Each float27 record:positionXYZ;four key RGBs;four multipliers;four attenuation starts;four attenuation ends. Key order Midnight,Dawn,Noon,Dusk.

ambient-cube-0.raw and ambient-cube-1.raw each retain six8x8 source faces,1536B/cube. Parent must apply existing reviewed cube channel mapping. Exact16-cubed RGBA LUTs:1315352 wellofsouls_cc(base/cinematic) and1529772 dgn_contrast_cc(start).

Base/start profiles differ in color/fog and brightness1/1.2. Selected scripts have no proven override selection, so no automatic start profile is chosen. No outdoor Dalentarth constants were copied. Parent must wire room points,cubes,fog,sky,LUT before claiming lighting parity; existing compiled outdoor constants otherwise remain in use.

## Route and trigger evidence

1262814-portal-graph.json contains nine authored links:1→1b→1c→2→3→4→5→6→7→8. Source endpoints+0x9c/+0xa0 in164B root+0xc0 records follow the recovered native graph reader. LAB is separate and has no such links; its later exit reaches West431646.

opening-volume-world-contract.json has named source96B script volumes for rooms1/1b/1c/2, original cube corners/plane triples,TQS,world vertices,planes,AABBs. Authored spawn point is inside WoS_Start_Room and Tutorial_Volume_Move. Native entering-object shape,tolerances,callback ordering remain separate from this point diagnostic.

Cached native evidence:00fdc910 assigns root+d8/dc to SPACE+74/78;00ff04f0 calls00fef2d0;00fef2d0 advances source96B/runtime168B;00fbdbc0 reads name+1c,script+18,flagbit+54;00fb0f60 reads S+48,T+28,Q+38 then00adcd40. Static collection loader00fec370 is preserved in native-evidence/. No Ghidra DB or original game state changed.

## Reproduction and integration boundary

Use stage_portable_preview.py, stage_first_room_geometry.py, catalog_opening.py, stage_room_textures.py and stage_environment_volumes.py. content_sources.py invokes existing installed pakfileunpacker only, extracts into this audit folder and records DATA→initial→patch precedence/hashes. Never run old destructive build_zone/build_world_pack over live assets.

No dynamic actors/37 actor80 visuals,skeletal mobs,particles,cinematics,inventory orquest logic are bundled in this static preview. Original save data and outdoor assets are untouched. Parent owns scene selection,environment integration and Windows/Android validation.
