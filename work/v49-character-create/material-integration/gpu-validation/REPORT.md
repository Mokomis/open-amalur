# Native HardLight12: isolated source review and EGL/GLES fixture

PASS, scoped to the opaque HardLight12 material helper and rigid vertex basis. No concrete source-formula mismatch was found. The ACTUAL live oa_post.c factory and oa_character_material.c upload function compiled, linked and ran; no copied fragment implementation stood in for the tested helper.

26 primary cases:24 material cases and2 independent vertex-basis diagnostics, each32x32 RGBA8. All material cases match the independent PS352 source oracle exactly when using this backend's separately observed HALF-target conversion. Against an ideal nearest-even HALF CPU model, maximum deviation is1RGBA8 code. No shared quantizer change is justified.

No core/UI/live preview files were edited. Source before/after hashes match. No game/native window/device actions occurred; only a standalone EGL pbuffer.

## Reviewed implementation

The captured PS352 contract is sealed under work/v49-character-create/character-gloss-audit. Current HardLight12 correctly:

- Uses packed map x=R*A*2-1,y=G*2-1,z=sqrt(saturate(1-x*x-y*y)), combines RAW interpolated T/B/N, then normalizes.
- Computes rim=saturate(Fresnel.x*pow(1-saturate(dot(N,V)),Fresnel.y)).
- Places Extra.x*rim INSIDE base: rawBase=(D+Extra.x*rim)*VC.rgb*VC.a.
- Uses rawSpec=S.GREEN*SpecularValues.x; specGain=saturate(rawSpec*VC.a); rawGloss=SpecularValues.y and exponent=rawGloss*.25 once.
- Overrides generic ambient with G2=HALF(saturate(CharacterCube(N.xzy)*VC.a*rawBase)). Generic q and sky-specular computations are overwritten before native final consumption.
- Ignores ConstantColor in the source HardLight color formula. The earlier generic preprocessing is overwritten by branch12, so uploading the unused source field does not leak tint.
- Independently normalizes N/T/B in the rigid VERTEX stage, before interpolation; fragment normalizes only the combined mapped normal.

Factory OA_CHARACTER_MATERIALS includes branch12 only for the explicit caller-vertex API. Legacy world preprocessing lacks that case. This was reviewed statically; no outdoor scene validation is claimed.

Root's prior struct-spanning finite-validation loop was fixed BEFORE compilation. The tested helper SHA is2543984096f47b85b03a7bca46b57d74fc9a8aef7ffe60f195d598f2d541b764. The four declared arrays are traversed independently. Runtime fixture also rejected ConstantColor NaN, negative gloss and negative Fresnel exponent; valid upload and uniform mapping passed.

## Actual renderer and build

EGL1.5, Google Inc. (NVIDIA).
ANGLE (NVIDIA, NVIDIA GeForce RTX 4080 SUPER (0x00002702) Direct3D11 vs_5_0 ps_5_0, D3D11-32.0.16.1692).
OpenGL ES3.0 / GLSL ES3.00, ANGLE2.1.27600 gitf39c3524d091.

build_and_run.cmd uses installed MSVC18 BuildTools and existing v40-windows-host EGL/GLES DLLs. The limited project import tables omit introspection functions needed by the fixture, so PRIVATE import .defs/.libs are generated here only. Existing libraries remain untouched. Actual post/cache/nativepost dependency .c files are compiled; unused post functions are not executed. Initial unresolved-link log is retained as build-initial-link.log; the final build.log has no warnings/errors, fixture-errors.txt is empty.

hardlight_fixture.c calls oa_character_rigid_material_program(1), which reaches oa_world_program_with_vertex, then oa_character_hardlight_upload. glGetShaderSource saved actual-linked-vertex.glsl and actual-linked-fragment.glsl from the linked program. Hashes:
- Vertex bd88b39348dd2a7eaffc38bea7ef49757c65df5d9163ac76bcad89c694bf6ed3.
- Fragment9901074f80434326bf6b960106d227e6a989012e61b6dd684a18e0c6a6a6837b.

## Material inputs and checks

One full-screen triangle, identity MVP, eye(4,0,-1). Sun/shadow/fog/direct lights disabled; AO=1. Nonzero generic globals deliberately alternate against zero: ambient_scales(5,.9), sky_light(.7,.9,.3,3.2). Feature bits128|16|4 enable the reviewed native material path; point-light bit8 stays off.

Textures are constant RGBA8 with nearest sampling: diffuse(80,120,160,255), packed normal(204,102,128,255), specular GREEN201; CharacterCube(101,173,219,255), same value all6faces. Vertex RGB=(204,153,230)/255; alpha0,.6,1. Source-profile input uses strength2.3,rawGloss20,Extra.x.15,Fresnel.x1.4,Fresnel.y2.4. Strength2.3 is a deliberately sensitive fixture input, not a source-material retune.

