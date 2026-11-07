# Native active far depth-of-field module

2026-11-05. New standalone module only; shared source/assets untouched. Original capture SHA72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209. No GPU/game/UI execution, installation or database mutation.

## API and ordering

Include oa_native_dof.c/.h, using existing oa_post_program. Open(p,fullW,fullH), then render(p,ungradedSceneRGBA8,hardwareDepth,currentGLVP,NULL) returns full-size RGBA8 effect texture. Close releases only owned resources. Depth and scene are borrowed. Rendering leaves post framebuffer/state changed; root owns restore/order.

The final merge is:

`C=clamp(mix(scene.rgb,effect.rgb,effect.a)+bloom.rgb*.4306860566,0,1)`.

Apply LUT AFTER this, then write final luma alpha(.299,.587,.114), then native final filter. Do not substitute effect RGB as the entire scene or apply the effect after grading. Native bloom extraction reads the unblurred scene; this module does not change that chain.

The module owns half-size RGBA8 fuzziness and full-size RGBA8 effect targets plus a LINEAR/CLAMP sampler. Original extents768x432 and1536x864 are represented by runtime width/height. It disables depth, stencil, culling, blending, scissor and dithering for its full-screen passes. The physical far DOF default starts9974.311523world units (~99.7m), grows over20001world units and caps at.7 alpha at23975units. Foreground is unchanged except ordinary final grading/filtering. No near DOF, scene-specific pixel mask, saved camera selector or visual tuning is added.

## Exact active pass reduction

Original phases112..117 create near/far fuzziness then resolve. Near builderPS1839's active near parameters c0.xy are0,0: it writes nearCoC0 everywhere. Its downsample and H/V blur remain0. Therefore those four zero-producing passes can be removed for this selected path without changing farDOF. No dormant nearDOF behavior is claimed.

Far builderPS1841 samples the full depth with NEAREST/CLAMP into halfRGBA8. Depth0 is first replaced by1, matching native. It reconstructs Z using inverseDepth=(1/B,-A/B), `Z=1/(inverseDepth.x*d+inverseDepth.y)`, where d is stored hardware depth0..1. There is no2*d−1 conversion. It computes:

```
nz=Z/524288;
farCoC=min(max((nz-.01902448944747448)*26.213088989257812,0),.699999988079071);
fuzz=(farCoC,nz,farCoC,farCoC);
```

The native threshold bit gate is retained; below threshold farCoC is0 anyway. These values are written to RGBA8 BEFORE blur sampling; do not upgrade fuzziness to float16 because its quantizedG depth influences foreground-edge weighting.

The default physical fields pack to the captured normalized constants BIT-EXACT in float32: start9974.3115234375,range20001,maxAlpha.6999999881,depthStorageScale1/524288. The fixed depth storage scale is a native shader/storage contract, NOT the current camera clipFar. Changing normal play clipFar must not move DOF start from100m.

To preserve native half-size NEAREST selection under GL bottom-left storage, the module explicitly converts half-screen native top-left pixel centres into full-depth integer texels, then reversesY for texelFetch. This avoids sampling the other side of the full-size texel boundary when downsampling2:1 after aY flip.

PS1849 (shipped equivalent1254fa3a99311a33) then samples half fuzziness linearly. It starts accumulatedRGB=scene centre, weight=1. For16 native offsets, q=uv+centerCoC*(6/fullExtent)*offset. Each neighbour's weight is neighbourCoC, reduced by.5 if that neighbour is in front of the centre depth and the centre is in the far region. The weighted samples are accumulated in native order, then divided by total weight. Output alpha is centreCoC. All16 precise float constants are retained in the C shader. Both input samplers are nativeLINEAR/CLAMP and output is againRGBA8 before final merge.

## Dynamic camera support and precision

render() derives current depth parameters from column-major GLVP. For r2/r3 spatial rows, s²=dot(r3,r3), a=dot(r2,r3)/s², b=(m14−a*m15)/(2*s), A=(a+1)/2, B=b. inverseDepth=(1/B,−A/B). This works with normal camera motion and current projection, rather than forcing captured near/far values.

Pass the pure GL projection matrix instead of fullVP when available; this avoids subtracting large translated camera terms when recoveringB. Full capturedGLVP recovery differs from the captured inverseDepth by~8e−8 per component because the matrix is alreadyfloat32. That is a precision limit, not a reason to pin the camera. render_constants accepts the exact CURRENT camera inverseDepth pair when supplied by the caller. The reference pair is(-.03818615898489952,.03818806633353233), retained as evidence/explicit reference option rather than silently hardcoded in normal rendering.

## Validation

Windows MSVC /std:c11 /W4 compile is clean with root's desktop_compat forced include. All three GLSL300ES stages compile. Independent CPU interpretation of ACTIVE SPIR-V1849 versus the concise16tap kernel passes160 randomRGBA8scene/fuzziness cases with exactfloat32RGBA agreement. Independent evaluation of ACTIVE1841 versus the far-fuzz formula passes124depth cases with exactRGBA agreement. Default world-to-native parameter packing is bit-exact. The interpreter asserts finite results; booleans/bitcasts are evaluated as uint32 rather than float numeric casts.

These tests validate shader arithmetic, kernel coordinates and default parameter packing. They do not execute GPU sampling, FBO storage rounding, driver compiler optimization or final image comparison. Root owns those runtime checks. Raw active shader modules/disassembly and phase constants/contracts are retained.
