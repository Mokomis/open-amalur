# koa.exe rebuild tool audit — qualified shortlist

No inspected toolkit is ready to turn this complete game into a native ARM64 Android engine while preserving its Windows behavior. A staged whole-engine qualification is defensible; treating tool support lists or generated C/C++ as a completed port is not.

The useful sequence is:
1. Conditionally qualify pcrecomp native32 as a Windows x86 reference host that imports real Windows/D3D11 services, with all guest engine code remaining lifted.
2. Independently qualify the portable CPU/runtime route, considering SwARc first as an integrated scaffold and Remill as an instruction-semantics foundation. An Android service/API layer is a separate required deliverable.
3. Keep a target-specific admission ledger; no backend is admitted merely because it emits or compiles source. Reject unresolved instructions, missing indirect targets, accidental native engine fallbacks and silently ignored state.

This is read-only source/documentation assessment. No toolkit was installed, built or run; no game was launched; no original database or project file was changed. Five exact commits and selected primary-source files are retained as audit evidence outside the project. No speed, completion date, playability or performance promise is made.

## Target-specific facts

Read-only PE parsing reverified koa.exe SHA16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314, PE32 machine0x14c/x86. The supplied target identity is cs15032. Detailed imports/sections/directories are koa-target-imports-and-PE.json.

The main image contains a1088-byte staticTLS template (VA01a0e000..01a0e440), index VA01a0be1c, an empty TLS callback list, and3SafeSEH table entries (tableVA017b2c30). Empty callbacks do not remove the staticTLS requirement. SafeSEH presence does not prove which exception path runs, but makes ignoring exception compatibility unjustified.

There are19statically imported DLLs, including D3D11CreateDevice, D3DCOMPILER_43, Steam, Bink, Winsock, LDAP, crypto, COM/OLE, input and Win32. Static imports are a lower bound: LoadLibrary/GetProcAddress, callbacks, COM/vtables and dependentDLL imports require separate coverage. Original captured shader evidence already establishes D3D11/SM5 use; oldDirectX HLE is not equivalent. A saved512-byte disassembly sample of native00ce93e0 containsMOVSS atVA00ce940f; this is a real instruction gap for the inspected SR cross-port backends. It is not a whole-image opcode inventory.

## Candidates and rejections

### pcrecomp: Windows reference candidate, conditional

Pin2adc02fec0702933325801aa7b29a7646321857f (verified2026-11-06).

native32.h2–29 describes a32-bit Windows host with real importedAPI/COM calls, guest code pages non-executable and lifted callback dispatch. native32.c15–16 explicitly refuses any build other than MSVCx86. This is a useful Windows qualification path, not ARM portable runtime proof. The optional hybrid layer contains x86 inlineassembly and allows deliberately mixed execution; do not use that to disguise unrecompiled engine code.

A concrete target gap is staticTLS: native32.c80–88's simulated TIB does not initialize ThreadLocalStoragePointer atTEB+0x2c; reviewed loader code has no main-image staticTLS template setup. This must be implemented or proven irrelevant by actual reachable-code evidence before admitting koa. TlsAlloc API support is not sufficient.

native32/eh32.c supports an MSVC C++ frame model, but lines36–38 expressly skip SEH filters/finally frames during C++ unwind. That is not general target SEH proof. Its source comments report other-game use; those reports are author claims, not this audit testing this executable.

The separate off-Windows win32hle is based onPOSIX/SDL2. Its README114–116 explicitly omits guestSEH/C++ exceptions and DirectX newer than6. Its claimed based-memory ARM64 design therefore does not make it an Android/D3D11 solution.

SSE has scalar/packed C lane lowering. The global backend's recomp_types.h900–904 states FTZ/DAZ are not modelled and exceptions stay masked; reciprocal/rsqrt lowering uses1/x or1/sqrt. lift32_sse.py292 can emit a counted UNIMPLEMENTED no-op comment. The CPU-struct emitter has a different aborting RECOMP_TODO mechanism. Qualify the chosen generator/runtime pair, reject every unknown form, and test target FP behavior rather than assuming the variants are identical.

