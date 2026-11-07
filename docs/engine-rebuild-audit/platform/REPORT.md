# Original-engine platform audit — 2026-11-06

Scope: read-only inspection of the installed original executable, preserved PE/cached decompiler exports, our x86 graphics source, historical recordings and one existing crash minidump. No game launch, build, installation, registry/configuration/save/key change, new analysis database, or target execution. Only new audit notes were written in this directory. Paths below are absolute or relative to `C:\Users\rwill\Documents\Opem Amalur` (P). No full-game performance prediction is made.

## Decision supported by current evidence

The actual installed game is still the original x86 PE32 engine. It is NOT currently a rebuilt ARM64 engine. The preserved x86 snapshot is identical to it. Existing generated-C compilation, native animation/matrix slices, and ARM captured-frame rendering establish narrower capabilities; none establishes a complete engine executable with its dependencies, guest ABI, callbacks, exceptions, live game state and I/O working on ARM64.

An original-behavior-preserving Windows x86 intermediate has concrete support: the existing proxy forwards device creation and COM calls to the real Windows D3D11 implementation while bounded functions can be replaced under byte guards. This is a viable incremental validation boundary, NOT evidence that all engine code has been rebuilt. An ARM64 continuation requires a defined 32-bit guest-memory and call boundary and an executable dependency strategy. It does NOT require writing every Windows API ourselves. Reusing Wine/WoW64 or an existing compatible runtime is a candidate; integration of OUR generated C with that runtime remains unproven.

## Verified executable and dependencies

Installed file: `C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe`.

- 23,741,952 bytes; SHA256 `16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314`.
- Byte-identical to P\work\v30-engine\koa.exe.
- Machine 0x014c (x86), optional-header magic 0x010b (PE32), linker header 10.0, image base 0x00400000, entry VA 0x011ca33e. File characteristics 0x0122 include large-address-aware; DLL characteristics 0x8140 include dynamic base and NX compatibility. These header flags are not a runtime exploit/security assessment.
- 349 static symbol/ordinal imports from 19 DLLs. After normalizing `ord3` versus `#3` notation the current parse exactly matches P\work\v30-engine\imports.json. No executable delay-import or CLR directory. No MSVCR DLL static import in koa.exe.
- TLS directory: initialized VA range 0x01a0e000..0x01a0e440 = 1088 bytes, index VA 0x01a0be1c, no TLS callbacks in its callback array. Dynamic thread/FLS initialization still exists; empty callback array does not mean no TLS.
- Load-config Size=72, cookie VA 0x0197713c, SEHandlerTable VA 0x017b2c30, count=3. Data-directory declared extent is 64, while the file-backed structure Size is 72; table presence is verified, loader acceptance of that discrepancy was not independently tested. Do not infer all exception semantics from these headers.

Direct modules: SHELL32, KERNEL32, XINPUT1_3, USER32, WINMM, SHLWAPI, ole32, D3DCOMPILER_43, dbghelp, DINPUT8, OLEAUT32, ADVAPI32, WS2_32, steam_api, binkw32, d3d11, WLDAP32, CRYPT32, Normaliz.

Current ordinal resolution was read from SysWOW64 exports without loading modules: XINPUT ordinal2=GetState,3=SetState; OLEAUT ordinal2=SysAllocString,6=SysFreeString. Full socket and LDAP ordinal names are in system-ordinal-name-resolution.json. This is the current installed Windows export mapping, not a claim that ordinal-only imports are architecture-independent.

| Installed bundled DLL | Bytes | Machine | SHA256 | Static dependency implication |
|---|---:|---|---|---|
| binkw32.dll | 198144 | x86/PE32 | 36810b3318acd07a5b4e78fe72db163ed63880ab2eb2d9b5bda0331ded32a9c3 | USER32,KERNEL32,WINMM,ole32; original game imports 25 decorated Bink APIs |
| steam_api.dll | 227616 | x86/PE32 | d99d425793f588fbc15f91c7765977cdd642b477be01dac41c0388ab6a5d492d | KERNEL32,ADVAPI32,SHELL32; original imports 10 Steam entrypoints |
| libeay32.dll | 1097216 | x86/PE32 | 3dc13114435872a72a26b16e67c3cda764d44aa20a44105835e28a4ea6021679 | WS2_32,GDI32,ADVAPI32,USER32,MSVCR90,KERNEL32 |
| ssleay32.dll | 237056 | x86/PE32 | e05800580e4f8bba4c965734d1231f0b80897f826326c52bbdce41d81c452c3c | LIBEAY32,MSVCR90,KERNEL32 |

