# Captured weighted HardLight VS375 basis contract

The captured VS375 skins POSITION, NORMAL and TANGENT. It does NOT skin BINORMAL. All three final direction outputs are independently normalized in the vertex stage, then smoothly interpolated. PS376 normalizes only the final packed-normal-map combination. Do not skin every direction or reconstruct B with cross(N,T) for this permutation.

This is a bounded shader/source-data proof, not a capture of the four current Almain clothing parts. No core/preview/config/database changes or GPU/game actions.

## Exact native program identity and declarations

VS375 SHA256526bae7c5776fc55f414b72987ee34c46addc60b869e7aa8c76372541af6d440.
PS376 SHA256778dce0a8f010eed316e3d4763cf513d4fb5ac826bdd28370ea6bf2cb09e78be.
PS376 SPIR-V text is BYTE-IDENTICAL to PS352, the exact source-material-matched RustySword HardLight shader from character-gloss-audit.

Existing captured pipelines13260(weighted56) and13262(weighted60) BOTH use VS375/PS376. Complete original pipeline structs are native-weighted-declarations.json.

| Input location | Stream | Format | 56B/type17 byte | 60B/type22 byte |
| --- | --- | --- | --- | --- |
| 0 P | 0 | float3 | 0 | 0 |
| 1 jointIndex | 0 | SINT8x4 | 12 | 12 |
| 2 boneWeight | 0 | SNORM16x4 | 16 | 16 |
| 3 UV0 | 0 | float2 | 24 | 24 |
| 4 N | 0 | SNORM16x4 | 32 | 32 |
| 5 T | 0 | SNORM16x4 | 40 | 40 |
| 6 B | 0 | SNORM16x4 | 48 | 48 |
| 7 COLOR | 1 for56,0 for60 | UNORM8x4 | stream1@0 | 56 |

Actual secondary56 binding stride12/defaultwhite is separately sealed in character-stream1-audit. Secondary60 stride8 has no active COLOR input. Do not derive active semantics solely from the same primary byte stride: that audit excludes nonweighted lookalikes.

VS binding68 is12float4 entity rows. Binding69 is234float4 palette rows =78three-row affine entries. Do not infer80valid entries from a3840B aligned descriptor range. No shader-side palette remapping/clamping exists.

## Exact equations and arithmetic convention

Let i=(i0,i1,i2,i3) be native signed-byte joint indices (valid range required by caller), and source decoded normalized weights=(w0,w1,w2,unusedStoredFourth).

The shader calculates w3=dot((-1,-1,-1,1),(w0,w1,w2,1)).
It ignores the raw stored fourth input; it does NOT clamp negative residuals, renormalize the weights or divide by their sum.

For joint j, use palette rows b69[3*j+0..2]:
point_j(P)=(dot(row0,(P,1)),dot(row1,(P,1)),dot(row2,(P,1))).
direction_j(D)=(dot(row0.xyz,D),dot(row1.xyz,D),dot(row2.xyz,D)).
Bone translation contributes to P only.

For either operation, accumulate in native order1,0,2,3:
r=op_i1(X)*w1;
r=op_i0(X)*w0+r;
r=op_i2(X)*w2+r;
r=op_i3(X)*w3+r.

Let SkinPoint/SkinDir denote these sums. Entity directions use
R(D)=D.y*c68[5].xyz + D.x*c68[4].xyz + D.z*c68[6].xyz
(native addition order y, then x, then z; no translation).

Final vertex varyings:
Nout=normalize(R(SkinDir(Nsource))).
Tout=normalize(R(SkinDir(Tsource))).
Bout=normalize(R(Bsource)).

Pskin=SkinPoint(Psource).
W=Pskin.y*c68[1].xyz+Pskin.x*c68[0].xyz+Pskin.z*c68[2].xyz+c68[3].xyz.
clip=Pskin.y*c68[9]+Pskin.x*c68[8]+Pskin.z*c68[10]+c68[11].
Thus bone palette and entity rows are separate stages in the native ABI.

No per-joint direction normalization, inverse-transpose construction, Gram-Schmidt, B=cross(N,T), handedness correction or tangent.w sign is in this shader. Only xyz of N/T/B is used. R is the exact supplied row operation; this audit does NOT prove how the native CPU producer constructs those rows for arbitrary entity scales.