Primary code:
- https://github.com/sp00nznet/pcrecomp/blob/2adc02fec0702933325801aa7b29a7646321857f/runtime/native32/native32.c#L15
- https://github.com/sp00nznet/pcrecomp/blob/2adc02fec0702933325801aa7b29a7646321857f/runtime/native32/native32.h#L2
- https://github.com/sp00nznet/pcrecomp/blob/2adc02fec0702933325801aa7b29a7646321857f/runtime/native32/eh32.c#L36
- https://github.com/sp00nznet/pcrecomp/blob/2adc02fec0702933325801aa7b29a7646321857f/runtime/win32hle/README.md#L114
- https://github.com/sp00nznet/pcrecomp/blob/2adc02fec0702933325801aa7b29a7646321857f/tools/lift/lift32_sse.py#L292

### SwARc: portable CPU/runtime scaffold candidate, conditional

Pin30bd2ad14bf3b0316178fc152ca6621c67ab2fce.

The PE32/x86 lifter and4GiB guest arena, per-function C++20, CPU state, dispatch, x87/SSE, Win32HLE and callback/thread machinery are unusually relevant. Unknown indirect targets are fatal and require code/manifest recovery; there is no decoder safety net. That improves visibility but does not establish function/target completeness for koa.

Do not recommend stockSwARc as a native Windows-host build. README requirements are Linuxx86-64 or macOSAppleSilicon. platform.cpp13–41 depends onPOSIX ucontext; CMake uses GNU/Clang/ELF-style options. ReadFaultContext48–71 has Linuxx86-64 and AppleARM64 cases, but no Linux/AndroidARM64 context extraction. Concrete AppleARM64 branches make its portability more substantial than a plain-C assertion, but no Android build, Windows-host build or ARM game run was verified.

Its current graphics layer lists D3D7/D3D9 and SM1–3 translation, not the target D3D11/SM5 API. Replacing this boundary requires real guest32/native64 COM/API/resource/shader handling or explicitly rebuilt higher-level renderer boundaries, not merely selecting Vulkan.

Main EXE staticTLS is implemented in process.cpp58–98; callbacks are rejected and32-bit lifted-DLL staticTLS is rejected. The target main-image empty callback list fits that narrow condition; dependent module coverage remains unknown.

SSE code is stronger than host float substitution but is not unrestricted bit parity: sse.cpp88–106 fails on DAZ-denormals, FTZ-tiny results and unmasked SIMD exceptions. Tests intentionally mask exceptions and turn FTZ/DAZ off. RsqrtLane337–372 correctly rounds1/sqrt, which need not reproduce a particular x86 CPU's approximateRSQRT bit pattern. That is a qualification issue, not proof of a bug in this target. Exact target MXCSR paths/approximations have not been measured here.

Primary code:
- https://github.com/JTM-rootstorm/SwARc/blob/30bd2ad14bf3b0316178fc152ca6621c67ab2fce/README.md
- https://github.com/JTM-rootstorm/SwARc/blob/30bd2ad14bf3b0316178fc152ca6621c67ab2fce/src/runtime/platform.cpp#L13
- https://github.com/JTM-rootstorm/SwARc/blob/30bd2ad14bf3b0316178fc152ca6621c67ab2fce/platforms/win32/src/win32/process.cpp#L58
- https://github.com/JTM-rootstorm/SwARc/blob/30bd2ad14bf3b0316178fc152ca6621c67ab2fce/src/x86/sse.cpp#L88
- https://github.com/JTM-rootstorm/SwARc/blob/30bd2ad14bf3b0316178fc152ca6621c67ab2fce/platforms/win32/src/win32/kernel32_seh.cpp#L133

### Remill /McSema: separate them

Remill pin56918a8c2554088e93389e97d292f4035286506c is an instruction-lifting library, not aWindows game runtime. Its x86/SSE/AVX semantics and differential tests make it relevant for function-level proof or a custom lifter/runtime. AArch64 in its architecture list describes an INPUT ISA. LLVM can targetARM, but guest pointers, state, imports, indirect calls, exceptions and platform services still require implementation.

The current workflow defines UbuntuARM64/macOS runners. That is concrete test configuration; successful runs or aWindows-x86→Android game result were not collected. READMEWindows support is experimental. CurrentRemill should not be evaluated solely through oldMcSema's documentation.

McSema pin26368053f761be05dab708bc28fb97090c64b2be is archived since2022. Its limitations document explicitly leaves exception handling to something else and distinguishes tool-host platform from input format. The archived x86 runtime actually emits nativeCPUID/RDTSC/RDTSCP assembly. This is not an ARM64 runtime by retargetingLLVM. Treat it as historical CFG/runtime material, not the ready whole-engine choice.

