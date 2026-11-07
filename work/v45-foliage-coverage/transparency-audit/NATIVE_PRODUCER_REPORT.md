# Bounded native producer follow-up

Scope: cached `work/v30-engine/decomp` exports and function/name/class inventories only. No Ghidra session, new replay, GPU, core/live asset edits or new random algorithm. Eight function bodies inspected, then stopped as authorized.

## Search coverage and class identities

Approach1 searched2469 cached C files (55,745,395bytes) for exact channel/class hex and decimal literals. Approach2 searched existing names/classes/functions/RTTI inventories for particle/emitter/dimension/angle/factory seeds, then checked address-form literals. Raw results are in native-producer/exact-channel-search.json, name-seed-search.json and address-form-channel-search.json. Missing literal hits are not evidence that runtime consumers do not exist: decompiler address-expression forms and indirect task properties can hide them.

Exact class hash identities from cached class methods:

-0xec5a12 = BHG_TaskletDimensions.
-0xc263f8 = BHG_TaskletFlatness. Therefore particle2132's float10 is **flatness**, not an initial rotation or10/2 angle conversion. This supersedes the earlier angle candidate based solely on numeric correlation.
-0xb40224 = BHG_TaskletBitMask.

The actual source emitter2131 has two separate integer channels0x1234094 and0x1261f62, each5. Cached named BHG_TaskletMinMaxAngle vf3 (00cba630) explicitly writes its second angle to LAB_01261f62. The fixed source5 values are thus meaningful angle-channel evidence, whereas flatness10 is unrelated. The MinMaxAngle constructor delegates defaults to FUN_00c47430; this helper was not read within the cap, so the first default-name assignment and exact native radians conversion have not been followed end-to-end.

## Dimension input contract, not a guessed lifetime interpolation

BHG_TaskletDimensions vf3 at00cb9eb0 invokes separate context getters00c79b90 and00c79c70, scales their returned inputs by the corresponding spline's final control-point time, and evaluates a clamped spline via00ae60a0. This is a genuine two-dimensional producer, not the current one-size scalar simplification.

The getters use authored name/type bindings:

- X: property name runtime+8, kind+0xc, normalization bias+0x90, scale+0xa0.
- Y: property name+0x80, kind+0x84, bias+0x98, scale+0xa4.
- Kind0x57bad reads int,0x12f35f reads float,0x1bf3d2 reads a vector-derived magnitude.
- For a recognized property, the result is `(value-bias)*scale`; unsupported/unbound kind falls back to the caller's float argument. A missing recognized property yields0 in the cached pseudocode.

Thus **the native Dimensions tasklet does not hardcode normalized lifetime**. Establishing whether this source record uses caller time, normalized age, a named property or a constant requires following serialized property binding and the execution caller, outside this eight-body cap. The cached Dimensions loader00d358d0 reads two spline pairs, per-axis fields, and a final0x32-byte group; its helper loaders were not decoded. It would be incorrect to map the currently retained width pair550→750 directly to current `age/life` simply because the spline's time keys are0 and1.

Mode3 initializes per-instance offsets: it evaluates each base spline, calls00cadc60 with that base and authored per-axis random parameters, and stores `selected-base`. Subsequent modes reuse the stored offset rather than drawing new values. The random helper00cadc60 was not inspected, so no distribution or seed is claimed. The pseudocode has register/stack recovery artifacts (`unaff_EBX`, `unaff_retaddr`, a pointer typedfloat); source lines support the high-level persistent-offset contract but should not be copied mechanically as C.

The source/capture measurement remains exact: source width keys550/750, height2500/2500; all6 sampled native quads have half extents550/2500 even though vertex colours differ. Native lifetime-linear width interpolation is not supported for this capture. Preserve full source curve/mode/binding fields until caller correlation is complete.

## Orientation evidence and limits

Captured source-linked quads obey the emitter-local-X cylindrical basis described in the main report, at5degrees modulo180degrees. This matches the fixed source5 angle channels. Simultaneous U/V sign reversal remains unresolved. Parent's proposed explanation—source random velocity lies on emitter-local±X, so velocity-aligned billboarding reverses both axes—is consistent with source `(10,0,0)` random velocity and the capture. The native velocity/billboard consumer was not inspected, so it remains a hypothesis, not an implemented new random policy.

The worldZ-up flag is contradicted for this source family. Flatness10 must not be used as an angle. Fixed5degrees without the source sign branch is not declared exact parity. Texture and PS1040/1042 corrections remain independent and promotion-ready; source shape metadata remains a review candidate.

## Exact eight-body ledger

1.00cb9eb0 BHG_TaskletDimensions__vf3.
2.00d358d0 BHG_TaskletDimensions__vf5.
3.00c46fa0 BHG_TaskletFlatness__vf3.
4.00cba630 BHG_TaskletMinMaxAngle__vf3.
5.00a1c860 BHG_TaskletMinMaxAngle__xtor.
6.00c79b90 X authored-input getter.
7.00c79c70 Y authored-input getter.
8.00ae60a0 clamped spline evaluator.

Verbatim bodies are preserved in native-producer/. No ninth body was opened. No promotion-ready shape binary was emitted to conceal the unresolved producer choices.
