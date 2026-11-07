# Native bridge water contract and recovered reflection resources

2026-11-05. Focused offline analysis only. Canonical project AGENTS.md and REA skill were read. Existing native shader exports and recorded frame were reused; no original game, UI, helper, tool installation, native database or existing source/assets were changed. New work is confined to this research folder and its Windows counterpart.

## Actionable result

The custom river currently runs the wrong water-family approximation. Native `river`/`rivernopointlights` is a 92-byte depth/refraction material. Custom water[11] instead maps parts of that material into the separate 48-byte generic water shader: native reflectivity becomes opacity, gloss1000 becomes a horizon factor, and its ambient cube substitutes for a photographic reflection probe. The scene-color/depth inputs are absent. This explains a real contract mismatch without tuning color by eye.

Recovered all eight active bridge river/pond draws, their exact consumed constants, samplers, reflection probes, buffers and vertex colors. Four original reflection cubes are now available. The riverwater cube visibly contains the bridge forest, trees, sky and water; it is not an ambient cube. A reviewed GLES3 snippet `river_native.glsl` implements the recovered material equation and compiles with glslangValidator. It is a source-level integration component; no GPU/runtime parity claim is made here.

## Identity and evidence

Source recording `/private/tmp/oa-dalentarth-20261105.gfxr` SHA256 `72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209`, the already validated original frame. `active-water-bindings.json` replays descriptor writes and binds in the recorded JSON and joins the previously extracted full memory52 uniform snapshot. It retains exact write/bind indices, pipeline IDs, buffer offsets, resource creation descriptions and sampler states. `water-pipelines.json` contains actual captured pipeline state, not guessed state from names.

`image-provenance.json` gives exact binary recording block/file offset, stored size, decompressed size, mip sizes, image format and SHA256 for every resource extracted. The parser reads the pinned GFXReconstruct InitImage header from retained `oa-format-0918.h`: 48-byte fixed metadata, uint64 per-mip sizes, then optional LZ4 data. All decompressed sizes are asserted. BC1 bytes are the authoritative pixels; the RGBA derivatives use conventional integer BC1 decoding and rounding. Native BC1 hardware rounding can differ by a channel unit. Every cube includes its original compressed mip chain; RGBA derivatives are top mip only.

Shader evidence: active river VS945/955, PS946/956, alpha-only PS944/950; active waterfall VS1095/PS1096. SPIR-V disassemblies are retained. Shipped HLSL assembly3316e4b0586bb12a provides the named 92-byte material layout and the matching four-light river equation. Shipped ca77b6f297c27a99 provides the scrolling-waterfall family. Active material identity is independently proved by exact bytes rather than shader-family naming alone.

## Native material and reflection mapping

`decode_materials.py` reads the real BXML root pointer/count. Each24-byte parameter record is float4 value, u32 type, u32 name-key. Texture refs are u32 asset ID plus u32 slot. Values precede keys. The legacy generator searches a key then reads the next record value; several call sites deliberately/accidentally obtain useful following values. Do not shift every legacy caller globally. The native sidecar uses real key/value records and the verified material layout.

`decoded-materials.json` preserves all authored vectors, keys, types, texture slots, source paths and hashes. `resources/material-*-native96.bin` contains six vec4s for the native92-byte layout plus ignored padding. All eight recorded river/pond draws match their authored sidecar first92bytes EXACTLY, including captured padding; `material-capture-match.json` is the proof:

| Draw | Material | Native shader | Reflection image |
| --- | --- | --- | --- |
|72952|449423 riverpond|946 no point lights|5807|
|72957|404112 riverwater|956 four point lights|3594|
|72962|449423 riverpond|946|3549|
|72967|1423574 riverwaterfall|956|3594|
|72972|1436262 pln_riverpond|946|3594|
|72974|1436262 pln_riverpond|946|3594|
|72979|1423574 riverwaterfall|956|3574|
|72984|449423 riverpond|946|3574|

All probes are128x128, six layers, six mip levels, BC1_RGBA_UNORM. Reflection selection is per draw, not universally per material. Native HLSL names this dynamic `EnvironmentProbeMap`; authored material slot21 is insufficient to reproduce the per-instance selection. Native target sequence is +X,-X,+Y,-Y,+Z,-Z. `cube-3594-128-rgba.bin`, etc, contains six top-mip128x128 RGBA faces in that sequence. Upload face rows as recovered; OpenGL convention/orientation must be validated in the actual renderer. Images are UNORM, not sRGB.

