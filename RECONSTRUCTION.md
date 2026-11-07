# Opem Amalur Lua reconstruction v0.4

This Windows tool reconstructs guarded Lua 5.1 source from the observed Amalur format `0x08`. It preserves instruction evidence, control-flow edges and explicit unresolved reasons in JSON IR. Generated register names and control flow are new; these are not original source files or game-ready replacements.

## Run on Windows

Extract the tools archive into `C:\Users\rwill\Documents\Opem Amalur`. Python 3.10+ is sufficient for the parser/reconstructor. Original scripts must be extracted from your own installed game; the deliverables exclude original executables, archives and binary scripts.

```powershell
New-Item -ItemType Directory -Force outputs\my-reconstruction
python src\amalur_reconstruct.py work\script-samples\1596600.lua_bxml --profile outputs\native-script-profile.json --output outputs\my-reconstruction\small.lua --ir outputs\my-reconstruction\small.ir.json
```

Input is the original extracted binary script, not the parser's JSON. Existing output files are replaced; outputs may not alias the input or semantic profile.

## Semantics

The profile admits bounded forms of 41 opcode mappings. Branches preserve native edges using explicit program-counter dispatch. Numeric loops use the native signed-32-bit iteration count, wrapped arithmetic and truncating division, not stock Lua numeric-for semantics. Their internal tagged counter cannot escape through ordinary values or captured cells. Generic loops preserve nil-only termination and fixed result counts; the native specialized iterator implementations themselves are not recreated.

Open calls, returns and VARARG preserve exact counts, including trailing nils and zero results. Every open consumer requires consistent stack-top provenance on all incoming paths. Fixed calls clear their native register tail; open calls invalidate fixed-register knowledge in their reused stack window. Calls overlapping live captured cells are rejected. CLOSE detaches those cells. Vararg flags 0, 2 and observed 3 are admitted; flag 7's legacy argument table is not implemented.

NEWTABLE supports bounded allocation hints (decoded array/hash capacities up to 65,536), with ordinary empty-table semantics. SETLIST handles fixed/open lists and extended block words, preserves values outside its written interval, and resets/nil-fills the stack window. GETFIELD and table operations require plain tables without metatables. LEN supports strings by byte length and dense positive-index sequences; sparse tables are rejected. DIV accepts signed-32-bit integers, truncates toward zero, and rejects division traps. Other arithmetic remains unmodeled.

Captured functions share mutable cells. Standalone captured-body drafts return factories accepting zero-indexed `{value=...}` cells and require the original environment. A body may be supported while its child functions remain explicit error stubs. Fully supported script counts require every body to be supported.

Very large functions use groups of at most 64 instruction cases, selected by binary search and connected through tail calls, to avoid Lua 5.1 jump-distance limits. This retains the register/cell state and exact returned value counts. Module-style environments propagate between groups and synchronize to the function on normal completion. Exceptional environment propagation, error/yield stack behavior and debugging stack layout are not equivalence claims.

## Validation

All game analysis, reconstruction, compilation and runtime tests run on Windows. Project-local validation dependencies:

```powershell
python -m pip install --only-binary=:all: --target tools\python-libs lupa==2.6
python -m unittest discover -s tests -v
python work\validate_lua51.py outputs\reconstruction-v04
```

For the separate syntax parser, install `luaparse@0.3.1` under `tools/lua-validation` using `npm.cmd`, then run `node work\validate_lua.cjs outputs\reconstruction-v04`. The compiler checker uses actual Lua 5.1 without invoking the chunks. Runtime tests execute generated code with bounded instruction hooks and mocked APIs, never the game.

Tests fingerprint original fixtures under `work/script-samples`, `work/capture-corpus`, and `work/initial-script-corpus-v04`. Existing v0.3 mock tests also use their retained `outputs/reconstruction-v03` fixture IR; the newer real-function tests parse and reconstruct original files afresh. Missing fixtures/dependencies can cause failures or skips and must be reported separately. Original game files and validation libraries are not bundled.

The frozen full-archive inventory and final validation report give exact counts. Coverage describes this observed build and guarded operand domains, not all game archives or universal native equivalence. The game executable remained unchanged.

## Reproduction helpers

`analyze_initial_corpus_v04.py` inventories the retained initial archive list, extracts to a new project-owned directory and compares against `work/baseline-v03`. `export_initial_corpus_v04.py` exports its reconstructed bodies and whole-script drafts. The optional refresh helper records the large-dispatch/flags3 transition from the first export. These scripts expect this project's Windows directory layout and retained inventory; they are not general-purpose installers. New extraction/export directories must not already exist.

Remaining work includes other arithmetic/string/table opcodes, legacy vararg tables, additional cached-state proofs, the batch wrapper variants, readable high-level source structure and native-runtime differential verification. Engine reconstruction and a native game build remain separate work.