The OpenSSL DLLs are physically present and form the dependency chain above; they are NOT direct imports of koa.exe and NOT present in the inspected historical minidump. This audit does not establish their runtime activation path. P\work\v30-engine\run-vk also contains DLL copies; filenames alone do not establish equality with installed files. In particular use the installed ssleay size/hash above.

`static-file-dependency-closure.json` recursively parses literal files reachable from the executable plus all four bundled candidates using game-root/SysWOW64 lookup: 33 files, 177 unresolved literal names, predominantly API-set contracts plus MSVCR90. This is intentionally NOT mislabeled a complete Windows loader closure: API-set namespace mapping, WinSxS activation, export forwarders, COM activation and arbitrary dynamic libraries are not resolved by a filename walk. Missing literal API-set DLLs do not mean Windows is broken. The observed run works through OS loader/runtime services; an ARM strategy must preserve equivalent resolution.

## Dynamic load evidence and its limits

`cached-dynamic-loader-sites.json` preserves exact file/line/function evidence from existing decompiler exports. Its 84 selected lines include 10 explicit LoadLibrary-family lines and 68 GetProcAddress lines, plus selected TLS/unwind sites. Parameter-based loaders and indirect calls make this a lower-bound static catalogue, not a complete possible-load list.

- P\work\v30-engine\decomp\misc.c:17487–17545 (`__mtinit`, 0x011d27e8): resolves FlsAlloc/GetValue/SetValue/Free from KERNEL32, falls back to TLS, allocates per-thread CRT data and uses encoded function pointers. The export identifies this function as VS2010 Release library match; linker10.0 and static CRT imports support that identification, not an exact source/build configuration for every object.
- misc.c:22931–22938: ADVAPI32/SystemFunction036 in rand_s; 36788–36796: late USER32/message-box helpers. misc.c:5322 creates the CRT thread through `__beginthreadex`/`__threadstartex_4`.
- decomp\unnamed_011a.c:7607–7628: COM initialization, LoadLibraryExW(XAudio2_7.DLL,0,0x800), CoCreateInstance and audio-device error path in keen sound. Audio is not closed by static imports alone.
- decomp\unnamed_00a6.c:563–666 (`00a652e0`): obtains already loaded steam_api and resolves THQNO_Wrapper_* platform/audio/overlay functions. The current installed steam_api export table contains NO THQNO_Wrapper export. This is an optional/candidate branch in the image, not proof those wrapper services execute or must all be implemented for this Steam build.
- decomp\unnamed_009f.c:5091–5146 (`009f69e0`): parameter-based module loading with LoadLibraryExA/AddDllDirectory/system-directory fallback. decomp\unnamed_010a.c:395–397 is another parameter-based LoadLibraryA/GetProcAddress bridge. Their call arguments are not exhaustively resolved here.
- decomp\unnamed_009e.c:5584 resolves InitSecurityInterfaceA; installed image contains secur32/security DLL strings. No live network use is inferred.
- decomp\unnamed_00a8.c:2572–2595: candidate VTune/CAProf profiler DLLs, each guarded by successful load; these are not demonstrated mandatory shipping dependencies.
- Our Vulkan layer, vk\oa_vk.c:2119–2144, loads vulkan-1.dll and resolves vkGetInstanceProcAddr. This is our replacement backend, not the original executable's static import list.

Observed historical modules: `historical-run-vk-minidump-modules.json` parses the existing P\work\v30-engine\run-vk\koa.dmp MODULE_LIST stream: 119 loaded modules, artifact SHA256 b05207bfd16d71e3d4b88f4ab7add1ede71e48ddce71f7ca71b6f45dfd0b2804. Includes original x86 engine, Bink, Steam API; Steam client/tier0/vstdlib/Steam/CSERHelper; XAudio2_7/8/9, Vulkan loader and NVIDIA driver components. Steam overlays and RTSS layers are observed injected/instrumentation components, not established engine requirements. Presence of three XAudio DLLs does not prove the engine directly calls each. This is one historical crash-state inventory, not a new run or complete all-scenes coverage; it does not provide a full LoadLibrary chronology or every GetProcAddress invocation.

## ABI, platform services and preservation requirements

These are mandatory CONTRACT boundaries; existing runtime libraries may supply them.

