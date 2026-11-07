# Source character cosmetic materials: sealed integration handoff

The opt-in portable material adapter and resource bank are ready for parent review/integration. All124 nonzero source materials in the189-model appearance catalogue map to9 reviewed source shader families. All412 exact-size/hash-pinned texture resources upload successfully in the existing ANGLE GLES3 fixture. No live core, deployed asset root, original database, user state or UI was changed by this task.

This establishes material arithmetic, source resources and actual GPU drawing. It does not claim a matched original creator image, every option rendered on a tablet, source animation timing, source room lighting parity or a performance measurement. The parent owns full actor/UI option vetting and deployment.

## Files and integration sequence

Implementation is FROZEN at implementation-freeze.json; final-validation-receipt.json confirms every frozen hash remains unchanged. Add oa_cosmetic_material.c/.h and oa_cosmetic_texture_bank.c/.h plus the3 generated cosmetic_*.inc tables. Bank imports the existing host opening_sha256.h. Shared fragment comes from root oa_world_fragment_source(), replacing its4 unique character hooks; no copied common lighting implementation is maintained here.

Copy the textures/ directory unchanged beneath any caller-selected prefix. texture-bank-whitelist.json pins all412 assetID/target/size/SHA records; the compiled cosmetic_texture_pins.inc enforces those before GL allocation. 411OATX2D files plus eye744821.oacube total480831000bytes. They retain all authored mips of the<=512 authored tail; no generated mip, resize, gamma adjustment or invented missing image. The special source filenames1446812 _N.dds and1446813 _N.dds really include a space before the suffix; their patch-precedence texture chains are present.

1. Build the parent source selection/plan; obtain per-component world matrices from exact source CMAP/CPAI pose API.
2. Open material context with borrowed CharacterAmbientMap cube and world ambient cube, native-assetID texture callback and supported light count. Set borrowed dynamic environment probe explicitly.
3. Upload canonical96B surfaces and validated own-component palettes. Caller transiently marks proven missing56/64 COLOR as native-default-white128; preserve authored60/68 COLOR. No facial ancestor collapse or second world rotation.
4. Call oa_cm_resources_ready() for EVERY selected material and instance before atomic publication. It calls the same resource resolver as draw, includes skin/head diffuse overrides, selected tattoo and dynamic probe, has no framebuffer/viewport/draw side effects. Lazy callback uploads can mutate texture bindings; invalidate parent cache accordingly.
5. At draw time call oa_cm_begin(actual world eye) THEN upload actual environment/lights/fog/AO/shadow uniforms. begin resets ambient-only inspection defaults; draw does not reset them. Reapply external sampler state as needed.
6. Draw opaque families with depth write enabled. Draw kind7 after opaque, SRC_ALPHA/ONE_MINUS_SRC_ALPHA and depth write disabled. Caller owns state, viewport, FBO and culling.
7. Any failed/unsupported surface/resource returns failure without requiring removal of the old renderer fallback. Bank/model resources are borrowed as documented; context owns only its shader/dummy textures.

## Material/input equations and evidence

material-family-ledger.json provides all9 families, each MID list and explicit equations/qualifications. material-catalog.json and all-source-materials.json preserve every source carrier path, SHA, exact parameters and slots.

- Skin649640: source hands513702 joins actual PS462 material, alpha mask and linear diffuse. Skin color is mix(D,D*skin.rgb,skin.a), with source gray Fresnel boost before vertex color. Mask GREEN strictly below authored cutoff discards; equality survives. BodyDiffuse override is explicit.
- Head649436: active VS429/PS430 uses mapped normal. Overlay sequence is tattoo, eyebrow, eyeliner, lipstick, using authored UV1 and mask channels. UV1 and a resolved real tattoo resource are mandatory, including NoneTattoo365597. The full active PS430 has no discard even though the source material carries an alpha-test field; do not apply the body-mask rule to it.
- Hair737390 and Beard976276: native full mapped normal, slot7.GREEN blends the independent two-color pair, slot1.GREEN supplies the authored alpha-test mask. Beard uses its own selected pair.
- Eye737934: actual PS394 matches source authored diffuse744833,mask744834 and all30 source cube744821 face/mip blocks. The authored eye reflection cube is separate from the dynamic scene probe. Eye color/emission follow the native shader, not generic skin tint.
- HardLight545212: uses reviewed source/native family12, including raw source gloss*.25. Generic world q/sky ambient must not leak into CharacterAmbientMap G2.
- Dot38827 mouth/detail preserves reviewed shared world family1 and world cube.
- CharacterReflect545211: separate dynamic probe, linear mask.GREEN, environment tint and native instance row3 multiply the reflected sample inside G2. Material TintColor is unused by the optimized pair; creator EyeColor is not substituted.
- FogAdditive375696 head auxiliary actually uses source acda7765676bc715/PS976: RGB has no fog-color mix; alpha uses mask.GREEN and per-pixel clipW exponential fog. Actual native blend is SRC_ALPHA/ONE_MINUS_SRC_ALPHA, not inferred additive from its source family name.

