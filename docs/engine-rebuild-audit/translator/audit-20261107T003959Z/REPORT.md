# Original-code translator audit — 2026-11-06

**Decision:** the retained translator is a compiled ARM64 prototype with concrete semantic defects and an isolated animation-decoder harness. It is reusable investigation infrastructure; it is not an execution-validated original engine or an immediately trustworthy engine substrate. No full-engine performance conclusion follows.

This pass only read existing files and decoded existing PE bytes with the cached Capstone library. No project scripts/binaries, game, build, installation, replay, capture or database session ran. All audit output is in this unique folder. Paths below are relative to C:\Users\rwill\Documents\Opem Amalur unless absolute. facts.json hashes the inspected sources/artifacts and preserves individual defect witnesses.

## What exists and what execution is actually proven

1. work/v30-engine/recomp/translate-report.txt:2–11 records73971 generated entry translations and3738147 instruction emissions, including46119Ghidra entries,27729raw data-pointer seeds,123new direct-call targets. The current out/functions.txt has73971lines and50koa_*.c chunks.
2. compile_all.py:9–12 compiles those chunks for aarch64-linux-android29 at-O1 with warnings suppressed(-w). compile.log, decoded asUTF16, lines1–6 records50/50success,0compile failures. All50ELF AArch64 object files are present. This proves successful C compilation, not instruction/CFG/runtime equivalence.
3. out/link.rsp:1–53 lists50chunks plus rt.o,table.o,native_test.o. out/native_test is an existing53523656B ELF64/AArch64 binary, SHA258f81c2b7efaf3e7a561b9127f8a5972b524ec12093d24bf14e42212e62bfd4. A linked artifact is present; build.log is empty. Source copies out/{rt.h,rt.c,native_test.c} are byte-identical to the parent copies.
4. native_test.c:86–155 is a targeted decoder harness. It maps one pristine PE image at0x400000, a64MiB low-address arena including8MiB guest stack, reads one skeleton and one clip, builds guest-cdecl arguments, and directly calls f_0111bf10 once per decoded source frame. It checks resulting ESP and writes transforms. It does NOT enter the original executable, initialize the engine, resolve imports, create original actors or run an update/render loop.
5. bake-test/ contains456813.fab_bxml,457525.anm_bxml and pc.bin. The latter is310284B, header64joints/101frames/fps29.999998, SHA1204bc868cba3787db3129cf2bf1fbda6fd1f4fa012e1c5b279547e605752b1b. This is a reference-shaped artifact, not a retained successful ARM64 translator run/comparison receipt. No translator stdout, return-code receipt, ARM output transform file or byte-comparison result was found in this directory; parent confirms no known additional Mac/tablet execution receipt. Therefore auto-translated native_test EXECUTION AND EQUIVALENCE ARE UNVERIFIED. The source's timing printf is not a measurement.

Do not interpret the73971entry count,50object count,trap counters, or linked binary size as engine coverage. There is no recorded dynamic path/edge/semantic coverage manifest here.

## Concrete defects in current generated code

### Wrong starting block after backward reachability

recomp.py:591–643 follows direct branches, including targets below the function entry. It then sorts all instruction addresses at652/663, emits the body at665–748, and does not insert an initial jump to the requested entry.

A genuine Ghidra-exported function starts at011c1340 (functions.tsv:44494). Original PE bytes at011c1340 are:
    xor eax,eax; mov al,[esp+8]; push ebx; mov ebx,eax; ...
Its conditional branch011c135f reaches a shared lower epilogue011c1330.

But out/koa_018.c:58203 defines f_011c1340 with its FIRST executable block:
    L11c1330:
    eax=edx-1;
    pop ebx;
    esp+=4; return;
The real entry's xor/mov/push follows that return. Calling this translation begins at the epilogue, not011c1340. This is a source-level correctness failure, not a hypothetical performance issue.