1. Guest32 object/data layout: source carries x86 pointer-sized fields, COM vtables, packed offsets, 32-bit registers/stack addresses and asset fixups. Native ARM64 host pointers cannot simply be substituted into those fields. P\work\v30-engine\recomp\rt.h:1,11–33 explicitly uses a 32-bit guest CPU and casts guest addresses to host addresses in low4GiB. Every allocation/mapped object exposed to that model must remain addressable, or use an explicit translated address space. Native host handles/COM pointers need indirection if they cannot fit; a cast is not a bridge.
2. Calls/callbacks: preserve cdecl/stdcall/thiscall/custom register inputs, stack cleanup, return/FP values, function pointers, vtable dispatch, allocator callbacks, thread start and COM callbacks. Current `rt.c:17–33` only looks up translated function addresses; misses terminate. It does not implement imports, native callbacks, DLL dispatch or exception transfer. `recomp.py:694–714` routes translated calls/jumps through that lookup. Compiling generated chunks does not supply these missing boundaries.
3. CRT/TLS/SEH: preserve per-thread CRT state/FLS destructors, x86 FS/TEB-linked state where referenced, exception/unwind and C++ object cleanup, cookie behavior/assumptions and thread lifecycle. KERNEL32 imports include TLS, RtlUnwind, RaiseException, exception filters and thread APIs. Native ARM unwind metadata differs from x86 guest SEH; neither PE header copying nor C `__thread` alone proves compatibility.
4. Threading/I/O: atomics and memory ordering, critical sections/events/semaphores/affinity, file mapping/heap/VirtualAlloc protection, Win32 completion ports/async completion, waits/timeouts and directory changes. Preserve blocking and callback-thread ownership; do not replace completion with success/no-op. Exact imports are machine-readable in pe-identities-and-imports.json. Recompiler `recomp.py:512–516` has bounded lock-xadd/cmpxchg translations but this is not an audited whole-program concurrency model.
5. Platform/UI/input: A/W strings/codepages/locale, raw input/DirectInput/XInput, keyboard layouts, window/message pump, cursor capture, clipboard, COM/OLE, paths and original asset search/streaming semantics. On native Windows some can remain native APIs. On Android they need compatible runtime service mapping or selected replacements, not necessarily a bespoke rewrite.
6. Numerical behavior: original SSE/x87, rounding/NaNs, control state and evaluation order must be checked where behavior depends on it. `rt.h:13–15` and `rt.c:36–44` model x87 state using double and decode80→double, not full extended-precision equivalence. The recovered matrix function's actual double intermediates were hidden by pseudocode: P\work\v33-native-camera\CURRENT_STATE.md:11–21 documents exact comparison for 4221 pairs. That is strong evidence for one kernel, not all floating-point code.

Middleware disposition:

- Bink: current mandatory static x86 interface includes decorated stdcall video decode/frame timing, async worker lifecycle, file/memory callbacks and XAudio2 binding. A native ARM process cannot directly use these x86 instruction bodies without an architecture bridge/emulation island. Options are a compatible native implementation/SDK, a thoroughly specified replacement, or preserved guest execution. No available ARM Bink build/license or complete replacement was verified. Dropping movies/audio/asynchronous behavior is not behavior preservation.
- Steam: current x86 Steam API plus dynamically observed client chain needs a consistent ABI/platform strategy. Native SDK availability, compatible service replacement and guest middleware hosting are candidates requiring confirmation; simply retaining x86 DLL filenames in an ARM native process is not sufficient. Preserve callback registration/dispatch, interface versions and actual entitlement/save/achievement behavior where used; this audit does not authorize bypassing authentication or inferring DLC ownership. Indirect Steam interfaces mean 10 static entrypoints do not bound its full surface.
- D3DCompiler_43: original statically requires D3DReflect. `decomp\unnamed_00c5.c:1322–1368` (00c589d0) reflects BOTH fragment and vertex blobs and extracts material bindings; `unnamed_0106.c:1126–1145` separately creates a VS and queries its input signature through reflection COM methods. Our SPIR-V translator does NOT implement the D3DReflect export/reflection COM ABI. An ARM route must retain it through a compatible runtime/bridge or implement the exact consumed reflection contract, including types, names, layouts, signatures and lifetimes. Recorded shaders do not make this runtime material-binding service disappear.
- OpenSSL/networking: available x86 DLLs and static Windows socket/LDAP/certificate/IDN APIs are unresolved scope, not safe removals on a 'single player' assumption. Their callers/activation must be established before excluding them.
- Bullet/Lua/FaceFX/keen sound: installed image source-bound strings and cached RTTI substantiate these components (middleware-identification-strings.json); v30 PLAN.md:15 records version identifications but not complete compilable source equivalence. Open-source Bullet/Lua releases cannot be substituted solely by name: engine-specific ABI, serialization/math and Lua host bindings matter. FaceFX/keen sound behavior needs preserved implementation or explicit covered replacement. No all-components ARM implementation is demonstrated.

