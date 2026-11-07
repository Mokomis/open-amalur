# Native final filter and sky reconstruction

2026-11-05. New files only in this folder. Existing native exports, original frame recording and extracted assets were read. No original game, live renderer, UI, database mutation, installation or helper inference occurred. Root owns shared implementation and GPU integration.

Reference recording SHA256: 72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209. Shader modules and raw constants are retained with phase-bindings.json. The enclosing research manifest identifies the native executable.

## Delivered code and integration

oa_native_filter.c/.h and native_filter_shader.h implement the active final filter with its native control flow. Open with input dimensions, render merge/LUT into its RGBA8 target via begin(), then draw() to the output framebuffer. The merge shader must write alpha=dot(final graded RGB,(.299,.587,.114)). Filter alpha is luminance input, not opacity; filter output alpha is1. Native input/output are1536x864. A different output size is an explicit resampling operation, not another captured parity claim.

oa_native_sky.c/.h and oa_native_sky_geometry.h implement the actual sky mesh, vertex mapping, two cloud layers, gradient sampling and native luminance adjustment. The procedural mesh matches every captured vertex byte and every active index byte. It uses current FULL GL view-projection, preserving native fixed world sky geometry rather than recentering a guessed unit sphere on the camera.

oa_native_sky_open_assets(p,manager,lowerPath,upperPath) reads the two OATX assets one mip at a time, creates and owns their textures. The original open(p,lowerGLuint,upperGLuint,gradient512) API instead borrows cloud textures. close() deletes owned resources only. draw(p,liveGLVP,params20) consumes native constant vectors4..8. bridge_noon_parameters(params,time) explicitly supplies the captured Noon reference contract; it is not a universal time-of-day model.

emit_sky_assets.py --output NEW_DIRECTORY --rgba generated native-assets/native-sky-lower.oatx and native-sky-upper.oatx. These are ordinary project OATX files: magicOATX, GL_RGBA8, width/height/level count, then byte-count plus pixels for each of the9 authored mips. Lower is4096², upper2048²; no512 cap or regenerated mip chain. Files are89,478,200 and22,369,592bytes. Their source BC3 chains and authored Noon gradient are validated against original captured images. The emitter reads existing files only, writes only its selected output, uses the existing keen_texture decoder and installs/extracts nothing.

Both modules compile cleanly with Windows MSVC /W4 and root's desktop_compat forced include. Both sky shaders and the complete final-filter translation pass GLSL300ES syntax checks. No GPU execution or final visual parity is claimed here.

## Final filter: active stage and exact source contract

At phase135 draw73404, module1858 combines base scene, effects and reconstructed bloom, applies the generated correction atlas, then emits corrected RGB and luminance alpha(.299,.587,.114). It writes RGBA8 image179/view239.

At phase136 draw73411, pipeline7607, vertex1859/fragment1860 samples that same image through view181 and writes the1536x864 UNORM output image. No additional exposure, colour table or ordinary scene-AO multiplier occurs here.

Fragment1860 has an early contrast test, a bounded6-iteration edge search and the native filtered-colour rescale capped at4. It emits the source centre RGB on the low-contrast branch. The edge branch computes a shifted sample and preserves native luminance-dependent colour scaling. Threshold constants include1/6 and1/12. Sample operations use explicit LOD0, cardinal and diagonal integer neighbour offsets, and the original edge-search steps. native-1860.frag retains every SPIR-V result ID so its arithmetic and branch provenance are reviewable.

translate_filter.py maps the original structured CFG directly: outer branch187/188→189, loop620/621→623 with continue622, and inner branch763/764→765. It fails on unknown operations/targets. The GL shader maps framebuffer bottom-left coordinates to native top-left texture coordinates and inverts integer neighbour-offsetY at textureLodOffset. These adapters affect coordinates, not colour arithmetic.

Native sampler148 is LINEAR with REPEAT in both axes and no mip interpolation; it is not clamp-to-edge. The module owns a matching sampler so borrowed source textures cannot accidentally change this behavior. Its RGBA8 target and no-dither state retain the native quantization boundary. Code, shader compilation, CFG inspection and capture identity are verified; a GPU comparison remains root's test.

## Native sky geometry and mapping

Active sky is phase107 draw72940, pipeline7547, vertex1876/fragment1879. Vertex input is576 records of20bytes: float3position and float2UV. Index count1722, uint16. Native geometry uses a420000-radius hemisphere shifted downward210000 along worldZ. Six15-degree vertical bands and24 angular segments generate576 vertices; the native indexed strip-to-triangle pattern includes its original degenerates.

Producer FUN_00d1f6f0 uses:
- radius global019662cc=420000;
- angular-step globals019662d0/d4=15;
- degree-to-radian constant013bf670=.017453279346227646;
- accumulated float angles, float sin/cos values, double radius products and float output positions.