Source palette packed ARGB conversion uses the exact native double multiplier0.0039215688593685627, no sRGB conversion. Skin alpha is caller-explicit. Concrete all8 creator/all4 final Type source StatsBlueprint skin high byte255 is now proved by the gameplay agent. Eyebrow alpha is not simply the fresh blueprint0: exact PLAYER.set_eyebrow_color callback keeps selected palette alpha when prior alpha0; it initializes255 for the source default callback. Other setters preserve existing alpha as separately documented. evidence/eyebrow-blueprint-contract.json pins field/setter/CB identities.

The weighted basis matches native VS375/417/429: native residual fourth weight, index range78, N/T skinned and normalized, B entity-only normalized. Supplied bone rows are already world-space; do not apply facing a second time. Raw native signed-byte indices are represented safely by current canonical bytes because all189 actual source models have max30 and no sign-bit values. No generic signed-to-unsigned admission is claimed.

## Dynamic scene reflection fallback: closed

dynamic-probe/REPORT.md preserves exact native producers and query. RenderConfig+0x14 is initialized by00d32700 from TextureMgr+0xf0. TextureMgr initializer00cbc310 creates SimpleBlackCube4x4x6 with allDWORD0, before renderer setup00d35760. Query00c97e90 begins with this resource and FLT_MAX squared distance, then selects the nearest source point across registered collections using ordinary3D squared distance and strict less-than.

CreatorSpace1583581 has0points, so the exact native creator fallback is a borrowed4x4 six-face RGBA(0,0,0,0) cube. Parent is creating/owning it. It is neither the world ambient cube nor candidate2036011 default_cubemap; the latter was explicitly rejected against active Gorhart3574. General gameplay point-registry integration remains outside this creator adapter.

## Raster culling: closed for current projection convention

evidence/01070c60-rasterizer-state.c proves source cull0->D3D11NONE1,1->FRONT2,2->BACK3. All124 source material rows carry2. All13 relevant recorded character pipelines are BACK/CLOCKWISE, including hair/headaux.

The actual recorded viewport62519 has height-864. For unchanged source indices, orientation-preserving component transforms and ordinary positive-height GLES viewport with no clip-Y inversion, equivalent parent state is GL_BACK with GL_CCW. An explicit clip-Y inversion or reflected transform reverses the front convention; caller owns that choice. Do not copy the recorded Vulkan CW bit blindly.

The actual source actor's10994 triangles give10991 positive cross(edge1,edge2) dot summed source normal and3 negative. Test-only ANGLE culling variants preserve the frozen implementation: CCW differs from disabled in405pixels, CW in26627pixels (interior surfaces). All3 compile/draw with GL0. Receipts and screenshots are cull-*.txt/.rgba/.png and evidence/character-cull-contract.json.

## Validation and scope

- Existing ANGLE2.1.27600 f39c3524d091 on NVIDIA RTX4080SUPER, D3D11 driver32.0.16.1692, EGL1.5/GLES3. Exact renderer.json preserved.
-412 pinned source resources: hash/size validation plus actual GL uploads PASS, GL0. Corrupt/unreviewed resource rejection tested.
-22 material raster cases PASS.20 independent source-math oracles compare327680 RGBA channels with0mismatch, including skin alpha0/.6/1, cutoff below/equal/above, distinct2x2 UV1 overlay patterns, hair/beard, eye and probe tint.
- Oracle uses previously measured ANGLE nonnegative half towardzero behavior. Ideal IEEE nearest-half can differ1code; this is not a universal/native GPU quantization claim.
- Actual default AlmainMale source creator idle703318 frame0: exact component maps/palettes,14draws(13opaque+1transparent),10994triangles,27088nonzero512x512pixels,35real textures, GL0. Actual-source fixture is ambient-only and source-pose timing/camera is not compared to the original creator.
- Both portable C modules compile C99 for Android26 ARM64 with NDKr30 -Wall -Wextra -Werror. No tablet GPU run is claimed here.
- Named platform-ID to embedded permutation-table entry remains unjoined. Actual active full-quality mapped normal for head/hair/skin is independently recorded; low peers are retained explicitly and are not silently selected.
- No remaining missing required material/image/probe input in this source catalogue. Full-option live readiness and all race-sex appearance quality still require the parent's actual actor/UI test matrix, not this one-actor smoke receipt.

All proof/artifacts stay inside this staging folder. final-validation-receipt.json and implementation-freeze.json are the concrete handoff pins.