## Our graphics layer: portability versus coverage

Current P\work\v30-engine\vk\d3d11.dll is x86/PE32, SHA256 64173034872f749412382f10027325c522f1a6aff0b71334e052ab794f3afe7a. Current proxy DLL is x86/PE32 SHA256 6302717382713001a26ceea246cd202a0803cb775f2e9e8d88ba438b65e69884. Both static-import KERNEL32 and static-link their C runtime. vk\build.cmd selects vcvars32, /MT, /LD; oa_vk.def uses x86 `_D3D11CreateDevice@40`/`...AndSwapChain@48` aliases.

Concrete port work, not a reason to discard the backend:

- `vk\oa_vk.c:264–284` generates x86 push/call/mov-eax/ret-N bytes for unimplemented vtable methods; :2072 allocates RWX storage. Those thunks must be regenerated/replaced for a native ARM host OR remain in a guest x86 interface. Their presence does NOT mean Vulkan rendering itself cannot be ported.
- :17 uses stdcall COM; :874–876 reads a D3D input element as seven32-bit words and converts the first32-bit semantic-name pointer directly to a host pointer. :2038 writes HWND as u32 into the swapchain descriptor. :2312–2316 reads Eip/Esp and x86 stacks. These are explicit guest ABI assumptions, not hidden portable C.
- :2119–2144/:1931 uses Windows DLL lookup and Win32 surface creation. An Android-native host needs a surface/lifecycle adapter; Windows ARM can retain a native Win32 surface route with a coherent ABI.
- :2139/:2167–2185 requires Vulkan1.3 dynamic rendering and requests BC, anisotropy, depth clamp/bias clamp, independent/dual-source blend, non-solid fill and robust buffer access. Real device feature availability/format behavior must be negotiated, not assumed from one desktop/tablet recording.
- `oa_dxbc.c:1–6` depends only on our header and standard C allocation/string/stdio/varargs; no D3DCompiler or Vulkan-loader library is linked into the translator itself. This is a promising portable component, NOT a completed ARM compatibility proof. :943 rejects all shader types except PS/VS; :911 rejects unsupported SM4 opcodes. `oa_dxbc.h` fixes signature32, CB16, sampler16, texture32; runtime reflection needs additional functionality as above.

Coverage classification, generated directly from current source and preserved recordings in recorded-d3d-coverage.json:

| Surface | Current explicit slot overrides | Remaining generated fallback slots |
|---|---:|---:|
| ID3D11Device | 27/43 | 16 |
| ID3D11DeviceContext | 34/115 | 81 |

These counts include IUnknown overrides; overrides are IMPLEMENTATION PRESENCE, not complete/correct contracts. Across20 preserved scene stats files the same48 methods (19device/29context) have overrides. This is meaningful evidence for that path. The separate oa_rec-title-native/stats.txt records56 fallback context methods once each. No recorded arguments establish null/default resets vs meaningful geometry/compute/UAV work; classify these as OBSERVED CALLS WITH UNRESOLVED SEMANTICS, not harmless unused fallback or proof advanced shader stages are needed. SwapChain slot15 fallback is independently observed at run-vk/oa_vk.log:13. Other unobserved slots remain unsupported, not proven unnecessary.

Unimplemented device slots include CreateTexture1D/UAV/GS/GS-with-SO/HS/DS/CS/ClassLinkage/Counter/OpenSharedResource and feature/counter queries. Context fallbacks include GetData, command-list operations, CopyResource, UpdateSubresource, GenerateMips, instanced/indirect/dispatch and many getters. See the exact generated table rather than extrapolating from names.

Implemented-but-bounded behaviors: `oa_vk.c:974–989` reports broad hardcoded format support, single-sample MSAA only, fixedfeaturelevel and creates a deferred context; :1695 drops deferred draws and FinishCommandList/ExecuteCommandList remain fallback. :1355–1386 ignores Map flags and maps existing CPU copies, not general GPU readback; :1346–1350/:1784–1805 use delayed/periodically sampled occlusion results. :2041–2054 fullscreen/resize-target calls are success no-ops. These are concrete semantic restrictions to close or positively bound; 'method implemented' alone is not parity.

Shader evidence: current inventory using the exact test_all.py glob/dedup policy is510 distinct filenames AND510 distinct SHA256s (current-recorded-shader-corpus.json). PLAN.md:62 says all510 passed spirv-val. This audit did NOT rerun a build/validator or assert arbitrary/new runtime shader coverage. Validation establishes structurally valid SPIR-V for that corpus, not D3D numerical/pixel parity, every engine shader variant, or future shader types. create_shader at oa_vk.c:885–904 fails on translator/module failure; it has no generic fallback compiler.