sky-generator-assembly.txt preserves the decisive x86 instruction ranges. Replacing this constant with full-precisionpi/180, recomputing angles from degrees independently, or rounding intermediate radii tofloat changes native vertices. The delivered generator reproduces all11,520vertex bytes exactly and all1,722active indices exactly. Production code contains no frame vertices, player position or room/save selector.

For vertexpositionP and authoredUV.x:
- gradientU=UV.x, equal to cos(inclination).
- cloud coverage=clamp(P.z/140000+2/7,0,1).
- lower-plane varying=(P.xy*.300000012,P.z+208010).
- upper-plane varying=(P.xy*1.25,P.z+320010).

These varyings interpolate over the native mesh. The native pixel shader normalizes each plane vector before division; code retains that operation.

Upper cloud samples (upperPlane.xy/upperPlane.z + time/2048)*2. Lower cloud samples (lowerPlane.yx/lowerPlane.z + time*(3/1024))*4. Upper is composited over gradient first; lower is composited over that result. Each opacity is textureAlpha*tintAlpha*coverage. Gradient alpha is NOT used by this active variant.

The final sky adjustment is C + luminanceFactors.w*(dot(C,luminanceFactors.rgb)*luminanceTint-C). Captured luminanceFactors.w=0, so this branch is neutral for the reference. There is no invented lower-horizon fog replacement, direction normalization for a unit dome, extra LUT or forced clip-depth constant.

The mesh is transformed by the full native view-projection. Native sky raster state is no culling/blending, depthLEQUAL/no writes and stencilEQUAL reference0 (background). The module can draw as background before visible colour geometry using matching depth coverage; it does not reproduce a missing native stencil producer by guessing. Root must retain rendering order and restore ordinary depth/raster state.

## Sky texture identity, gradient and constants

Captured lower binding32/view13028 is4096² BC3_UNORM image13024. Its mip0 and all9authored mip payloads match extracted710562_1.dds exactly. Captured upper binding33/view13887 is2048² BC3_UNORM image13880; all9mips match159747_1.dds exactly. The existing build_sky.py's lower/upper identifier labels were reversed relative to active HLSL bindings. This is proven by byte identity and shader use, not by texture filenames.

Shipped eb22737fa46893d9.asm names t0 lowerCloud, t1 upperCloud, t8 gradient and agrees with active1879. cecafe65b2d06197.asm and272904a3620a5a4c.asm are transition variants, not the selected frame variant. Cloud sampler149 is trilinear, repeat/repeat, no anisotropy; captured image views expose9mips. Module samplers preserve this and clamp maximumLOD8.

Gradient binding40/view4586 is32x4 RGBA8_UNORM image4582, sampler1882 linear/trilinear with Urepeat and Vclamp. Noon V=.625=(2+.5)/4. No256x1 approximation or half-texel rewrite is used.

The GFXReconstruct InitImage record contains1024bytes for this image, but only its tightly packed32*4*4=512bytes are image pixels; the remainder is recording allocation padding. The existing official source file_processor.cpp reads InitImage level sizes; vulkan_replay_consumer_base.cpp sets bufferRowLength=0 and bufferImageHeight=0. Extraction preserves the entire metadata payload and separately writes sky-gradient-tight.rgba. Similar end-of-level alignment padding is removed before comparing small BC3 mips.

Noon gradient row2 independently matches the authored325844.sky_bxml at32samples t=i/32, truncating each interpolated channel tointeger. All128bytes match captured row2. The preserved full512-byte header supplies the native asset's four rows; this pass does not claim to have repaired the older parser's handling of all other authored time keys. The emitter is explicitly scoped to the Noon reference and records source hashes.

Captured vectors4..8 are:
- lowerTint=(1,1,1,1);
- upperTint=(1,1,1,1);
- transition=(0,0,.625,75.51945495605469);
- luminanceFactors=(.21176472306251526,.7137255072593689,.07058823853731155,0);
- luminanceTint=(.6039215922355652,.2549019753932953,.29019609093666077); trailingW is unused.

Both white tints agree with the authored Noon sky record. The time is an explicit snapshot value; normal operation should supply current engine time, not force it globally.

## Evidence and remaining limits

phase-bindings.json and constants-phase*.bin preserve active descriptor offsets/resources. sky-geometry-validation.json proves procedural geometry identity; sky-asset-validation.json proves all captured BC3 mips and Noon gradient identity; native-assets/sky-assets.json records emitted OATX mip shapes and hashes. Raw SPIR-V, disassembly, shipped HLSL headers, producer pseudocode and focused native assembly are retained.

The modules close the guessed sky geometry/UV/layer/gradient contracts and missing final-filter implementation. Root still owns runtime shader compilation, resource uploads, rendering-order/stencil compatibility, exact texture decoding/driver behavior and image comparison. Dynamic sky asset/time-key transitions outside the selected Noon bridge remain outside this implementation; do not describe those as universally solved.
