# Authored lamp actor source, LOD pack and exact emissive material

## Result

The missing right-hand bridge lamp is **source-authored actor0x98[17]** in PATCH431646.space_bxml (`out_dal_west_01`), FAB540961 `vil_lamp_ns_stand`. Its source position/rotation/scale match the captured draw exactly. There is no captured-placement override or unresolved local-bind correction for this lamp.

Private staging is ready under `stage/`: six `lamp-world/rCX_CY.bin` geometry files, `lamp-index.bin`, four OATX files693..696, material298 row-only candidates and a bridge-only authored fixture. Nothing was deployed.

**Merge the lamp ranges with the other auxiliary packs. Do not overwrite an existing region r-file with a lamp-only r-file.** The index and material row candidates are deliberately separate from other agents' reserved296/297 entries.

## Generic authored actor producer

A space file's pointer/count pair at bodyheader0x98 selects80-byte actor records. Pointer values are absolute file offsets (body indexing subtracts8). Proven fields:

| Record offset | Observed field |
|---|---|
| 0 | raw u32,0 in these lamps |
| 4 | translation float3 |
| 16 | homogeneous float1 |
| 20 | quaternion float4 |
| 36 | scale float3 |
| 48 | raw source flags/kind (66 or94); interpretation retained as unknown |
| 52 | FAB asset ID |
| 56 | instance/entity ID;0 is permitted |
| 60/64/68 | raw u32 values, usually1/0/0 |
| 72 | repeated FAB ID |
| 76 | raw u32 mode; retained without assigning meaning |

For the bridge actor, header0x98 has count26, row17 has FAB540961, entity0, flags66, T=(5173.41015625,-86035.984375,5857.6357421875), Q=(0,0,0,1), scale=(1,1,1). Source-only transform is `world=rotate(conjugate(Q),local*scale)+T`. A second visible actor0x98[16] has a nonidentity Z rotation and exactly matching authored translation(2060.06201171875,-83377.53125,5577.02587890625).

Seven captured main-pass draws match source vertex+index hashes for these two actors. Source-only matrices reproduce all seven captured matrices within1.22408e-8. The bridge actor draws assembly10 at67763,9 at68088,11 at68279 and12 at68589. The other actor draws9 at68080,11 at68281 and12 at68587; its base is not present in this capture's draw list. No general visibility/culling rule is inferred from that absent part.

This direct actor collection was outside the earlier84-byte cached-render-array search and the v41 typed-entity catalog. A generic importer should read this actor array directly; it does not need to guess a simtype from FAB names or drop entityID0 records. Other actor families can require FAB local-node transforms (the independently recovered cart has such a candidate); this lamp's direct transform is verified, not a license to omit all FAB node transforms.

## Counts and authored LODs

There are **32**, not the initially estimated27, source540961 actor records in the audited Dal spaces. All hits are in0x98. Fourteen actors' whole geometry bounds intersect the requested203 visible cells. They occupy six existing cells in the unchanged1271-cell registry. Source IDs are stable `0x40000000 + ordinal` within the saved32-actor catalog; the full provenance includes space/header/record so zero entity IDs remain distinguishable.

The extracted source FAB declares:

| Colour group | Assemblies | Raw distance range | Triangles per actor |
|---|---|---|---:|
| 1 | 0,1,2,3,4 | 0..2000 | 1884 |
| 2 | 5,6,7,8 | 2000..3200 | 924 |
| 3 | 9,10,11,12 | 3200..9000 | 470 |

Each element's explicit distance min/max agrees with its group. Other colour groups are empty. The secondary lists are preserved in metadata and are not emitted as extra geometry. The old reference FAB parser reports identity static-bind candidates for all13 elements, with bone indices2/3/4 corresponding to these LOD groups. The complete authored metadata is retained in `lamp-authored-groups.json`.

Actor LOD ranges use **distanceScale1**, not the region-tree pack's inferred0.5. The bridge actor origin distance is3618.032849, and native uses group3. Applying0.5 would incorrectly select group1. The second actor distance7542.485406 also agrees with group3. These two observed fixtures support the actor setting; generalized user quality modes remain outside this check.

All three groups are stored, but only one is enabled per actor distance. Stored cost is65,590vertices,45,892triangles across all groups,182ranges,5,544,448geometry bytes. If all14 actors used the same group, costs are26,376near,12,936middle or6,580far triangles. Four staged textures total1,398,208bytes.

## Auxiliary format and materials

Geometry format is the parent's OARGEO1:28-byte header,76-byte vertices,48-byte range records. Each range is `<4I6fIf>`: material row,first index,index count,original actor flags,LOD anchor(raw actor T.xyz and conservative radius),minSq,maxSq,sourceIndex,per-range distanceScale1. Group/rank remains in JSON. Whole-instance bounds determine the centroid cell; geometry is not split at triangle centroids. `lamp-index.bin` is OARGIDX1 with six cells,materialCount299,header distanceScale1 and actual bounds. Base index files remain unchanged.