The native riverwater values are tile(2,2,2), scroll(.03,.01,.03,.02,.03), reflectivity.7420110106, refractionScale.0320109986, fogDepth.000049999999, waterTint(.2,.239215702,.254901975,1), specularColor(.996078491,.917647123,.713725507,1), specularLevel.7, gloss1000, refractionBias.440820009. Native specularColor is declared but unused in this pixel equation; do not multiply it into the result merely because its name looks suitable.

## Scene resources and pipeline

River phase108 first copies prior scene then renders eight river/pond surfaces. Binding32 is8x8 ambient cube;33 is1536x864 D24 scene depth;34 is1536x864 RGBA8 pre-water scene color;35 base;36 normal;37 foam;38 detail normal;39 refraction normal/noise;40 dynamic reflection cube. Samplers17/18 are nearest clamp for scene depth/color; material surface maps wrap with linear/trilinear sampling; cube clamps. Preserve exact sampler structures in the JSON.

The scene-color/depth textures must be stable copies or otherwise legal read-only inputs distinct from the active render target/attached depth. Never sample the framebuffer currently being written. InitImage dumps of scene targets are frame-start bytes and do not by themselves reproduce the scene at phase108; the static reflection probe bytes are useful directly.

Actual river state: depth test LEQUAL, depth write OFF, alpha blending SRC_ALPHA/ONE_MINUS_SRC_ALPHA for color and alpha, backface culling, clockwise front. Phase109 repeats the river geometry with simple alpha-only shaders; its role in later compositing is not fully interpreted here. Custom direct forward blend can reproduce the visible color contract without claiming full native intermediate-target equivalence.

## Geometry and UV contract

Native48-byte vertex: position float3@0, UV float2@12, normal SNORM16x4@20, tangent@28, binormal@36, RGBA8 color@44. `buffer-provenance.json` plus `resources/buffer-*.bin` preserve the original river VB/IB InitBuffer payloads. The actual pipeline declares zero static stride because vkCmdBindVertexBuffers2 supplies48 dynamically.

River VS passes vertex color unchanged. Pixel uses RED, not alpha, to blend foam into the river surface. Captured riverwater VB10520 has varied grayscale/red149..255 and alpha254. Pond colors are white. Current generator discards river color and tangent/binormal; it only packs waterfall alpha into normal length. A correct river geometry path must preserve vertex red and its native tangent frame. Derivative-based tangent approximation is a known remaining approximation if retained.

Exact active VS UVs, with m[6] in the native layout:

    baseUV = UV + time * vec2(m[0].w,m[1].x) * m[0].x
    scrollingFoamUV = UV + vec2(time*m[1].y,0)
    foamUV = scrollingFoamUV*m[0].z
    detailNormalUV = scrollingFoamUV*m[0].y
    refractionUV = UV + time*m[1].zw

Base UV is not uniformly tiled by m[0].x; the tile scales its scroll term. The exact captured VS instructions are retained to avoid confusing this with an intuitively equivalent-looking authored-water UV formula.

## Pixel contract

See commented `river_native.glsl` for the full ready-to-integrate equation, including normal decoding, four local lights, native diffuse/specular, global tint and luminance adjustment. Its essential depth/refraction portion is:

    screenUV = saturate(nativeClip.xy/nativeClip.w * (.5,-.5) + .5)
    sceneLinearDepth = 1/(invDepthTransform.x*sceneDepth + invDepthTransform.y)
    deltaOriginal = originalSceneLinearDepth - nativeClip.z
    refractedUV = screenUV + decodedRefraction.xy*RefractionScale
    accept refracted sample only if refractedSceneLinearDepth > nativeClip.z
    delta = acceptedSceneLinearDepth - nativeClip.z
    underwater = mix(acceptedSceneColor, WaterTint, saturate(delta^1.5*FogDepth))
    underwater += enabled*(1-exp(-delta*FogDepth*waterFogDepthScale))*(.4*WaterTint-underwater)
    fresnel = clamp(saturate(dot(worldN,V)+RefractionBias),.3,.8)
    surface = mix(baseMap, probeReflection, WaterReflectivity)
    combined = mix(surface,underwater,fresnel)
    combined += enabled*((surface*(1-fresnel)+underwater)-combined)
    alpha = saturate((deltaOriginal*(.01+enabled*(waterFogOpacityScale-.01)))^3)
    albedo = mix(foamMap,combined,vertexRed)

Measured globals are waterFogDepthScale80, waterFogOpacityScale.01, enabled1. Thus opacity reaches1 at approximately100 game units depth difference; near-bank shallows become transparent continuously. Refraction uses the accepted/rejected sample delta; opacity always uses original unrefracted delta.

