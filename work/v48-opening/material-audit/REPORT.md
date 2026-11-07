# Dominant opening wall: GlassMetalProbe

MID469438 nca_wall01 is shader358224 glassmetalprobe. Its source shader carrier points to GlassMetalProbeGeometry380423 and WeightedGlassMetalProbeGeometry380425, with named low variants549749/549743. This is distinct from fresnelglassmetalprobe/family9. No live source or preview assets were modified.

Exact source parameters:
SpecularValues=(2.5,70,0,0);
ReflectionInfluence=.20000000298023224;
TintColor=(1,1,1,1);
Opacity=1.
SpecularColor is not explicitly overridden here.
Material flags in the existing source catalogue are alpha_test0/cull2, opaque.
Textures: source0diffuse469469;1reflection-mask498117;2specular469471;3normal469470;21probe1259503.

Original retained DXBC6ac6c90a39ca9861 is the full normal-map geometry variant with exactly the non-Fresnel material layout/resources. 637bd0508a9cd5d9 is a corresponding low geometry variant: G0/ambient use normalized geometric normal, while reflection still uses the mapped normal. 8af7b90f9cc700d2 contains additional FresnelPower/FresnelScale and is the separate existing family9 contract. All are retained in shaders/. Source platformID-to-DXBC hash table is not joined; a cached native-name/numeric seed search found no anchor and was stopped (cached-platform-join-seeds.json). This limitation does not erase the actual arithmetic/resource evidence.

Full geometry arithmetic:
N=normalize(T*(map.a*map.r*2-1)+B*(map.g*2-1)+rawN*sqrt(saturate(1-x*x-y*y)));
rho=mask.GREEN*vertexColor.a*ReflectionInfluence;
rawBase=D.rgb*vertexColor.rgb*(1-rho);
rawSpec=S.GREEN*SpecularValues.x;
reflection=rho*probe(reflect(-unitToEye,N).xzy).rgb*TintColor.rgb*environmentTint.rgb.
G0=(N*.5+.5,runtimeSpecularValues.y);
G1=saturate(rawBase,rawSpec);
G2.rgb=saturate(ambientCube(N.xzy).rgb*rawBase+reflection).
G2.a=saturate(dynamicLuminanceShiftId).
Native target storage then quantizes each target to F16 independently. Reflection belongs inside G2 clamp/F16 and ambient AO, not an unlit addition after final lighting. No Fresnel, extra VCa on rawSpec/base, or generic-world rawSpec*.9 ambient term. Opacity/TintColor.a/SpecularColor are declared but not consumed by this geometry PS. CPU source-to-runtime gloss conversion is separate; retain existing proven host upload policy.

Use glassmetalprobe.glsl as the source arithmetic helper. Parent can assign distinct family11. Normalize/interpolate TBN exactly as the chosen native vertex producer requires; this bounded pass establishes PS consumption and does not prove a new VS rule.

All glassmetalprobe materials in the existing first-room catalogue (not all installed-game materials) are preserved in opening-glassmetalprobe-materials.json:
464114 min_metaltrim01: probe505647, influence.4, spec1.76/100, Tint(.89803928,.66666669,.56470591,1).
469438 nca_wall01: probe1259503, influence.2, spec2.5/70, whiteTint.
476693 nca_stalagmite01: source slot21 explicitly0, influence.1, spec1/100, whiteTint. This lacks a usable authored probe. Native runtime fallback/nearest-probe selection has not been established. Do not inherit the previous draw's bound cube or invent a nearest-probe rule. Label any explicit fallback.

Authored cube pack:
glassmetalprobe-probes.bin, OAWPversion2,2textures,0materials.
Asset1259503 and505647 are both128x128x6 BC1 source cubes with6 authored levels128,64,32,16,8,4. All levels are retained; no generated mip/tail trimming. Decode standard BC1 to RGBA8 without R/B swap, face rotation, row/vertical flip, resizing or other color transformation. Source faces0..5 are retained in source order; existing OAWP loader maps them +X,-X,+Y,-Y,+Z,-Z. This preserves the current authored-cube convention; no opening capture of these exact probes was available to independently compare orientation. Software/GPU BC rounding parity is not claimed.

Pack SHA2566a74981dcb0d99b8c5c1de6b0a8f8b56a37ecd21e9be022f6edd2f57639f5486,1048528bytes. Open with oa_cart_probe_open(assets,path,1259503) or505647. Each returned texture is independently owned. Metadata/source hashes/per-face-per-mip hashes are in glassmetalprobe-probes.json; reproducible producer stage_glassmetalprobe_cubes.py. cube-loader-validation.json tests the ACTUAL current oa_cart_probe.c through mocked uploads, not a GPU run.

Source2D shader samplers are trilinear WRAP; ambient/probe cube samplers are trilinear CLAMP. Source21 is the material-resource slot, not the PS texture binding index (PSprobe=t5). GBuffer texture and format contracts remain those already recovered for the shared deferred combine. No additional shader families were expanded; MID570823 raw source was retained only, without claiming textureblend support.