A conservative text search found266generated definitions whose initial lower label precedes the named entry;79are Ghidra entries. facts.json lists every witness. These counts are diagnostics, not an estimate of reachable broken functions. Each actual caller must be validated.

### Actual CRT memory bitset operation is mis-translated

Original _strpbrk at011c1f10 (functions.tsv:44514) allocates/zeros32bytes, reads character values into EAX, then uses:
    011c1f2d bts dword ptr[esp],eax
    011c1f41 bt  dword ptr[esp],eax
This is a256bit character-set bitstring; a register index beyond31 selects another memory word.

recomp.py:452–455 instead reads/writes ONLY the base word and masks every index with31. It never advances the effective memory address for the higher bit index. Thus character values separated by32alias. For example a delimiter'A'(65) and input'!'(33) map to the same generated bit1, unlike the original distinct bits. This is a concrete semantic counterexample in an identified original routine; this pass did not execute it. Correct bitstring addressing/operand-width behavior requires repair and differential tests.

### EFLAGS are not caller-dependent CPU state

rt.h:11 declares GPRs/XMM only in cpu_t. EFLAGS are absent. recomp.py:742–748 saves/loads only used GPRs/XMM and initializes cf/zf/sf/of/pf=0 at EVERY translated entry. Calls at692–696 execute SV/call/LD without flags. Consequently:
- a callee/tail target cannot receive actual incoming flags;
- a caller retains its PRE-call local flags instead of the callee's resulting flags;
- shared tail blocks/assembly helpers depending on inherited flags cannot work generally;
- AF is never represented; PUSHFD at483–485 also omits DF and other architectural bits.

The per-thread DF/FS/MXCSR/x87 globals are a separate state model and do persist across C calls; they do not repair local EFLAGS. Ordinary compiler-generated functions often overwrite flags before using them, so this observation is NOT a claim that every call fails. No dynamic live-in/live-out flags oracle or proof that all connected engine paths are independent of caller flags is present.

This needs an explicit CPU-state/interprocedural contract, not merely more recognized mnemonics.

## Structural blockers and untested hazards

The following separates implementation facts from unobserved downstream effects.

- **Discovery is not authoritative code identification.** recomp.py:546–553 treats any aligned .rdata/.data word pointing into uncovered .text as a code entry. Actual seed0065006c is produced by UTF16'le' inside strings, e.g.rdata0175e080 in'Unable to write...'; it is emitted as f_0065006c (out/koa_046.c:353494). This demonstrates data-derived false admission evidence. It does not prove every one of27729seeds false. Multiple translations can overlap instruction ranges, so instruction emissions are not unique code bytes. The unsupported examples include many suspicious privileged/string-derived decodes. Treat unresolved provenance as unknown, not real engine instructions by default.

- **Indirect flow is bounded by generated entries.** rt.c:17–27 resolves only exact g_funcs addresses and exits98 on a miss. gen_table.py:6–15 creates that table from generated functions.txt, with no host import/OS callback layer. Recognized jump tables are one narrow scale4/no-base pattern; missing table metadata is guessed by scanning up to256consecutive text-looking pointers(recomp.py:622–634). Other computed jumps become dispatch at712–714. This can handle some paths, but no trace proves closure of actual vtable/callback/internal-label targets. g_dispatch_misses exists at rt.c:15 but is not incremented; its presence does not establish a measured zero-miss count.

- **RET/control transfer uses the host C call stack.** recomp.py:679–681 merely increments guest ESP and returns to the host caller; it does not read/dispatch the guest return address. This is suitable for a restricted structured-call subset, not arbitrary modified returns, nonlocal control transfer or guest exception unwinding. Direct guest call/ret-immediate/GPR stack behavior is partially represented, but Win32 cdecl/stdcall/thiscall callbacks into native host services require audited stubs. There is no universal ABI bridge.

