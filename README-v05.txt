Opem Amalur script reconstruction tools v0.5

Windows workspace: C:\Users\rwill\Documents\Opem Amalur
Target: Steam Kingdoms of Amalur Re-Reckoning, build10619381, x86 koa.exe
SHA256:16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314

The structural parser reads the observed format0x08. The reconstructor produces
guarded Lua5.1 register-level source with explicit control flow and shared
capture cells. These are generated source drafts, not original source or a
working replacement for the native game engine.

Files and use
  src/amalur_script.py       structural parser and explicit bundle API
  src/amalur_reconstruct.py  native-profile-driven lifter and Lua generator
  src/cache_flow.py          whole-CFG cached-value must-alias proof
  src/amalur_uint64.lua      exact opaque type11 carrier, shared per Lua realm
  outputs/native-script-profile.json  evidence, admitted semantics and guards

Single script:
  python src\amalur_script.py INPUT --output parsed.json
  python src\amalur_reconstruct.py INPUT --profile outputs\native-script-profile.json --output draft.lua --ir draft.ir.json

Batch wrapper:
  python src\amalur_script.py INPUT --bundle --output bundle.json
  Or iterate iter_bundle_file(Path(INPUT)); each yielded member can be passed
  independently to reconstruct(member,profile). Exhaust the iterator before
  treating a container as fully validated. Container order is storage evidence,
  not a native-confirmed load order. Preserve all container/member bindings.

Tests:
  python -m unittest discover -s tests -v
  python -m unittest discover -s work/v05-parser -v
  python -m unittest discover -s work/v05-cache -p test_cache_flow.py -v
  Runtime checks need the existing tools/python-libs Lupa2.6 (Lua5.1).
  Corpus checks need extracted game files under work/initial-script-corpus-v04;
  game files and dependencies are not included in this tools package.

Complete corpus workflow:
  python work\export_corpus_v05.py
  Export destination must not already exist. Every unique exact wrapped input
  is exported once; all standalone and batch occurrence bindings are retained.
  Full scripts plus every function body are compiled with Lua5.1 during export.
  Recovered code is not run against the game by this workflow.

Type11 / 64-bit IDs
  Before invoking a draft that transports these IDs, install one runtime module
  instance per Lua realm:
    __amalur_uint64 = dofile('src/amalur_uint64.lua')
  The source passes exact sixteen-digit hexadecimal serialized bits. The native
  reader replaces the low nibble with b. The module interns immutable userdata
  using that canonical identity; it never converts IDs to floating point.
  Native or replacement-engine bindings must explicitly marshal those tokens.
  The module alone is not an adapter to the shipped game. Arithmetic, ordering,
  custom equality and table keys outside the admitted domains still raise an
  explicit error. Raw serialized bytes remain in parser and IR provenance.

Recovered v0.5 behavior
  Exact int32 ADD/SUB/MUL/MOD/POW/UNM, with low32 wrapping and signed remainder;
  guarded string/int32 concatenation; SELF and typed table access/fallback;
  canonical tail calls with owned open RETURN; cached-register alias proof
  across branches/loops; flags7 legacy arg table with exact n and shallow-copy
  array storage separate from later VARARG reads; exact type11 transport.
  Existing numeric/generic loops, open argument/result lists, branches and
  mutable captured variables remain supported with their original guards.

Limits
  Initial_0.pak only. No native engine reconstruction or all-archive claim.
  No runtime differential comparison against the Havok interpreter yet.
  Primitive signed-int32 and plain-table domains; custom userdata, coercions
  and metamethod paths are not generally implemented. Type11 transport requires
  an explicit shared adapter and matching engine bindings.
  Nonempty debug/prototype sections and other header variants remain outside
  the observed structural profile. High-level source structuring and original
  local variable names have not been recovered. Large dispatcher environment
  synchronization is checked on normal completion, not errors or yields.