| Native material | Source shader | Staged row |
|---|---|---:|
| 489075 vil_wood | dot3offset | 11 |
| 489077 vil_stone | dot3 | 14 |
| 374967 for_house_copper | glassmetal | 43 (92 is a duplicate signature) |
| 489073 vil_glass | glassmetalwithemissiveprobe | 12 |
| 654012 vil_lamp_glass | textureemissive | **298, new family8** |

The first four rows retain the existing shader/profile limitations; their native material identities and source geometry are preserved. Only654012's active emissive shader is newly reconstructed exactly here. `material-298.native84.bin`, `material-298.mats28.bin` and `material-298.json` are row-only merge candidates. Source header and active PS838 have no alpha test/discard, and source cull2/native pipeline use BACK. MATS candidate flags are0x10000000, no alpha bit/cutoff.

## Active PS838 / VS837 emissive contract

Captured draw68589 CB0 is `(1,1,1,1; 1,20,0,0; 1,0,0,0)`. Source RGB, strength and specular agree; its colour padding alpha is not read. Source parameter keys are emissiveRGB9647303,SpecularValues11960536,strength10055862,U-scroll1462591,V-scroll1473230. VS837 uses `UV=sourceUV+gameTime*CB0[2].yz`; both speeds are0 for this material.

Let D=diffuse.rgb, C=vertexRGB, a=vertexAlpha, S=specularMap.g, M=emissiveMask.g. Decode DXT5nm as xy=2*(normal.r*normal.a,normal.g)-1 and z=sqrt(sat(1-dot(xy,xy))). The final material normal is normalize(TW*xy.x+BW*xy.y+N0*z), with raw interpolated N0/TW/BW. Individual basis vectors are not normalized again per fragment.

- rawSpec=S*specularStrength.
- G0=(normal*.5+.5,sourceGloss).
- G1.rgb=sat(D*C*a), G1.a=sat(rawSpec*a).
- q=rawSpec*ambientSpecularScale, **without vertex alpha**.
- E=M*D*emissiveRGB*emissiveStrength, **without vertex RGB/alpha**.
- G2.rgb=sat((1-sat(q))*cube(normal.xzy)*(D*C*a)+q*skyRGB*pow(sat(reflect(-V,normal).z),skyAlpha*ambientExponent)+E).
- G2.a=sat(dynamic luminanceShiftId), captured0.4375.

G-buffer stores are native HALF, followed by the ordinary deferred lighting, AO/shadow combination and fog. Thus emission is added **inside G2's clamp/HALF**, and native deferred AO subsequently multiplies the whole G2 term. Adding emission as an unlit post-light term would differ from the capture.

The profile candidate follows the parent integration mapping: color=(1,1,1,unused0),specular=(1,20,1,0),UV=(1,1,0,0),native_t=(693diffuse,694normal,695specular,696emissiveMask,unused...). The concise GLSL helper and independent interpreter validation are in `emissive-contract/`.

## Textures and sampling

Active native resources are256square,7 authored levels: binding33/image7829 diffuse489069 BC1_UNORM,34/image7796 emissiveMask489969 BC1_UNORM,35/image7824 normal490046 BC3_UNORM,36/image7816 specular492241 BC1_UNORM. All28 tight compressed mip payloads match source KEEN carriers **byte for byte**. Source original dimensions are2048; this capture loaded the authored256 carrier (shift3). The staged693..696 maps decode those seven original levels to linearRGBA8 OATX, without generated mips. This matches the requested reference resource level; higher-resolution streaming variants remain preserved in source, not claimed implemented by this stage.

All four material samplers are LINEAR min/mag,LINEAR mip filtering,REPEAT,anisotropy disabled. The existing loader's generic anisotropy4 should not be applied to693..696. Existing slots32..34 are1024 with11 generated/current levels, so they are not byte-equivalent to these exact reference resources.

## Validation and boundaries

Independent CPU interpretation of active PS838 across400 random material/frame samples agrees with the concise formula: maximum G0 error5.96e-8,G1 exactly0,G2 error4.77e-7; cube direction error5.96e-8. GLSL helper compilation passes. This validates arithmetic, not a GPU render or texture filtering.

Independent pack validation checks every cell shape, index bound, nonoverlapping run, material298 profile, actor/source flags and anchors, one LOD group per test distance and all four OATX shapes. Two source poses/seven captured matrices are independently compared. The pack preserves source normals/tangents/bitangents,UVs andRGBA.

The source scan, raw records,FAB/stream hashes,source material,all texture carriers,capture bindings,source mip comparison and staged manifests remain in this directory. No source/core/live asset/database writes, original launch,replay,GPU action or waterfall change was performed. Integration and visual validation belong to the parent.