- **SSE/MXCSR is not an x86 FP environment.** ldmxcsr/stmxcsr only assign/read a TLS integer(recomp.py:346–349). Arithmetic uses host Cfloat/double; round_d2i uses host rint(rt.h:39–40), not the modeled MXCSR. No FP environment/DAZ/FTZ/exception-status propagation is present. rcpps/rsqrtps are replaced by division/sqrt(rt.h:57–58), rather than the original instruction's approximation behavior. Actual Ghidra census records these instructions and ldmxcsr (mnemonics.tsv:157,168,213). This is demonstrably a different model; whether a particular admitted scene/clip differs is untested here. A finite normal-value matrix/decoder match would not certify all modes, NaNs, denormals or exceptions.

- **x87 is explicitly double-only.** rt.h:13,86–94 and rt.c:36–60 convert80bit values through double; FCW is stored but precision/exceptions are not generally enacted. frnd handles only a subset of explicit rounding cases. Transcendentals call host libm(recomp.py:353–357), stack tag/exception state is absent. FCW's default0x27f means it is especially wrong to infer that all ordinary operations necessarily diverge; nevertheless this is not full80bit/exponent/control-word fidelity. Original functions do contain FLDCW/FNSTCW(mnemonics.tsv:98/115). Need mode/data-dependent oracle tests, not an asserted failure of every x87 calculation.

- **Atomic/memory semantics need replacement or proof of a restricted domain.** XCHG(recomp.py:401–402) is two ordinary memory accesses. Real00928dc2 is xchg[ecx],eax, a memory atomic exchange; this translation is not an atomic RMW. LOCKXADD does use seq-cst host atomics(512–513); LOCKCMPXCHG(514–516) updates ZF/EAX but does not compute the other comparison flags. The inspected00928d87 routine immediately overwrites the relevant arithmetic flags with NEG, so that particular local use does NOT prove an observable flag failure. Other races/uses are untested. General R16/32/64 and writes are memcpy-based with no guest synchronization model(rt.h:20–33). Need real synchronization/callback/thread-state validation rather than assuming ARM memory behavior equals x86.

- **Generated C has unchecked exception/UB edges.** Narrow SHL can generate a negative host shift count for the CF calculation when masked count exceeds operand width(recomp.py:163–170). DIV/IDIV use raw host division/casts(431–440), with no guest divide-fault path. Faulting alignment, FP exceptions and guest memory exceptions are not translated into guest handlers. These are source-level semantic hazards; their reachability under valid actual engine inputs is unproven.

- **TLS/SEH/platform startup are absent in this harness.** rt.c:9 initializes FS=0; address generation only adds that integer for FS segments(recomp.py:56–67). native_test.c:51–78 copies PEsections without import resolution/TLS registration/callbacks/entrypoint initialization. The actual PE has a.tls section and a nonzero TLSdirectory; imports.json includes TlsAlloc/Get/Set/Free, CreateThread, RaiseException, exception filters and synchronization APIs, among349imports/19DLLs. cpu_t being host __thread is not a Win32TEB/TLS/SEH implementation. No guest handler dispatch or host fault/SEH bridge appears in rt.c. PE32's zero exception data-directory must not be misread as absence of x86SEH.

- **RDTSC/CPUID are policy substitutions.** recomp.py:486–491 returns a hardcoded CPUID signature/features and an ARM CNTVCT tick value without an x86 timing/frequency contract. No dependent runtime correctness or timing test was retained. Do not infer performance or engine scheduling compatibility from these substitutions.

- **Trap counters are incomplete capability descriptions.** Report148'functions with traps' counts only caught Unsupported cases(fn_unsup at726–750). Explicit INT3/UD2/HLT traps and undecodable paths are emitted separately. Static unsupported226instances/30undecodable stops can include false code and do not bound actual reachable failures. Runtime trap/dispatch exits98/99 cannot replace guest exception semantics.

## Related native work — preserve the boundary