24 cases =3alpha *2rim(on/off) *2ConstantColor(1,1,1,1 vs.13,.95,.27,.37) *2genericambient(zero/nonzero). All4096 bytes of every corresponding ConstantColor/ambient pair are identical. Thus no unused ConstantColor tint or generic-q/sky leak was observed. Alpha0 is all black.

Center RGBA pixels (all material center samples also equal both independent CPU models):
| Alpha | Rim OFF | Rim ON |
| --- | --- | --- |
| 0 | 0,0,0,255 | 0,0,0,255 |
| .6 | 9,18,45,255 | 11,20,49,255 |
| 1 | 25,49,124,255 | 30,55,136,255 |

Two diagnostics use unequal-length, varying per-vertex N/T/B, then the same vectors normalized before upload. Actual mapped-normal images are byte-identical between both inputs. A CPU counterfactual omitting vertex normalization differs by up to19normal codes. Actual mapped N read into RGBA32F agrees with independent CPU N within2.3841858e-7 per component. This tests independent basis normalization before interpolation, not skinning/world-transform producer correctness.

## Oracle and conversion qualification

validate_source_oracle.py independently implements retained native PS352 source math, not parsing or reusing current GLSL. It clamps raw CharacterCube*VC.a*rawBase, converts to HALF, then nominal roundEvenRGBA8. Original ideal nearest-even HALF comparison:106496channels,618 differ by exactly1code, no larger deviations. This includes both direct-UNORM8 normal diagnostics. All Fresnel-OFF material cases are exact.

A small conversion probe isolates the rounding assumption. For all3 discriminating values, current packHalf2x16 and DIRECT RGBA16F target writes agree:
- input.100019999 ->.0999755859375 (nearest-even HALF would be.10003662109375).
- input.333299994 ->.333251953125.
- input.421589255 ->.42138671875.
Direct RGBA8 store of.421589255 yields107, while nominal nearest-even multiplication gives108. Therefore direct normal-display UNORM8 conversion can differ by1code even with float N agreement.

validate_observed_target_oracle.py preserves the independent source arithmetic and uses positive float32-to-HALF toward-zero conversion, separately supported by those actual target probes. Result:ALL98304channels in24material images match EXACTLY,0mismatches. The original ideal-RNE images/report remain preserved, not replaced. Do not generalize this observed backend rounding to every GPU or claim an original-opening frame conversion observation.

oracle-validation.json contains every actual/oracle pixel hash and per-case error; observed-target-oracle-validation.json seals the second model and all24 exact matches. Raw case-00..25.rgba, ideal -oracle.rgba and material -observed-target-oracle.rgba are retained. conversion-probe.jsonl and float-normal-diagnostic.json preserve the additional bounded measurements.

## Scope limits and reproduction

No whole-character, skinned palette/pose, dynamic cosmetics, native room-light selection, sun/shadow/point-light/specular integration, fog, full scene, Android GPU or FPS claim. Specular uniform mapping was verified, but all illuminating sources were off as requested, so reflected-lobe rendering is not tested here. Cube sampling used constant faces; spatial character-cube selection/orientation remains covered by earlier source/capture evidence, not this fixture.

Reproduce in this folder: build_and_run.cmd; then existing Python312 validate_source_oracle.py and validate_observed_target_oracle.py. This rebuilds only the standalone fixture; it does not install/deploy/run the game. No further driver experiments or shared quantizer edits are needed from this bounded result.

Source hashes below were identical before and after all fixture runs:

- work\v19-host\oa_post.c: c3bc0e0bc330d9599ae38ac60aa462fb4b4a52efa9ab0048965c6bdf4d44b5d5
- work\v19-host\oa_post.h: c135a546b5af4e5fd7e52ef23a78847cf209e7ade215865aba32b6fe4a68a26b
- work\v19-host\oa_character_material.c: 2543984096f47b85b03a7bca46b57d74fc9a8aef7ffe60f195d598f2d541b764
- work\v19-host\oa_character_material.h: 5c3048bbc4c9da2df53a7bd0bba6865ba250aa16e07863d74e3de1d5ebe525bd
- work\v19-host\oa_render_cache.c: 9b71d7caa11ebbba3745b3853aebb0c3f7093809635ebb5ea45d5238ed9342ea
- work\v19-host\oa_render_cache.h: 578a86b99d61fcea4ce76432e92df3385dc615bdd2453588ffb42adebe2ceee2
