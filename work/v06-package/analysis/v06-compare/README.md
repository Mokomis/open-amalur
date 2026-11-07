# Original native VM comparison harness

This Windows x86 test harness executes the installed game's original interpreter and selected math callbacks, then compares exact returned values with reconstructed Lua 5.1. It is a validation oracle for a portable implementation. It is not an Android runtime, game launcher, or complete engine replacement.

The coordinated Windows run reported these passing families. Each `comparison.json` records its exact harness, target, fixtures, reconstruction source and profile hashes; use those records when combining results from different builds.

| Family | Cases passed | What executes as original x86 code |
| --- | ---: | --- |
| Synthetic primitive VM | 364 / 364 | Arithmetic, int32 wrap behavior, comparisons, truth branches, counted loops, returns |
| Selected real function bodies | 71 / 71, across 19 bodies | Exact selected game bytecode/constants, restricted primitive inputs |
| Native math callbacks | 319 / 319 | `abs`, `sqrt`, `pow`, `min`, `max` |
| C-call boundaries | 63 / 63 | CALL/TAILCALL and cached dispatch, C-frame setup, fixed/open result movement |
| Seeded Lua calls | 55 / 55 | Lua frame setup, nested RETURN, missing/extra arguments, cached CALL and mixed Lua/C boundaries |

Total: 872 admitted comparisons. Smoke cases are not additional unique coverage. All five families were rechecked against the final seeded-Lua-capable harness (SHA256 prefix `e2e0f14`). No excluded or domain-rejected input counts as a pass.

## Build on Windows

Prerequisites are the existing project source and native profile, Python 3.11 or later, Lupa's Lua 5.1 module in `tools/python-libs`, and the installed MSVC x86 toolchain configured by `build_native_vm.cmd`.

From PowerShell:

```powershell
Set-Location 'C:\Users\rwill\Documents\Opem Amalur'
& '.\work\v06-compare\build_native_vm.cmd'
if ($LASTEXITCODE -ne 0) { throw 'Native harness build failed; inspect build.log' }
```

The build script selects `vcvars32.bat`, uses `/MT`, and links `bcrypt.lib`. Logs are beside the harness source. The harness requires a 32-bit process; a 64-bit build is rejected.

## Run comparisons

Use a new output directory for every invocation. The runners refuse to overwrite an existing directory. The following examples use the existing Windows `python` command.

```powershell
python work/v06-compare/compare_native_vm.py --smoke --output outputs/engine-bindings-v06/recheck-primitive-smoke
python work/v06-compare/compare_native_vm.py --output outputs/engine-bindings-v06/recheck-primitives
python work/v06-compare/compare_native_math.py --output outputs/engine-bindings-v06/recheck-math
python work/v06-compare/compare_native_calls.py --smoke --output outputs/engine-bindings-v06/recheck-c-call-smoke
python work/v06-compare/compare_native_calls.py --output outputs/engine-bindings-v06/recheck-c-calls
python work/v06-compare/compare_native_lua_calls.py --smoke --output outputs/engine-bindings-v06/recheck-lua-call-smoke
python work/v06-compare/compare_native_lua_calls.py --output outputs/engine-bindings-v06/recheck-lua-calls
```

The math and call runners load `work/v06-runtime/amalur_native_math.lua`. To regenerate and replay the bounded selection of real functions:

```powershell
python work/v06-compare/prepare_real_vm_cases.py --output outputs/engine-bindings-v06/recheck-real-fixtures.json
python work/v06-compare/compare_native_vm.py --real-fixtures outputs/engine-bindings-v06/recheck-real-fixtures.json --output outputs/engine-bindings-v06/recheck-real-bodies
```

The real-body selector admits acyclic primitive functions with no captures, globals, calls, strings or varargs. It selects in source order, deduplicates exact code/constants/signatures, and records original file hashes and instruction offsets. This is a domain restriction, not representative whole-corpus sampling. Input rejection details remain in `excluded-inputs.json`.

## Isolation and provenance

The target is the installed `koa.exe`, SHA256 `16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314`. The runner verifies it before and after execution; the native process verifies it before mapping.

The harness maps original PE sections into its own address space and applies only validated standard PE HIGHLOW base relocations. It records mapped base, relocation delta and patch count. It never invokes the PE entrypoint, TLS/CRT initialization, import resolution, game startup, Steam startup, process attachment, or save access. It does not patch the installed executable. Synthetic states, registers, prototypes and call frames belong to the harness process. Native faults fail explicitly; the parent runner enforces a 45-second subprocess timeout.

The original VM dispatch may specialize the fixture instruction array in memory. Those writable instructions are fixture inputs, not installed game code. The target's original machine instructions are changed only by standard loader relocations.

Modes remain separate: `OMVM06` primitive VM, `OMCB06` five native math callbacks, `OMCL06` controlled C calls, and `OMLU06` seeded nonvararg Lua prototypes. The C callees used for empty/nil/multiple/echo behavior are authored boundary inputs; original VM dispatch, frame setup and result movement are what those tests verify. Seeded Lua callees similarly test frame behavior without exercising allocation or CLOSURE creation.

`native_vm_harness.calls-verified.c` preserves the C-call-tested source before the seeded-Lua extension. The current `native_vm_harness.c` contains all four modes. Native outputs, process exit details, fixtures, generated sources and comparisons are retained in each output directory, including failure artifacts.

## Limits relevant to Android

These results support tested VM semantics on exact admitted inputs. They do not establish Android compilation or execution, engine API behavior, game resource loading, graphics/audio, game state, saves, allocation/GC, capture lifetime, Lua tail-call frame reuse, vararg frame rotation, scheduling, yields, error unwinding, coercions, metamethods or whole-game equivalence.

The Android implementation must supply portable Lua/runtime behavior and the required engine services. This original-x86 Windows harness remains a reference to compare against; copying or mapping the Windows PE is not an Android port. See `NATIVE_COMPARISON_SCOPE.txt` for exact native structure offsets and supporting function addresses.
