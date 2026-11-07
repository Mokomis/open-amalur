# Native cart material426015: ready family9 staging

Native draw68274 uses VS650/PS651, source material426015 `for_cart`, shader358221 `fresnelglassmetalprobe`. The active shipped DXBC is `8af7b90f9cc700d2`. The cart is opaque; its brown reflection tint belongs to this distinct material contract. Shared legacy row10 cannot represent it faithfully. Append alias row299 and change only the newly recovered cart auxiliary run to299; preserve existing rows0..298.

## Ready files and integration

- `native_cart_contract.glsl`: exact compact vertex-frame, material and ambient functions, plus G0/G1/G2 output contract.
- `material-row299.bin`: one28-byte MATS row, opaque native-back-cull flag0x10000000, texture IDs697/698/699/700.
- `native-material-row299.bin`: one84-byte family9 profile. COLOR=TintColor; SPEC=(SpecStrength,Gloss,FresnelPower,FresnelScale); UV=(1,1,ReflectionInfluence,unused Opacity).
- `world/t697.bin`..`t700.bin`: diffuse, normal, specular and independent alpha/reflection mask. Each is native256x256, seven authored levels through4x4, portable OATX RGBA8. No generated/resized levels. All28 native BC payloads match original authored source DDS levels exactly; per-level BC/RGBA hashes and source-file hashes are in `material-contract-and-merge-plan.json`.
- `cart-environment.bin`: `OARE001\0` plus three little-endian float32 values(1,1,1), from captured CB1.environmentTint.rgb@96; buffer51/memory52 absolute offset360992. `cb-layout.json` and complete captured CB binaries preserve offsets and exact values.
- `oa_cart_probe.c/.h`: independent loader `oa_cart_probe_open(assetManager,"world/water-native.bin",3594)`; returned GL cube belongs to the common world renderer. Bind to the requested common unit14 and delete/recreate with that context. This reads existing OAWP2 cube3594 from the current water pack; no water source/API/resource ownership change is needed.

Family9 must normalize transformed source N/T/B separately **per vertex**, matching native VS650. Pass those three raw interpolated vectors into `oaCartMaterial`; do not normalize them again in the fragment stage before applying the mapped components. Existing source OAWE data supplies the original independent N/T/B. No derivative frame is used. All four 2D maps use unchanged UV0 and UNORM sampling. Native vertex RGBA uses source byte order.

The alpha map's GREEN channel times vertex alpha is a reflection mask, not coverage. The normal XY decoder is `(normal.r*normal.a,normal.g)*2-1`, then reconstruct positive Z and normalize the final mixed world normal. `rho=fresnel*alpha.g*vertex.a*ReflectionInfluence`. Diffuse is multiplied by vertex RGB and `(1-rho)`; TintColor affects only the reflection cube. Specular uses GREEN times SpecStrength once. Opacity and SpecularColor RGB are unused by this active opaque PS.

The family9 ambient result is `clamp(ambientCube(N.xzy)*rawBase + rho*reflectionCube(reflect(-V,N).xzy)*TintRGB*environmentTintRGB,0,1)`. Evaluate with rawBase before its G1 clamp and bypass generic ambient-q/sky attenuation. Keep the shared deferred direct/specular contract. Do not apply SpecStrength again downstream. G0=(N*.5+.5,Gloss), G1=clamp(rawBase,rawSpec), G2=(ambient,clamp(dynamicLuminanceShiftId)). Native targets are RGBA16F. Captured dynamicLuminanceShiftId=.4375 is perdraw CB4+252, not a material parameter. Live eye supplies V.

Sampler149 on all four2D maps: linear min/mag, linear mip, REPEAT, bias0, minLOD0/maxLOD1000, anisotropy disabled(native0 ->GL1), max authored level6. Cube sampler336: same filtering, CLAMP, anisotropy disabled, cube maxlevel5. Extend any native-only anis1 loader whitelist through697..700. Image3594 is128x128, six faces and six authored levels ending4x4; face order +X,-X,+Y,-Y,+Z,-Z with unchanged row order. Exact pack offsets/hashes are recorded in the merge plan. Ambient cube7496 is the existing common native ambient resource.

## Evidence and validation

Source RDEF names, captured CB bytes, source material keys, descriptor image/sampler identity and shader instructions all independently support the mapping. `cb-layout.json` enumerates the exact CB0/1/2/4 offsets. `captured-samplers.json` records active bound sampler IDs/states. Native PS651 and VS650 disassembly, shipped DXBC, complete CB ranges and extraction script are included.

`ps651-algebra-validation.json`: independent execution of the actual PS651 SPIR-V SSA versus the compact functions on512 deterministic randomized cases, including nonunit interpolated frames and coordinate-dependent cube functions; maximum error3.3306690738754696e-16(float64 algebra). `shader-compile-check.json`: GLES3 vertex and fragment wrappers compile with glslangValidator. This proves algebra/syntax, not GPU float rounding/filter parity.

`probe-parser-validation.json`: the new standalone C loader compiled under current Windows host headers/MSVC19.51. A mock GL test loaded existing live OAWP2 and validated36 face/mip calls,524160 RGBA bytes, maxlevel5, FNV1a64 `1df1c570a115663e` against an independent Python parse. No GPU/render/replay was used. No original game launch or core/live source edits occurred. Parent owns actual renderer integration and Windows/Android image validation.

## Scope and remaining limits

This stage preserves the source/captured cart geometry and placement work already delivered separately. Rebind only its auxiliary run to299. Existing shared row10 remains unchanged. Source records and GPU descriptors prove the recovered contract; final visual parity still depends on parent integration, half storage rounding and common deferred pipeline. The static captured reflection probe is the same existing water resource, not a newly synthesized environment. Water module source and headers were not edited by this task.
