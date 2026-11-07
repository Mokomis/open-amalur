# Static source attributes and exact material identity in18 reference cells

## Delivered

Recovered537source instances /108,786triangles across the requested shop cells x-1..1,y-11..-9 and bridge cells x0..2,y-15..-13. Source geometry matched actual current LOD0 cells with zero material-ID ambiguity. All output positions and UV0 are copied from actual cell bytes, preserving their current geometry. Source render records recover the real material ID per triangle; they resolve ambiguous legacy texture signatures instead of guessing one native shader per old material row.

`cell-overlays/` contains one OAWT file and `.remove.u32` per cell. `cell-join-manifest.json` records actual input cell hashes, joined counts, material families and maximum source position error.108,786triangles match:46,796vertexblendmodifiedmask;46,633dot3;12,552vertexblend;2,805trunkdot3.16cells source-match exactly; two have up to.03125game-unit source-vs-cell error. Every output still takes its geometry from the actual baseline cell. Unsupported triangles stay in the baseline.

Each remove file is uint32 positions in the ORIGINAL cell index array, each identifying a triple to omit when activating its corresponding native overlay. It is not a global zone triangle index. OAWT overlays are triangle soup in exactly remove-file order. Root may activate only the supported plain-dot3 subset; pair source triangle j's native material with remove[j] and preserve other baseline triples. Existing cell data was never written.

## Format

20-byte header `<4s4I`: OAWT,version1,stride76,vertexCount,indexCount0. Then interleaved76-byte vertices:

- float32 position3 at0
- float32 normal3 at12
- float32 tangent3 at24
- float32 binormal3 at36
- float32 UV0_2 at48
- float32 UV1_2 at56
- RGBA8 at64
- uint32 nativeMaterialID at68
- uint32 attributeFlags at72

Flags currently3 = native frame + source RGBA. All537matched source VBs are48bytes/singleUV, so UV1 duplicates UV0 and is explicitly not a recovered secondUV claim. Source56-byte layout is supported by the script but did not occur in this subset. Source60-byte layout remains fallback. Preserve baseline vertex/index/order for unsupported portions.

`source-provenance.json` retains source space ID/name, group/instance, FAB ID/name, assembly, real material ID, complete render record bytes, source mesh path/hash and source color ranges. `native-materials.json` preserves original material IDs, shader IDs/names, parameter value/type/key records, texture IDs/slots and file hashes. The reconstruction uses the same admitted pose recipe as current geometry, allowing exact source joining. It is not a proof that every nonunit native bind has been fully reversed. No camera/time/native framebuffer data is baked into the static overlay.

## High-impact material discrepancy

223source instances are actual `for_rock_cliffblend`414763, a vertexblendmodifiedmask material sharing its primary diffuse/normal/specular signature with plain cliff410101. Selecting plain dot3 from that shared legacy row loses the second material and green mask. Treebarkblend353286 has native vertex RGBA varying0..255; removing those colors loses diffuse tint and blend selection.

Bound native32-byte cliff constants(.924,67.12,0,0,2,2,1,1) match122active G-buffer draws, all pipeline12360, VS923/PS924. `cliffblend-bound-draws.json` retains offsets and indices. Its actual instruction sequence matches shipped e64a1080a0176273. This is corroborated family evidence; equal constants alone do not independently name every matched draw.

Barkblend353286 constants(1,20,0,0,1.2,1.2,1,1) match68active G-buffer draws, VS903/PS904; instructions match shipped ee25c36fd1dec8db. Again, constant agreement by itself is not a unique full material/draw identity proof.

Trunk evidence is stronger: six exact captured InitBuffer byte hashes match the source VB bytes for trunk FAB assemblies, yielding four actual G-buffer draws in pipelines8238/13167, VS883/PS884. `trunk-source-vb-hashes.json` and `trunk-capture-correspondence.json` retain the correspondence. PS884 instructions match shipped3cec76619974c89f. All relevant HLSL and SPIR-V files are retained.

## Ready material GLSL

