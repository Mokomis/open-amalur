# Family8 implementation review

No concrete implementation mistake was found in the new family8 branch or native-profile acceptance. This review uses actual source snapshots retained beside this report, not earlier proposed snippets.

- `oa_post.c:58`: raw spec is specularMap.g*sourceStrength; vertex alpha affects G1 spec only. Base is diffuse*vertexRGB*vertexAlpha. Emission is mask.g*rawDiffuse*emissiveRGB*strength without vertex colour/alpha. `unpack` at26 matches DXT5nm; branch8 passes raw N0/TW/BW and normalizes the final result once.
- `oa_post.c:64`: family8 q uses raw spec directly, avoiding a second strength multiplication or vertex alpha. Pre-Gbuffer materialN/materialBase remain available for native ambient. Emission is added inside G2 clamp, then HALF-rounded, before shared AO. Gloss maps to full HALF sourceGloss before the deferred*.25 exponent.
- `oa_post.c:18`: UV scroll is game_time*material_tiling.zw. The game_time setter exists in android_scene.c:394. Profile.xy unity/zw zero correctly implements this lamp material.
- `oa_stream.c:98`: native profile acceptance explicitly allows8 while retaining existing1..6. It reads8 texture indices and12 floats at the correct84-byte row offsets, and a299-row table is within material_count299. profile.native_uv.x=1 selects native_t bindings0..7 for opaque phase0.
- Staged row298 has family8; D/N/S/mask693/694/695/696; colour(1,1,1,unused0),specular(1,20,1,0),UV(1,1,0,0). MATS BACK/no-alpha routes it to opaque phase0. Aux header materialCount299 agrees.

Full source snapshot SHA256 values:

- oa_post.c: `3f9313690b2f57d9098858cb5044c15681d130433231434743ce58af77f7d44d`
- oa_stream.c: `6ef39c8860b2ef7380980c2a6b8f0b21c7e7208d489b13d4084f5a2831299691`

No code changes, repeated400-case test or GPU run were performed. The earlier independent active838 formula validation remains the arithmetic evidence. Final merged live asset tables are a separate pending integration check; this review confirms code acceptance and staged row candidates.