Preserve ORIGINAL D3D clip.z separately. The VS copies WVP clip.xyzw directly into the pixel varying. Do not substitute clip.w/eye distance; GLES gl_Position.z remapping must not alter this saved value. Bound inverse depth constants are(-.0381861589849,.0381880663335). For a live camera recompute the matching inverse depth coefficients from its projection or linearize in the same convention. The GLSL snippet explicitly adapts native upper-left scene UVs to GLES lower-left textures at every final sample, including refraction Y.

Normal decode uses(R*A,G), maps to[-1,1], reconstructs third component; the river intermediate is xzy. Mixed river normal is normalize((normal1+normal2)*(.5,2,.5)). Probe reflection is evaluated against this intermediate normal using reflect(-V.xzy,nr), before tangent-frame world-normal reconstruction. Preserve that order; sampling cube(reflect(-V,worldN).xzy) is not universally equivalent.

Native diffuse is cube(worldN.xzy)+(1-nDotL)*shadowColor+sunColor*nDotL plus four selected point lights in PS956. Native specular exponent is Glossiness*.25, with level SpecularLevel. The native river pixel does not apply generic distance fog at its end. Adding the opaque world's fog mix merely because current water returns early would create an unsupported change.

## Waterfall

Fourteen active draws73034..73190 use the exact for_waterfall material422631. Their64-byte vectors are scroll(0,.7,0,.5), unused declared specularColor(1,1,1,1), specularValues(5,999,0,0), selfIllumination(.176470593,.176470593,.176470593,1). PS1096 consumes two diffuse maps, green channels of two alpha maps, two normal maps and ambient cube. This family uses ambient cube for lighting; it does not declare the river reflection/depth contract. The current scrolling-waterfall p vector happens to match these scalars; the earliest parser suspicion is not a reason to blindly alter it.

Native alpha is alpha1.g*alpha2.g*vertexAlpha, with no current custom .004 discard. Current generator's max(vertexAlpha,.02) creates artificial opacity at zero-alpha edges; separate color storage permits the exact value. Current normal-length encoding, tangent approximation and local-light selection remain fidelity limits. Draw73214 is another scrolling-waterfall material and is intentionally not claimed to be for_waterfall.

## Checks and remaining gaps

- All eight active river92-byte blocks independently match authored material sidecars exactly.
- Original image/geometry payload decompressed sizes and per-resource SHA256 are recorded.
- Four recovered reflection face sheets were decoded; riverwater3594 shows the expected forest/sky environment.
- GLES3 source compiles successfully with the installed glslangValidator.
- No runtime, screenshots of a modified renderer, or original-game execution were performed by this research worker.

Integration still needs source/asset changes by the owning agent: stable pre-water scene/depth inputs, material sidecar upload, per-instance probe selection, original tangent+red-channel preservation and shader wiring. The full engine producer selecting nearest/interpolated environment probes beyond these recorded instances was not reversed here. Source-correlating recovered cube image3594 with a packaged cubemap asset ID remains open; actual recorded resource pixels and per-draw mapping are recovered regardless. Exact phase109 alpha-layer ownership and dynamic probe selection outside this bridge frame remain bounded unknowns. No whole-scene water parity claim is justified until runtime views are compared.

## Ready-to-integrate independent static water meshes

`build_meshes.py` emits eight OAWM files in `meshes/`, using native VB/IB asset bytes transformed by the native per-instance world/worldVector matrices. These are ordinary world-space static meshes; no WVP, camera, screen coordinates or recorded time are baked. Live camera/time continue to drive the renderer. `water-mesh-manifest.json` records exact bounds, original buffers, transforms, per-instance tint/luminance and hashes. Retained source transforms prove provenance; source asset/FAB IDs for these exact draw buffers are not yet correlated.

OAWM is little-endian32-byte header `<4s7I`: magic OAWM,version1,materialId,reflectionImageId,vertexCount,indexCount,stride72,originalDrawIndex. Then vertexCount interleaved float18 vertices: position3,UV2,normal3,tangent3,binormal3,RGBA4; then indexCount uint32 indices. Native triangle order is retained. All indices are bounds-checked against recovered VB and all output floats are checked finite. Native SNORM16 decode clamps -32768 to-1, transforms and normalizes each frame vector exactly as the active VS does. Output conversion uses CPU floating-point math rounded to float32, so native shader intermediate arithmetic may differ slightly.

For scoped replacement, compare world-space triangle+UV signatures with current cell geometry before suppressing legacy batches. The manifest bounds locate the corresponding river instances. Hiding a whole material globally would erase unrecorded water elsewhere; fallback should remain. Read the native shader's live world-space positions and camera, not recorded clip positions.
