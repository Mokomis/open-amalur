# Skin palette -> native shader colour: bounded source/capture contract

Proved: the selected source SkinTone record supplies packed RGB plus separate HEAD and BODY diffuse assets. The original setter preserves the EXISTING skin alpha, converts BGRA bytes to shader RGBA with its exact reciprocal constant, and writes skinColor at byte32 of the144B instance block. No gamma conversion occurs in that converter.

This is a data/native-shader proof only. It does not implement a skin renderer or remove any live pending label. Fresh-creator alpha initialization, full source-hands/captured mesh identity and a complete future source-permutation admission remain explicit boundaries.

## Source record example

playercustomizationdata.bin SHA25649183ebab1eba503fcb1048c9d2c33fefa80a552b99d383db3167823dc0839c1, five little-endianu32 per record.

Almain_Male SkinTone3, original file12688:
[133302,4292265927,4294967295,1290637,1290634].
Packed colour0xffd6c7c7. Head diffuse1290637, body diffuse1290634.
With EXPLICIT existing alpha255, shaderRGBA is:
(.8392157554626465,.7803922295570374,.7803922295570374,1).
This matches captured draw67691 instance skinColor bit-for-bit.

Default Almain_Male SkinTone4, file12708:
[135685,4292128410,4294967295,1290637,1290634].
Packed0xffd4ae9a. With the same explicit alpha255:
(.8313726186752319,.6823529601097107,.6039215922355652,1).
That alpha is a supplied witnessed value, NOT a newly proved fresh-creator default.

Varani_Male defaultSkinTone2 raw record is also retained, with head1430980/body1290634. It demonstrates why an RGB-only replacement or one shared head/body diffuse is insufficient. Only valid selected records are considered; no unknown/out-of-range palette fallback is invented.

source-skin-records.json and three20B .record files preserve exact source offsets/words/bytes. These are the same underlying records preserved by oa_creation_source_tables, not a new colour palette. Source list index and optionKey are distinct: native lookup compares word0; Almain list3 uses optionKey133302.

## First focused route: setter and instance producer

The exact original EXE SHA is16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314.

Lua character_data751829 on_skin_color_change (0/51, PCs16..24, files83677..83709) calls PLAYER.set_skin_color(genderHash,raceHash,optionKey). The compact IR is lua-on-skin-color-change.json.

Direct read-only PE string/xref evidence locates set_skin_color atVA01759b40 and registration in01032dc0. The registration is12B name object followed by4B callback; source name constructor00af4d70 writes offsets0..10 and returns with16B argument cleanup. The callback is written by the NEXT constructor block:0102d700, not adjacent0101c490. That latter getter belongs the preceding get_tattoo_texture_index entry. Original assembly and rejected-adjacent evidence are preserved; do not reuse the wrong pointer.

0102d700 checks3arguments, marshals them and calls0102b250. The cached body of0102b250 queries category0x2ba8f1 (SkinTone) with {genderHash,category} and race.00f2cbb0/00f1f4b0 select the20B record:
- word1 -> packed skin colour;
- word2 -> ignored/null output for this setter;
- words3/4 -> head/body diffuse references (authored assetIDs in source; native imported records may hold resolved resource refs).
The setter then overwrites ONLY colour's high byte from previous Stats+30, preserving alpha. It calls00f50b30,00f50b50,00f50ba0 to store colour@Stats+30,head@34,body@38. Their calls to00f408e0 reach00ddad60/00dda730 and update render visual children recursively.

00dda730 switches on source shader identity:649436(characterhead) uses Stats+34;649640(characterskin) uses Stats+38.00dc2260 appends the corresponding per-instance texture override; the retained DXBC also labels diffuse as S_INST_E_DiffuseMap, while normal/spec maps are material-owned. A palette selection therefore changes actual diffuse binding, not only tint.

00dda730 converts packed Stats+30 through00b37520 into local_bc..b0, exactly32B after the144B block origin local_dc. It copies36words to queued opcode0x44 atcommand+8, so SkinColor is payload+32/command+40. Reflection and active shader binding3[2] independently agree on that offset.

The old010136d0/f76030 seed route was ruled out: it resolves character_skills, not palette application. Its small retained files are negative evidence, not this producer chain.

## Exact colour conversion and alpha

00b37520 outputs:
R=float(double(byte2)*K),
G=float(double(byte1)*K),
B=float(double(byte0)*K),
A=float(double(byte3)*K).

K is double dataVA01732c30, rawLE000000201010703f, exactly
0.0039215688593685626983642578125.
This is FLOAT32(1/255) promoted to double, NOT mathematical double1/255. The final float product can differ by1ULP from byte/255 division.00b09e80 is a no-op; no sRGB/gamma/power conversion is applied. native-color-scale.json retains actual bytes/value; native_skin_record_equation.h is a reference equation taking REQUIRED existing_argb alpha, with no default.

The native setter explicitly retains previous alpha. All9 existing skin draw snapshots have skinColor.a=1, corresponding to byte255. Selected67663 and67691 were independently reconstructed from the original final FillMemory73631 (memory52,33554432B) before QueueSubmit76331 executes commandBuffer46. Full fill SHAa9433c481e510e8777abfaa9105019d735e66551125b7fb083deac6ea9e3befd. There is no stale draw-recording-time uniform assumption.

BHG_PartStats__vf5 at00f76530 loads Stats+30 from its blueprint payload+10. That exact reader is retained. The source Almain/Varani fresh blueprint payload value was NOT decoded, so a fresh creation alpha initializer remains unknown. Existing capture alpha255 is witnessed, not proof of all fresh/player states. Do not take paletteword1 alphaFF or the four cosmetic opacity sliders as an initializer.

