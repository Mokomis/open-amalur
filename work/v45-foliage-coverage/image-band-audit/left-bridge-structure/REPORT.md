# Missing left-bridge structure: overturned cart recovered

Native draw68274 is conclusively **FAB638222 for_cart_overturned, assembly0**, native material426015 for_cart, existing legacy materialrow10. Source VB and IB match the capture byte-for-byte. The source stream was missing from the previous1270cached-stream scan and was extracted as one specific archive entry into this private audit folder. No whole archive extraction, game/replay launch, core edit or live asset promotion.

## Exact indexed draw and source proof

VB8611:89,664bytes,1,868vertices at48bytes, SHA9af51667c0af71a3a20f9b6264eb0d57188ec0ef03c6b010b7cff0c8b61b6d6d. IB8613:7,776bytes,3,888u16indices/1,296triangles, SHA6b37064367fe4c3b21ac88e10c4b6f06dca57d386568dd96a820a1f911f99af0. Bind offsets, firstIndex and vertexOffset are all0; all1,868vertices are referenced. This is the complete mesh, without an aggregate-buffer subrange ambiguity.

Source: DATA_0.pak/638222.fab_visual_data_streamable_bin,97,520bytes, SHAb55899540dc9bdec4f1d47720e18b5c4ec34ed819d2e8c51cb3c9f933742e830. Sole VB0 and IB0 are exact matches; assembly0 references both. Layout: pos3f@0,UV2f@12,N/T/B snorm4@20/28/36,RGBA8@44.

Projected native-source mesh bounds reproduce the requested target: x777.3114..918.4690,y463.8762..542.0900 at the reference1536x864 projection. This is a geometry/projection match, not a name or appearance guess.

## Authored source instance

PATCH431646.space_bxml, out_dal_west_01. Actor array pointer/count is header0x98; recordstride80, row0, rawfile offset8540. Instance/entity1390820, FAB638222, rawtype94. Translation(5718.794921875,-85493.5546875,5852.23486328125), quaternion(-.022241337224841118,.021964486688375473,.7111735343933105,.7023211717605591), scale(1,1,1). The world rotation derived from conjugate quaternion matches native within5.3e-8.

|Offset|Recorded field/value|
|---|---|
|0|u32 0|
|4|translation3f|
|16|float1|
|20|quaternion4f|
|36|scale3f|
|48|rawtype94; meaning not decoded|
|52|FAB638222|
|56|instance1390820|
|60|u32 1|
|64|u32 0|
|68|u32 0|
|72|repeated FAB638222|
|76|u32 1|

All80rawbytes and all20u32/float views are preserved in source-and-placement-contract.json. This actor table was outside the earlier static-render-array recovery paths.

## Placement offset: source evidence and limit

Captured renderT=(5717.96142578125,-85493.5546875,5865.5439453125), a world delta(-.83349609375,0,+13.30908203125), or local approximately(0,-.000221,+13.335156).

The specifically extracted metadata638222.fab_bxml is1,172bytes, SHA0bbf47a620353d828a5fa47243e5f2be3f10fd32386de3cce4c5ff7866b6ad2b. It contains repeated48byte transform-shaped blocks at148/196: identity quaternion, translation(0,0,+13.334948539733887,1), unit scale. SourceactorT+conjugate(q)*that source-local translation, rounded tofloat32, reproduces all3captured renderTcomponents exactly.

This proves source bytes and numerical composition, not the owning node/physics/bind semantics. It must not be described as a decoded bind. The source-composed staged positions match1,839/1,868native-fixture packed vertices exactly; remaining maximum difference is.0078125cm, one large-world floatULP. Raw authoredpose remains separately provided with the13.335cm placement difference visible in metadata.

## Ready staging geometry and runs

Each OAWE76 file has1,868source vertices,3,888u32indices, one draw(material10,first0,count3888), all76byte vertex attributes, native materialID426015, source flags3, UV1 duplicated from the single sourceUV. Triangles remain source indexed geometry. All lie in cell(0,-14). Full-rangeLOD auxiliary runs, bounds, sourcekind space_actor_0x98, rawtype94, sourceinstance1390820 are in aux-cart-runs.json.

|Pose / purpose|OAWE file|SHA256|
|---|---|---|
|native-static-pose|cart-638222-native-static-pose.oawe|5bab347016f4d950874acd5625ce7570c269e5a51af34c6328e075ff683d43a7|
|authored-actor-pose|cart-638222-authored-actor-pose.oawe|7ef5fe832a79596d4ec991f8cdc7273aae9d35536d0624bec73f9889220f6545|
|source-actor-plus-FAB-local-candidate|cart-638222-source-actor-plus-FAB-local-candidate.oawe|48e5188c8e495571b01b5b04b7ec2067629d414ce8fe281f0755f3d63e5a597c|

The raw authored actor pose and sourceactor+FAB-local candidate are source-driven candidates; the native-static pose is a separately labeled comparison fixture. Root chooses integration. No existing percell indices require removal because this source asset was absent from the earlier cached geometry import.

## Material limit and validation

Existing row10 has exact signature diffuse425985 for_cart_base, alpha426863, normal426928, spec426869. Source material426015 uses shader358221 fresnelglassmetalprobe and cube379578; captured material includes spec(1.7697,100) and multiple color controls. Row10 restores baseline material compatibility. Exact native fresnelglassmetalprobe shading remains outside reconstructed static families1..4, and these staging files do not claim shader parity.

Independent serialized reread validated OAWE counts, material/index run, exact original index sequence, sourceUVs, bounds and hashes. The original source stream and native buffers remain unchanged. Source-and-placement-contract.json, cart-validation.json, extraction logs and native-subrange-evidence.json retain full provenance.
