# Actual starter sword material: CharacterHardLight

Scope: source material1880463 (01_Rusty_Sword), shader545212 characterhardlight. No core/preview/creator-runtime files were changed, no original database/game execution, no Mac copy. This report separates exact source data, actual recovered DXBC arithmetic and the remaining named-platform-to-bytecode registration join.

## Exact source

source-material.json preserves the raw material and source texture slots. material-parameters.json copies the independently decoded source facts from the geometry agent and checks raw-byte equality.
ConstantColor=(1,1,1,1), hash10276250.
SpecularValues=(1,20,0,0), hash11960536.
CharacterExtraTerms2=(.15000000596046448,1,1,0), hash23195542.
FresnelValues2=(1.399999976158142,2.4000000953674316,0,0), hash10120212.
These values precede each trailing parameter key in the serialized carrier. Reading floats after the key gives the next field and is incorrect.

Source slots0D1880460,1white250070,2S1880462,3N1880461. The geometry agent already staged all authored2D chains, including portable <=512 tails, under sibling initial-sword-visuals; see its texture-stage manifest. No duplicate texture conversion was needed here. Source alpha_test0,cull2,cutoff0: opaque source material with back culling. GL front-face winding depends on the geometry producer and is not inferred from cull2.

545212.shader_bxml references platform545164 CharacterHardLightGeometry,545174 WeightedCharacterHardLightGeometry, low549565/549577. Source shader identity is exact.

## Missing native shader recovered

The previous private extractor work/v19-lighting/shx2.py only scanned compressed prefix D00XBC. Valid aPLib headers also use nonzero low tag bits. The bounded D[tag1..31]XBC check found343 missed entries/81 unique additional blobs. All343 decompressed with exact declared size and valid DXBC. Only exact four-field/no-instance-buffer character candidates were retained here; the existing cache was not changed.

recovered-shaders/78f3c69a187f2822.asm/.dxbc is the full normal-map opaque character geometry program matching this material layout and D/N/S + CharacterAmbientMap resources. 3733cb3c80902fc0 is its low geometry peer. The old cosmetic/emissive/reflection candidates in this folder are rejected diagnostics, not implementation choices. See missed-prefix-recovery.json and reproducible recover_hardlight_prefix_candidates.py.

The named platform ID to embedded bytecode registration table has not been joined. platform_shader_init.bin establishes index29/41 for the full/weighted names, but contains only IDs and a zero array. Cached manager methods, literal/numeric EXE searches and absolute bytecode-pointer checks did not produce the registration link. The new program's layout/resources/operations match the required opaque non-instance character path; this is actual native arithmetic evidence, not proof of an observed opening draw using this hash. Do not relabel the missing association as an active-frame capture.

## Implementable full geometry arithmetic

Materialbuffer cb0: ConstantColor@0,SpecularValues@16,CharacterExtraTerms2@32,FresnelValues2@48.
cb2.cameraPosition@64.
cb4.luminanceShiftId@252.
Shader texture bindings t0D,t1N,t2S,t4CharacterAmbientCube. These differ from source slot numbering.2D maps are trilinear WRAP; ambient is trilinear CLAMP.

Decode x=normal.a*normal.r*2-1,y=normal.g*2-1,z=sqrt(saturate(1-x*x-y*y)).
N=normalize(rawInterpolatedT*x+rawInterpolatedB*y+rawInterpolatedN*z).
PS normalizes only the final mapped normal; it does not separately normalize interpolated T/B/N. VS pre-normalization has not been identified in this bounded pass.
V=normalize(eye-worldPosition).
F=saturate(FresnelValues2.x*pow(1-saturate(dot(N,V)),FresnelValues2.y)).
rawBase=(D.rgb+CharacterExtraTerms2.x*F)*vertexColor.rgb*vertexColor.a.
rawSpec=S.GREEN*SpecularValues.x*vertexColor.a.
G0=(N*.5+.5,SpecularValues.y).
G1=saturate(rawBase,rawSpec).
G2.rgb=saturate(CharacterAmbientCube(N.xzy).rgb*vertexColor.a*rawBase).
G2.a=saturate(dynamicLuminanceShiftId).
The three targets independently store F16. G2 uses rawBase before G1 saturation/quantization. No generic-world rawSpec*.9 ambient term. The extra alpha factor in G2 is intentional: base already contains vertexColor.a once.

The Fresnel operation adds a gray highlight INSIDE material base RGB; it is not a probe reflection or opacity term. ConstantColor, Extra.yzw and Fresnel.zw are unused in this optimized geometry PS. It has no instance skinColor, probe sample, emissive map, alpha texture or discard. White source slot1 is not sampled. There is no per-material light computation/fog here: feed these Gbuffer-equivalent values to the established native shared combine/fog. The matching four-field forward peer3653199d3f8e51b4 explicitly uses SpecularValues.y*.25 as the specular exponent; for this source20 becomes5 in a folded forward implementation.

characterhardlight.glsl is a direct arithmetic helper. It takes CharacterAmbientMap explicitly; using an unrelated main cube is an acknowledged resource approximation until the opening's character-ambient binding is supplied. Source maps/color-space and dynamic luminance ID must follow the existing native resource path, not invented tint values.

## Geometry and bone scope

Per the sibling geometry producer:
Sword FAB1880465: one assembly,424vertices/604triangles,stride48; P@0,UV@12,N@20,T@28,B@36,RGBA@44. Descriptor bone2, no remaps; source skeleton4bones with nonidentity hierarchy.
Container swordpiece:438vertices/610triangles,stride60; P@0,indices4u8@12,weights4u16@16,UV@24,N@32,T@40,B@48,RGBA@56. Every used vertex has weights(32767,0,0,0),indices(0,0,0,0); descriptor bone51/no remaps.
Both source parts use1880463.

The PS needs world-position/TBN/vertex color but no bone data. The rigid sword still requires its correct node2/model transform; container vertices still require the actual node51 transform. A bind hierarchy is not an active animation pose. Do not assume identity, reuse the old preview's hand55 transform, or apply a guessed held-sword orientation. Placement/skinning remains with the geometry producer; this material contract does not change it.

## Integration boundary

integration-contract.json proposes a distinct CharacterHardLight material profile preserving all source values and binding D/N/S. It does not assign an existing generic family or activate a fallback. Restrict initial use to this white-ConstantColor opaque material. Review the explicit program-association, CharacterAmbientMap and vertex/bone producer qualifications before claiming full native fidelity. Texture assets and geometric source evidence are already staged independently.