## Second focused route: one skin material/profile and actual capture

Source MID513702, shader649640 characterskin:
D source slot0=1290634; mask slot1=518404; S slot2=513642; N slot3=513640.

Its64material bytes, reordered by actual parameter keys to runtime buffer order, equal captured draw67663 CB0 byte-for-byte:
ConstantColor=(.49803924560546875,.5529412031173706,1,1),
SpecularValues=(.6499999761581421,20,0,0),
CharacterExtraTerms2=(.30000001192092896,1,1,0),
FresnelValues2=(1.5,4,0,0).

Source flags alphaTest1,cull2,cutoffByte232. Captured cutoff is.9098039269447327 =FLOAT32(232/255), which is a different conversion issue from the packed tint reciprocal. Do not apply the tint converter's reciprocal rule to cutoff by assumption.

Draw67663 VS461/PS462, actual native images/views:
| Binding | Image/view | Actual view format | Extent/mips |
| --- | --- | --- | --- |
| 32 diffuse |12633/12637|BC1_RGBA_UNORM_BLOCK|2048x2048/9 |
| 33 normal |12756/12760|BC3_UNORM_BLOCK|2048x2048/9 |
| 34 specular |12765/12769|BC1_RGBA_UNORM_BLOCK|2048x2048/9 |
| 35 mask |3347/3351|BC1_RGBA_UNORM_BLOCK|128x128/6 |
| 36 CharacterAmbient |7502/7504|RGBA8_UNORM|8x8x6/1 |

Thus the selected native diffuse view is LINEAR UNORM, NOT sRGB. This is independently observed from the no-gamma palette converter. No automatic sRGB decode should be inferred for either. Identity component swizzles and exact image/view create structs are preserved in draw-67663-bindings.json.

This proves the exact source parameter-profile/alpha-property match and native resource layout/format. It does NOT prove complete MID-to-bound-image identity: full source texture pixels were NOT joined here, and the current source hands/torso VBs are absent from the730-buffer main-Gbuffer inventory. Do not relabel it a fully captured FAB514034 instance. material-513702-contract.json and skin-mesh-join-boundary.json state that distinction. Only two source N/S carriers were extracted privately before the stop request; no broad extraction or additional capture was attempted.

Captured draw67691 skinRGBA exactly equals Almain_Male record3 under the proven conversion. That is an exact value match, not unique proof of actor race or requested optionKey; NPCs/other gender/race records can share a packed colour. The static setter independently establishes how this selected source record maps to uniforms.

## Actual masked shader equation / requirements

Existing MATERIAL_SUPPORT.md/opaque DXBCa6137bc3ab30c78c is a useful colour core, but it is NOT sufficient to render source513702 because this material is alpha-tested.

Active PS462 lines149..183 sample t3 at UV0.xy and discard iff mask.GREEN-cutoff<0. Equality survives. It does NOT use diffuse alpha or vertex alpha for this test.

Its skin core uses instance.skinColor@32:
delta=skinColor.rgb*D-D;
cosmetic=skinColor.a*delta+D+Extra.x*saturate(Fresnel.x*pow(1-saturate(dot(N,V)),Fresnel.y));
rawBase=cosmetic*VC.rgb*VC.a.

The normal map is packed(R*A,G), reconstructed positiveZ, combined with RAW interpolated T/B/N then normalized. Body only needs UV0 for D/N/S/mask in this permutation. Specular uses S.GREEN*sourceStrength*VC.a; rawGloss20 is passed unchanged, exponent5 in shared lighting. G1 and G2 are independently saturated and HALF-stored; G2=CharacterAmbientMap(N.xzy)*VC.a*rawBase. ConstantColor and generic world ambient q are not colour multipliers here.

Active VS461 SPIR-V text is BYTE-IDENTICAL to previously proved VS375, SHA526bae7c5776fc55f414b72987ee34c46addc60b869e7aa8c76372541af6d440. Therefore this captured weighted skin permutation has the SAME P/N/T skinning, unskinned entity-transformed B and independent vertex normalizations. See weighted-hardlight-basis-audit; no new basis guess is needed for this observed pair. Exact future source-platform649431-to-active-permutation routing remains a separate admission question.

Head uses its own diffuse override plus tattoo/makeup colour/UV/mask operations. Existing retained headDXBCd4be... requires a separate overlay UV pair; source headUV1 differs from UV0. This pass does not validate all head bindings, and body-only tint must not be advertised as a full head/hair/cosmetic creator.

body-skin-equations.glsl and native_skin_record_equation.h are REFERENCE artifacts only; no live renderer, shader family, palette fallback, save or UI implementation was made.

## Completion boundary and preservation

The two focused routes closed record-field semantics, exact packed-colour conversion, preserved alpha behaviour, head/body diffuse selection, instanceCB slot and an active masked-body profile/format/equation witness. Remaining:
- actual fresh creator StatsBlueprint alpha payload+10;
- exact source mesh and bound texture-pixel identity;
- final source-platform/permutation admission and a real renderer test;
- full head/hair/other cosmetic operations and dynamic texture/UV requirements.

No new game/capture execution, GPU experiment, live/core/asset-root/UI/user-state/database writes, new native analysis session or Mac mirror. All new evidence only under work/v49-character-create/skin-colour-contract-audit. Work stops here as requested; the original pending UI state was not changed.