`material_contracts.glsl` contains reviewed GLES3 helper functions returning native albedo, perturbed normal, raw/saturated specular and stored gloss, plus native ambient cube/sky contribution. Syntax validation passed with installed glslangValidator. These helpers do not recreate the entire deferred shadow/AO/combine pipeline.

Vertexblendmodifiedmask uses vertex alpha A:

    low=saturate(2*A); high=saturate(2*A-1)
    weight=mask.g*(low-high)+high

Ordinary vertexblend uses weight=A directly. Native UV1 for these shaders is UV*UTile,VTile; layer2 UV is the same sourceUV*UTile2,VTile2. They do not require an invented second sourceUV channel.

Diffuse is mix(diffuse1,diffuse2,weight)*vertexRGB. For normal mixing, sample packed normals, first replace R with R*A in each, interpolate encoded(R*A,G), then map XY to[-1,1], reconstructZ and transform by nativeTBN. Do not decode each normal toXYZ and interpolate afterward; that is a different function.

Specular strength uses mix(spec1.g,spec2.g,weight)*SpecularValues.x. Stored gloss is constant SpecularValues.y, without sampling the blue channel. Native deferred exponent is storedGloss*.25. Native ambient q uses the RAW strength times ambientSpecularScale; the G-buffer specular channel itself saturates separately. The helper preserves both values.

Trunkdot3 uses diffuse*vertexRGB, packed normal(R*A,G), specular GREEN*strength and constant gloss20 for these two authored trunk materials. Native PS884 has no alpha discard and does not read its declared alpha-map resource. Do not blindly apply the old filename-selected cutout heuristic to this supported trunk path. Broader shadow-pass alpha ownership and VS wind/dissolve behavior remain independent work; normal-vector fourth components are not preserved in this sidecar.

## Additional texture resources

`material-texture-plan.json` maps native texture slot IDs to existing texture indices by reconstructing actual build_textures.py key order (assetID,alphaID,kind), then verifies all255base material rows. One already missing source reference remains0xffffffff.30native material profiles occur in this subset. Native slots:0diffuse1,1mask,2specular1,3normal1,8diffuse2,10specular2,11normal2.

19new files under `extra-textures/` contain ready OATX RGBA8 UNORM resources with source archive/file/SHA provenance in `extra-texture-manifest.json`; they include original mask510546 and missing secondary normals/specular/diffuse maps. Original alpha is preserved, so the real green mask is available. Existing alpha-combined diffuse variants must not be treated as raw mask resources merely because their RGB happens to match. Resources use a source mip at most1024 and generated BOX lower mips; native compressed lower-mip and hardware rounding parity remain qualified. Asset0 and365597 remain unavailable; retain fallback for unsupported material slots.

All archive extraction went to this NEW research subdirectory using the existing installed unpacker. No reinstall, original game/UI launch, native database access, or existing source/asset edits occurred.

## Water suppression completed

`water-hide/legacy-hide-*.oawm` contains ALL8recorded river instances transformed with the OLD/current geometry recipe for precise legacy suppression. They share the normal OAWM format, but are matching aids, not render replacements. `legacy-water-hide-provenance.json` proves captured VB+IB byte identity with source FAB/assembly and exact serialized translation match with the native instance.

The two earlier nonunit failures are resolved:72979 is FAB1425104 for_river_fallfree05 with legacy position delta(+27.700,-33.561,0), and72984 is FAB1616984 for_river_pond_02 with delta(+17.448,-3.069,+.0473). Root can now match actual cell triangles by these OLD worldpositions+UV and remove every equivalent copy, then draw the correctly transformed native replacement mesh. This avoids material-global/bounds-only deletion.

## Remaining scope

LOD1/2 positions are vertex-clustered, so their attribute ownership requires replaying the existing clustering provenance or a separate exact source join. They remain baseline fallback here. Source material shaders beyond these three families, vertex fourth-vector/wind metadata, exact native mip filtering, and full deferred lighting are not solved merely by recovering attributes. No integrated-renderer visual parity or gameplay performance claim is made by this worker.
