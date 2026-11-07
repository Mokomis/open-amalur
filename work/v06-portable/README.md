# Opem Amalur portable script host

This is a portable C host for reconstructed Lua scripts, with a reusable library and a command-line executable. It targets Windows and Android arm64. It does not implement the game engine, render gameplay, or package an APK.

The parent workflow supplies verified Lua 5.1.5 sources, the Android NDK, and runtime modules. The original Windows x86 comparison harness remains an independent semantics reference; this host uses portable Lua code, not mapped Windows instructions.

Validated on Windows: all eight process scenarios passed, including the 71 native-verified recovered-function inputs, the five-value nil/type11 contract, and 20 embedding API checks. Expected budget and memory failures were retained as passing rejection tests, not successful script executions. Both looping xpcall error-handler paths were covered.

The Android build produced an arm64 ELF64 executable with 16 KiB load-segment alignment verified. No Android device was attached, so Android execution remains untested. This is a cross-compiled command-line script host and reusable static library; it is not yet an APK or playable game.

## Build

Set `LUA_SOURCE_DIR` to the unpacked Lua 5.1.5 root that contains `src/lua.h`. CMake checks the exact release. Lua is compiled into a separate static library; the interpreter/compiler executables are not included.

Windows example from the project root:

```powershell
cmake -S work/v06-portable -B work/v06-portable/build-windows -DLUA_SOURCE_DIR=C:/path/to/lua-5.1.5
cmake --build work/v06-portable/build-windows --config Release
```

Android arm64 example, using explicit local dependency paths:

```powershell
cmake -S work/v06-portable -B work/v06-portable/build-android -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=C:/path/to/android-ndk/build/cmake/android.toolchain.cmake -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-26 -DLUA_SOURCE_DIR=C:/path/to/lua-5.1.5
cmake --build work/v06-portable/build-android
```

The library propagates `max-page-size=16384` and `common-page-size=16384` linker options for Android consumers. Verify the resulting ELF program headers; compilation alone does not prove device execution or platform compatibility. The current Android target deliberately accepts only `arm64-v8a`.

Targets are `amalur_lua51`, `amalur_runtime`, `amalur-script`, and, by default, `amalur-runtime-api-test`. Set `AMALUR_BUILD_TESTS=OFF` to omit the API test executable. The reusable C API is in `include/amalur_runtime.h`.

## Explicit runtime directory

Provide these five files in one directory:

- `amalur_uint64.lua`
- `amalur_native_math.lua`
- `engine_binding_registry.lua`
- `amalur_engine_bindings.lua`
- `amalur_engine_handles.lua`

Each host instance owns an independent Lua state and plain global environment. The carrier is shared within that realm as `__amalur_uint64`; typed handles are available as `__amalur_handles`. The global `math` table contains only the five verified, guarded Amalur integer math functions. Other stock-Lua math functions are not silently presented as Amalur implementations.

Registry namespaces are installed through the strict provider bridge. The default provider is empty: registered engine calls fail with an explicit unimplemented-binding error. An embedding application can install real services with `amalur_runtime_set_provider`; providers receive no implicit `self`. No engine state, actor, quest or world result is fabricated.

The host retains base/string/table facilities required by recovered Lua. It removes `io`, `os`, `debug`, `package`, `coroutine`, `require`, `dofile`, `loadfile`, `load`, and `loadstring` from the script environment. This is a deliberately small execution interface, not a security boundary for hostile code.

## Execute

From the Windows build output (single-configuration generators omit `Release/`):

```powershell
work/v06-portable/build-windows/Release/amalur-script.exe --runtime-dir work/v06-portable/runtime work/v06-portable/tests/portable_contract.lua
work/v06-portable/build-windows/Release/amalur-script.exe --runtime-dir work/v06-portable/runtime work/v06-portable/tests/native_verified_real_functions.lua
work/v06-portable/build-windows/Release/amalur-runtime-api-test.exe work/v06-portable/runtime
```

The second fixture is supplied by the parent workflow, with provenance JSON linking the exact 71 inputs across 19 original game function bodies to native Windows comparisons. It is not an authored approximation of those functions.

The CLI reports typed results as JSON, including exact result count and trailing nil. Type11 userdata is reported as canonical hexadecimal; it is never coerced into a Lua double. Strings are escaped byte-by-byte. Tables/functions remain typed opaque results; the embedding API can inspect them directly.

Expected failure probes:

```powershell
work/v06-portable/build-windows/Release/amalur-script.exe --runtime-dir work/v06-portable/runtime --budget 1000 work/v06-portable/tests/budget_cannot_be_swallowed.lua
work/v06-portable/build-windows/Release/amalur-script.exe --runtime-dir work/v06-portable/runtime --budget 1000 work/v06-portable/tests/budget_xpcall_cannot_be_swallowed.lua
work/v06-portable/build-windows/Release/amalur-script.exe --runtime-dir work/v06-portable/runtime --memory-limit 2097152 work/v06-portable/tests/memory_limit.lua
```

These must return a nonzero process exit and an evaluation error. Initialization and provider installation each have their own one-million-instruction setup budget, independent of the requested per-evaluation budget, so a low-budget execution test does not accidentally test module loading or namespace installation.

## Embedding contract

Create a realm with an explicit runtime directory, instruction limit and Lua memory limit. Zero limits select one million instructions and 64 MiB. Every evaluation clears earlier stack values, resets its instruction budget, and leaves all returned values on the Lua stack with an exact count. Retain values across evaluations with ordinary Lua registry references. On failure, one original Lua error object remains on the stack; the bounded text diagnostic is a convenience and may say `non-string Lua error` for table/userdata errors.

The instruction hook counts Lua instructions. Budget-aware `pcall` and `xpcall` preserve ordinary error behavior while propagating budget exhaustion through nested protected calls. A C wrapper skips the user xpcall handler after exhaustion, because Lua 5.1 can disable hooks while handling a hook-raised error. Coroutines and hook control are unavailable to scripts. Native provider callbacks must bound their own work: the Lua hook cannot interrupt a blocking C function. The memory allocator caps Lua-managed allocations; source parsing is memory-bounded but has no instruction hook until execution. Files and source strings are trusted recovered input.

A realm is not concurrently thread-safe. Different realms own separate Lua states. Native code using `amalur_runtime_state` is trusted embedding code and must follow Lua's protected-call/allocation discipline. Successful `set_provider` leaves its input stack unchanged; failed provider installation appends an error object. The bridge validates the complete provider table before any namespace replacement.

## Validation boundary

`portable_contract.lua` checks host initialization, exact opaque handles, native math edge behavior, explicit missing services, ordinary protected-call semantics, and trailing-nil results. `amalur-runtime-api-test` checks provider arguments/results, realm separation, original non-string errors, low-budget initialization, budget propagation, memory limits, error-handler loops after hook exhaustion, and recovery after both failure classes.

Successful Windows execution and Android cross-compilation are separate milestones. Android execution requires running the built arm64 executable on an attached compatible device. None of these tests establish graphics, audio, controls, save compatibility, all engine bindings, or a playable Android game.