## Windows intermediate and ARM runtime reuse

Existing x86 Windows forward-import boundary is concrete: `proxy\oa_d3d11.c:350–386` selects OA_REAL_D3D11 or systemD3D11, loads it, resolves the two create exports, calls real creation and hooks returned real COM objects. :62–74 emits x86 counting thunks forwarding to ORIGINAL methods. `proxy\oa_engine.c:525–550` checks expected original bytes at ASLR-adjusted addresses before a5-byte x86 JMP replacement. Same-process x86 code shares real object layouts and supports original-code A/B. Mixing a real-D3D COM resource with an unrelated Vulkan-owned fake object without full wrapping is not supported by this mechanism.

For generated-C Windows x86 testing, preserving32-bit memory and real Win32 imports is a sensible inference, but the existing recompiler still needs import/callback/dispatch integration; compile_all's successful chunk compilation is NOT a fully linked loader/engine. `recomp\translate-report.txt` itself reports417 dynamic jumps,148functions with traps and30undecodable stops. Its suspicious unsupported-instruction examples may contain code/data misidentification; those counts are generator diagnostics, not a verified count of real unreachable or faulty engine functions. They prevent claiming complete translation.

External primary-source check (read2026-11-06): [Hangover official README](https://github.com/AndreRH/hangover#how-it-works) describes x86_32/x86_64 applications on aarch64 Wine using emulator DLLs and WineWoW64, executing Windows/Wine system calls outside emulation. Current HODLL options include libwow64fex and wowbox64. This proves a runtime-reuse ARCHITECTURE exists. It does not prove our generated C can be registered as such an emulator, marshal guest callbacks/exceptions/COM, or run koa fully; that integration is a separate gate. Reusing Wine native APIs and keeping selected x86 middleware under an established emulation boundary is a candidate distinct from rebuilding every DLL. ARM64EC's documented64-bit route is not automatically an x86PE32-to-C solution.

## Full-game gates and bounded unknowns

To honestly call this an original-engine rebuild for Windows and ARM after changes, require:

1. A complete engine code/indirect-dispatch boundary: implemented imports and callbacks, resolved real reachable traps/jumps and correct loader/data relocations. Decompiler export and chunk compilation alone fail this gate.
2. A chosen executable memory/ABI model, tested across worker/audio/render threads, TLS/FLS, exceptions/unwind and middleware callbacks. Native pointer widths must not silently alter source objects or truncate host resources.
3. Explicit middleware disposition for Bink, Steam/client interfaces, D3DReflect, audio/FaceFX, and any activated networking. Native compatible code OR a proven guest bridge/runtime can satisfy the contract; no blanket need to rewrite all Windows, and no blanket permission for no-op replacements.
4. Real backend parity for original scene/menu/movie/streaming/device transitions, query/readback/deferred paths actually used, complete selected runtime shader/reflection corpus and correct format/mip/sampler/state semantics. Current48-method path and510shader corpus are bounded witnesses.
5. Preservation of original world/AI/combat/quest/Lua/inventory/cinematic/save/load/threaded streaming behavior through original-code comparisons. A static captured frame or one animation/matrix slice cannot substitute for those live systems.

Unresolved by this bounded read-only audit: all possible dynamic DLLs/COM classes/interface versions; active OpenSSL path; complete import forwarder/API-set/SxS closure; native ARM middleware availability/license; generated-C→Wine integration; all indirect branches, precise x86 FP/SEH equivalence and all-scene shader/API use. No current evidence justifies asserting full-game completion or projected FPS.

## Evidence files

- pe-identities-and-imports.json — installed/snapshot identity, PE fields, direct imports/exports and TLS/load-config.
- static-file-dependency-closure.json — recursive literal static-file scope and unresolved loader mappings.
- system-ordinal-name-resolution.json — current x86OS ordinal names and DLL hashes.
- cached-dynamic-loader-sites.json — cached source loader/FLS/unwind sites with function addresses/lines.
- historical-run-vk-minidump-modules.json —119historically observed modules; contains paths, not memory contents.
- middleware-identification-strings.json — source file offsets and identification strings.
- d3dreflect-sites.json — exact reflection source locations.
- recorded-d3d-coverage.json —21statsfiles and method-presence comparison, with hashes.
- current-recorded-shader-corpus.json —510existing blobs/hashes; no shader outputs changed.
- source-pins.json — audited source/notes hashes. Original files remain unchanged by this audit.