These are separate accomplishments, not validation of the auto-translator:
- v31-native-slice/material-constants/android-result-constants.json and host-sanitized-result.json record29synthetic geometry/material-copy contract checks,64bit pointers, full_scene=false. Their manually recovered address-safe adapters are reusable for those exact contracts.
- v32-native-benchmark/CURRENT_STATE.md:5,11,24–26,65–69 explicitly describes GFXReconstruct repeating one captured graphics frame; cached modes freeze captured memory/images. It excludes simulation, live animation, culling and streaming. Replay FPS/CPU profiles cannot establish translator/full-engine speed.
- v33-native-camera/CURRENT_STATE.md:13–21 records a manually recovered matrix kernel compared with original x86 and ARM64/captured data. That is a useful differential-kernel methodology, not execution of generated rt/recomp code.
- v36 CURRENT_STATE:5–11 and v37 CURRENT_STATE:14–23 describe a few recovered geometry submission tails, copied recorded palettes and a partial packet-builder tail. Captured shaders/state still do most rendering. Recorded alternate poses are not a native animation/state producer.
- Old v37 planning FPS ranges are explicitly judgments in that note and are not admissible measured full-engine results.

## Reuse versus rework

REUSE: private original PE/source identity; read-only Ghidra range/jump exports as imperfect evidence; Capstone decoding; source addresses; pure-kernel input/output formats; reference assets; exact adapter/native-oracle receipts; compile-chunk/table infrastructure as an auditable prototype. Reuse tested helpers only within their stated input/precision/boundary contracts.

REWORK BEFORE TRUST: function-entry/CFG emission; caller-dependent architectural state including flags; memory bitstring semantics; exact admitted FP/control modes; guest atomic/exception/return behavior; guest32memory/Win32ABI/TLS/SEH/import/callback boundaries and real engine initialization. Some existing emitters may survive after differential tests; this audit does not justify discarding every arithmetic handler or trusting every one wholesale.

NO EVIDENCE: whole-engine boot, connected actor update stack, complete reachable indirect/import closure, real multi-thread execution equivalence, resource/lifetime correctness over transitions, native gameplay coverage or full-game performance through this translator.

## Smallest meaningful validation gates

1. **Stop known wrong-code first.** Add original-x86 differential fixtures for actual011c1340/shared-lower-tail entry and _strpbrk character-set collisions, plus call/tail-call/return cases with explicit initial/final flags/GPR/ESP and memory effects. Admit a function only when entry/edges/state match, not when it compiles. This is a proposed test, not one executed in this audit.

2. **Seal the existing intended decoder.** Retain full command/environment/build/input hashes, ARM binary exit/stdout, produced transform bytes and independent original-x86 output. Exercise the actually used source rigs/clips and required FP modes. Record dynamic translated targets/traps/import requirements. The currently missing ARMexecution receipt is the smallest immediate evidence gap; filling it would certify only the decoder closure.

3. **One connected subsystem, with no recorded-output substitution.** Choose one real actor/source-asset closure from asset parsing through changing animation state, hierarchy/association/palette production to its material/geometry command boundary. Compare original inputs, all relevant written bytes, ordered outputs and successive state against the translated path; vary time/pose/instance/input and include its actual callbacks/allocator/thread dependencies. Existing native kernel/adaptor fixtures can anchor this gate, but pre-baked palettes, frozen frame resources or synthetic call counts cannot satisfy it. Fail/trace every unknown reachable edge; don't silently stub it.

4. **Full-engine gate, separately scoped.** A documented original-code entry/startup path with platform/middleware/import/TLS/SEH/thread/ABI/resource contracts must load original assets and drive interactive progression/scene transitions with state/lifetime/save evidence and matched original behavior. Identify precisely which services are translated, rebuilt or substituted. Only after that functional closure should matched dynamic device measurements inform performance decisions; no current FPS extrapolation, staffing/time estimate or 'mostly-covered' percentage is supported here.

The strategic choice remains open, but the evidence does rule out treating the existing73971generated functions as a validated rebuild shortcut.