Primary code/docs:
- https://github.com/lifting-bits/remill/blob/56918a8c2554088e93389e97d292f4035286506c/README.md
- https://github.com/lifting-bits/remill/blob/56918a8c2554088e93389e97d292f4035286506c/docs/DESIGN.md
- https://github.com/lifting-bits/remill/blob/56918a8c2554088e93389e97d292f4035286506c/.github/workflows/build.yml#L97
- https://github.com/lifting-bits/remill/blob/56918a8c2554088e93389e97d292f4035286506c/lib/Arch/X86/Semantics/SSE.cpp
- https://github.com/lifting-bits/mcsema/blob/26368053f761be05dab708bc28fb97090c64b2be/docs/Limitations.md
- https://github.com/lifting-bits/mcsema/blob/26368053f761be05dab708bc28fb97090c64b2be/mcsema/Arch/X86/Runtime/Runtime.cpp#L91
- https://github.com/lifting-bits/mcsema/blob/26368053f761be05dab708bc28fb97090c64b2be/mcsema/Arch/X86/Runtime/print_PE_32_windows.cpp

### M-HT/SR: genuine precedent, wrong cross-port backend for koa

Pinac690ddf3010bc3d2c875cb1b5e8da4f53a8d5b3.

SR isDOS; SRW isWindows plus title-specific information; llasm can feedLLVM. Supported legacy-game ports and advertisedARM64 hosts are credible precedents, not transferableD3D11 support.

The actual ARM and Windows-llasm switches do not handleMOVSS/MOVAPS/MOVUPS/ADDPS/MULPS/SHUFPS/UCOMISS/LDMXCSR/STMXCSR, and their default branches return error5. koa's inspected code containsMOVSS. This is enough to reject the existing cross-port path for thisSSE-heavy target. It does not prove the x86/x64 output path cannot retainSSE instructions; that route would still not solveAndroid or theAPI layer.

N64Recomp and Xenon tools remain architectural precedents, not compatible translators for this PE32x86 input.

Primary code:
- https://github.com/M-HT/SR/blob/ac690ddf3010bc3d2c875cb1b5e8da4f53a8d5b3/README.md
- https://github.com/M-HT/SR/blob/ac690ddf3010bc3d2c875cb1b5e8da4f53a8d5b3/SRW/README.md
- https://github.com/M-HT/SR/blob/ac690ddf3010bc3d2c875cb1b5e8da4f53a8d5b3/SR/SR_full_arm_instr.c#L8556
- https://github.com/M-HT/SR/blob/ac690ddf3010bc3d2c875cb1b5e8da4f53a8d5b3/SRW/SR_full_llasm_instr.c#L7749

## Required qualification gates before any implementation claim

- Reconcile function/basic-block and indirect-call/jump coverage against existing recovered symbols and target bytes. Include data-held vtables/callbacks, tailcalls, exception continuations, DLL and generated-code behavior. Report unresolved targets explicitly.
- Match every reachable encoding against the exact selected emitter/runtime. No compiled no-op UNIMPLEMENTED, missing hypercall, placeholder return or hidden interpretation/native-engine fallback.
- Validate target Windows staticTLS/per-thread state, SEH/C++ unwinding and non-local exits. Test the actual calling conventions, callbacks, COM object/vtable layouts, varargs and error/lifetime rules at the external boundary.
- Differentially test representative SSE/x87/FP behavior, MXCSR modes, approximation-sensitive math and save/load data. Test thread memory ordering/atomics and numerical divergence on realARM64 before claiming equivalent execution.
- Inventory the actual imported and dynamically resolved API/DLL surface. D3D11/SM5, resource formats, shader translation, input/audio/movie, COM, network/platform services are separate from CPU lifting. Existing recovered rendering contracts help implementation but do not constitute a completeD3D11 runtime.
- Establish reproducible Windows reference execution first, preserving read-only original inputs and user state. Then independently admit nativeARM64 Android host/runtime and complete scenes/gameplay. A toolselftest, compiling generated source or a rendered test frame is not whole-engine parity.

No compatibility gate above was executed against koa in this audit. The result is a source-backed shortlist and rejection ledger, not a completed feasibility proof.