After interpolation, PS376 decodes map x=R*A*2-1,y=G*2-1,z=sqrt(saturate(1-x*x-y*y)) and uses normalize(Tout*map.x+Bout*map.y+Nout*map.z). It does not renormalize each interpolated basis vector separately.

## Instruction anchors

The retained full module-375.spvasm is authoritative; native-basis-excerpts.txt contains numbered spans:
-107..120 residualw3;129..138 signed indices*3.
-135..315 skinned P uses palette69/point dot4;316..344 composed clip.
-401..629 sourceN/palette69 dot3 and weights;630..687 entityR then inverse-length normalization/outputlocation5.
-688..916 sourceT/palette69 dot3 and weights;917..974 entityR then normalization/outputlocation6.
-975..1032 sourceB reads ONLY entity68[4..6], normalizes and writes outputlocation7. The entire block has no palette69/index/weight load.
-345..346 COLOR passes unchanged;347..351 UV0 passes unchanged.

Native B asymmetry is explicit even if it creates a basis that is no longer orthogonal after a joint rotates. Do not replace it with a more conventional frame by assumption. This result is for VS375 only, not every weighted native vertex shader.

## Source pack and current host convention

The existing checked source-join-manifest/exporter under vertex-contract-audit identifies source56/type17 and60/type22 N/T/B at32/40/48. It copies the entire24B SNORM N/T/B span byte-exact into the OACAT attribute record at0/8/16 (including their unused fourth shorts). No axis reordering, cross-derived binormal, handedness rewrite or per-vertex skin transform is in that source copy.

The old52B OACHAR geometry alone does not contain sourceT/B. Use the retained source attributes, not derivative TBN or the former normal-offset heuristic. Current feet/legs/pack/shirt source descriptor joins and per-assembly palette fixes remain their existing evidence; this task does not claim those models occur in the captured frame.

Current oa_character_bones already composes facing and feet into EVERY palette entry: lines119..123 rotate q/t by c->facing and add c->feet to affine translation. current-bone-producer-excerpt.txt retains the exact source SHA/lines. Therefore its output palette is WORLD-space, unlike the split native69/68 ABI above.

If using those existing WORLD rows:
- Pworld=SkinPoint_world(Psource).
- Nworld=normalize(SkinDir_world(Nsource)).
- Tworld=normalize(SkinDir_world(Tsource)).
- Bworld must still use the ENTITY-ONLY normal/direction transform of Bsource; for the currently shown rotation/translation-only producer, that is facing rotation, without joint skinning or feet translation.
- Do not apply facing/world rotation AGAIN to N/T or P. Additional entity scaling/normal transforms must be supplied explicitly by the caller; no generic scale inference is made here.

oa_character_material rigid factory SHA2543984096f47b85b03a7bca46b57d74fc9a8aef7ffe60f195d598f2d541b764 expects ALREADY-world P/N/T/B and only independently normalizes the three inputs. It performs no bone or entity transform and cannot infer the B exception. A weighted caller should provide its own verified vertex stage through oa_world_program_with_vertex; the material fragment can remain shared.

weighted_hardlight_basis.glsl is an illustrative exact native split-ABI helper, NOT a full renderer replacement or tested skinned scene. It deliberately preserves unskinned B and negative fourth weight. No host weight-policy/palette/pose fix is applied by this audit.

## Independent equation check and limits

analyze_vs375.py directly executes the straight-line SPIR-V instruction stream using float32 arithmetic and compares it against separately written vector equations for12deterministic inputs. It varies all palette/entity matrices and includes a negative residualw3. Maximum component error5.960464477539063e-8. Mutating bones/weights changes N/T but leaves B BIT-IDENTICAL in every case. COLOR remains direct input copy. equation-validation.json retains per-output errors and all case receipts.

This is CPU validation of shader arithmetic, not new native execution, GPU timing or an opening-frame comparison. No bone-palette producer identity, original source-clothing draw, animation timing, final render or full-character parity is claimed. Existing source/palette/pose qualifications remain.

All new files are confined to work/v49-character-create/weighted-hardlight-basis-audit. Source-reference SHAs are source-reference-hashes.json plus the current bone-producer excerpt. Investigation stops after this sealed proof; no core/preview/config/database/user-data changes.
