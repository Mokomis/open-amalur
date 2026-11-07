# Portable creator state/profile staging

This folder is standalone C99 data/state code. It does not change core/menu code, render cosmetics, execute the native game, apply gameplay stats, or read/write any user save/settings file.

Compile oa_creation.c and oa_creation_source_tables.c with oa_creation.h and the generated table header. No dependencies beyond C99 stdint/stddef/string. Windows test command: run_tests.cmd from this directory. Android compile-only checks use the existing NDK, no install/device execution.

## Supported source data

Eight definitions:4races x2sexes; five source presets each; six allowed patrons per race, including None buff1697849. Nine raw racial skill deltas use10 units per displayed rank. Default names, full/lite player simtypes, rigs, cosmetic item simtypes, palette order/raw five-word records and alpha values come from the finalized v49 source catalogue. Generated asset filters preserve the184 source category/race/sex-mask records.

Begin uses m_default_customization, which is distinct from applying source preset1. Preset0 in a profile means source defaults/custom state origin. Begin/select_type selects the race's first allowed patron as explicit HOST MODULE POLICY, not a recovered original automatic choice. select_type resets default appearance/patron and changes the name only if it was still marked as a default; user-entered names persist.

Source lookups expose all forty raw presets. Applying these five returns OA_CREATION_SOURCE_PRESET_UNRESOLVED without modifying state:
Almain/Female5, Varani/Male5, Varani/Female5, Ljosalfar/Male2, Dokkalfar/Female4.
Their authored palette indices exceed the recovered option lists. No guessed native fallback or clamping is implemented. Other35 apply and validate. Source table lookup still exposes the exact problematic values for review.

Assets are validated against category/race/sex masks, not assumed unlocked by the original entitlement predicate. Ears0 means UNSPECIFIED (not an invented native None item); elf render selections flag this. Female beard0/color0 is the source absence case. All real None tattoo/accessory choices remain their nonzero source simtype IDs.

oa_creation_render returns explicit head/hair/beard/ears/tattoo/accessory simtypes, full/lite player IDs, rig, exact color records, alpha values, and selected skin head/body diffuse IDs. It does not convert packed color words, multiply tint textures, pick a replacement mesh, or apply native cosmetic shaders. Its warnings always state that visuals and native availability/name-filter semantics are unimplemented/unverified; female animation and unspecified elf ears have additional flags. Successful state validation is not a full visual creator claim.

Name policy is deliberately explicit: strict UTF8,1..16 Unicode scalar values,1..64 bytes, rejects ASCII controls and invalid/overlong/surrogate/out-of-range UTF8. The original source editbox limit is16; native UTF16/byte counting and special-character sanitizer are not established. This custom policy is not labeled native-equivalent.

## Host integration and exactly-once effects

1. oa_creation_begin; select_type/patron/asset/color/alpha/name or apply_preset while DRAFT.
2. oa_creation_finalize(state,host_unique_nonzero_token,&candidate). State becomes PENDING. Candidate includes the profile snapshot, raw nine-skill deltas, selected patron buff, caster/tag1731073,duration-1 and restore-health-to-max request.
3. Repeating finalize with the same token returns the same candidate. Another token is rejected. Selection changes are locked while pending.
4. The host applies effects to a transaction/snapshot, acknowledges a COPY of candidate.profile with the same token, serializes that COMMITTED profile, and atomically persists BOTH gameplay changes and profile acknowledgement. Only after success replace the active UI state.
5. COMMITTED finalize returns ALREADY_COMMITTED and zeroed candidate output. Duplicate acknowledge returns ALREADY_COMMITTED. Loading the committed envelope preserves this guard.

The module cannot make separately written stats/profile files crash-atomic. If the host grants effects then persists acknowledgement separately, a crash can still duplicate a grant. Host transaction/atomic snapshot ownership is REQUIRED. cancel_pending is valid only when the host transaction has not applied effects, or has rolled them back; it is not an undo operation on gameplay stats. Token uniqueness is the host's responsibility. No RNG or implicit permanent save identifier is invented.

This candidate covers CREATION CHOICE effects only. It does not silently implement the native patron buff bodies, inventory bootstrap, global stealth/reckoning initialization, cinematic/timing/quest transitions or skill actor-state rebuild. The host must implement these services separately. Raw skill array names/order are exported in oa_creation_skill_names; do not use displayed ranks as raw values.

## Envelope and validation

Separate OACREA1 envelope, version1, little endian, explicit fields rather than C struct layout. No legacy/native save format is overwritten. Current source catalogue CRC32 is0xa08d9075; a different catalogue requires explicit migration rather than silent reinterpretation.

32B header:
magic8 OACREA1\\0; version u32@8; payload bytes u32@12; payload CRC32@16; source catalogue CRC32@20; zero reserved words@24/@28.

Payload:
race/sex/preset/patron/phase/customized/name_is_default:7u8;
four alpha bytes;
UTF8 byte length u16;
six cosmetic simtype IDs u32;
eight one-based palette indices u16;
host transaction u64;
revision u32;
exact UTF8 name bytes, no stored terminator.
Fixed payload65B plus name. Maximum encoded profile161B; public buffer allowance192B.

Deserialize rejects truncation/trailing bytes, bad magic/version/reserved fields, CRC mismatch, unknown source catalogue, invalid UTF8/name length, invalid state transitions/tokens, out-of-source asset/palette/patron selections, and falsely uncustomized appearance data. It leaves the destination unchanged on failure. Serialize validates state and never truncates output to fit a short buffer. CRC32 is corruption detection, not authentication/security.

## Validation

tests-result.json: standalone MSVC14.51 x64,/std:c11 /W4 /WX /O2,1379 checks,0failures. C source is C99-compatible; android-c99-compile.json confirms both runtime/table sources compile with the existing Android NDK target aarch64-linux-android28,-std=c99 -Wall -Wextra -Werror.
Coverage includes all8 definitions/40raw presets, the5 unresolved source cases, actual source IDs/skill deltas/None buff, cross-race rejection, UTF8 boundaries, draft/pending/committed round trips, same-token retries, acknowledgement/cancellation locks, every encoded-byte flip and truncation, and forged CRC-correct invalid selections.
No GPU/device/native-game execution or user file I/O occurred.

generate_source_tables.py writes only this folder and records input hashes in source-tables-receipt.json. Its canonical catalogue fingerprint excludes path/annotation fields and includes actual choices, palettes, masks, stats and patron records. The finalized source evidence remains in the sibling analysis/staged-source folders.
