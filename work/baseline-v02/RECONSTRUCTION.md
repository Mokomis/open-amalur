# Initial Lua reconstruction

`amalur_reconstruct.py` adds a conservative step after the structural parser: a register-level intermediate representation, basic-block boundaries, and Lua 5.1 source for the supported straight-line subset. It does not run the game or generated Lua.

Run on Windows from the Opem Amalur project:

```powershell
New-Item -ItemType Directory -Force outputs\reconstruction
python src\amalur_reconstruct.py work\script-samples\1596600.lua_bxml --profile outputs\native-script-profile.json --output outputs\reconstruction\small.lua --ir outputs\reconstruction\small.ir.json
python -m unittest discover -s tests -p test_amalur_reconstruct.py -v
```

The profile path is explicit: use the native semantic profile produced by this investigation, not a profile inferred only from opcode names. Each admitted operation records its native evidence references; the IR retains the complete profile, original input hash, raw instruction words, file offsets, register reads/writes, payload-word locations, control-flow edges, and unresolved obligations. `null` successors mean unknown control flow, not an absent edge.

Supported emitter operations are register moves, supported literal loads, environment reads/writes, confirmed field reads, fixed-argument/result calls, fixed returns, and closures without captured upvalues. Known jumps are retained in the IR but prevent source emission until control-flow structuring is implemented. Instructions after an earlier return also prevent emission. Reads without a known register definition remain unresolved.

Inline DATA words are consumed only through a confirmed owning instruction, with bounds and opcode checks. Global-load cache slots must fit in the function's constant pool. They are not emitted as silent no-ops. Cached `GETFIELD_R1` is admitted only immediately after a confirmed global load that produces the hidden last result, and only when the encoded register matches that producer. Other uses remain unresolved. The initial emitter rejects high operand flags for this instruction and calls, vararg flags other than 0/2, open calls/returns, captured-upvalue closures, unconfirmed number interpretation, and large register-local bodies.

Each unsupported function body becomes an explicit `error(...)` stub with an `UNRESOLVED` comment. The report counts emittable and unresolved bodies separately; a supported parent may still contain an unresolved child. Do not treat partially emitted output as equivalent to the original script. The tool never reports a complete decompilation merely because it wrote a Lua file.

Generated names such as `r0` represent VM registers, not recovered source names. String literals preserve exact input bytes. A localized `getfenv` helper reads the executing function's current environment at every global access; it does not retain a stale `_G` table across a `module(...)` call. Child functions are created at their original closure instruction, preserving that ordering. The output targets Lua 5.1 environment semantics and has not been validated in the game's Havok Script runtime.

The synthetic suite checks explicit refusal of unconfirmed semantics, payload-word handling, cached-result assumptions, argument/result ranges, exact string bytes, signed number rendering, register bounds/definitions, closure restrictions, and jump edges. Native confirmation and real-sample results are recorded separately by the parent investigation; synthetic tests alone do not validate opcode meanings.

## Validated continuation

The final combined Windows suite passes 61 tests: 34 parser tests and 27 reconstruction tests. All three real samples complete reconstruction. The small MQ14 script emits both bodies without unresolved stubs. Across all samples, 101 of 161 bodies are eligible for standalone drafts; 60 remain unresolved. These are static results, not game-runtime validation.

Export each supported body from a saved IR into a fresh directory:

```powershell
python work\export_fragments.py outputs\reconstruction\sq02.ir.json outputs\reconstruction\fragments\sq02
```

A standalone draft requires its original environment and can contain explicit unresolved child stubs. The full IR preserves every analyzed child even when an unresolved parent prevents it appearing in whole-script output.

Optional syntax validation uses the project-local luaparse dependency and does not execute Lua:

```powershell
npm.cmd install --prefix tools\lua-validation --ignore-scripts --no-audit --no-fund luaparse@0.3.1
node work\validate_lua.cjs
```

All 104 generated Lua files passed this Lua 5.1 syntax check. Lua environment/runtime behavior still needs independent validation.
