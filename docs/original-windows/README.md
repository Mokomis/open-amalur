# Opem Amalur script parser

An initial, dependency-free Python structural reader for the observed Kingdoms of Amalur: Re-Reckoning Havok Script format `0x08`. It writes a JSON function tree and an optional bytecode listing with native-confirmed opcode names. It does **not** reconstruct Lua source or establish the behavior of the game runtime.

## Run on Windows

Requires Python 3.10 or newer. Put `amalur_script.py` in the project's `src` directory and `test_amalur_script.py` in `tests`. From `C:\Users\rwill\Documents\Opem Amalur`:

```powershell
python src\amalur_script.py work\script-samples\1596600.lua_bxml --output outputs\parser\small.json --disassembly outputs\parser\small.txt
python -m unittest discover -s tests -p test_amalur_script.py -v
```

Create the output directory first if necessary. Input may be an extracted `.lua_bxml` script wrapper or a raw chunk beginning with `1b 4c 75 61`. The parser does not unpack archives, launch the game, or modify its installation. Outputs cannot alias the input, including through an existing hard link. Existing unrelated output files are replaced.

The Python API exposes `parse_file(Path(...), Limits(...))` and `parse_bytes(data, Limits(...))`. Defaults cap the input at 16 MiB, individual strings at 1 MiB, functions at 10,000, child depth at 64, and aggregate instructions and constants at 1,000,000 each. The file read itself is bounded even if the file grows after its size check. These limits bound input traversal; JSON expansion can be substantially larger than the binary input.

## Observed layout

The reader admits only this exact 14-byte profile header:

```text
1b 4c 75 61 51 08 00 04 04 04 04 01 01 00
```

The wrapper has a little-endian 32-bit name length, name bytes without a terminator, a 32-bit metadata-string count, that many length-prefixed non-NUL strings, a 32-bit payload length, and the payload. The initial three samples have count zero; the broader corpus established the optional list. Its strings' semantic role is not yet verified against the native wrapper reader. Counts/lengths are bounded, and the payload length must match the remaining file exactly. `opaque_word` remains a legacy alias for the count.

The chunk uses big-endian 32-bit counts and words. Counted strings include a terminal NUL; zero length represents a null string. The type table is read dynamically and checked against the 13 native-required type IDs and names, in their required order. Its end happens to be offset `0xee` in the tested chunks; this is not hardcoded.

Each recursive function is read as two counted strings; two source-line fields; upvalue and parameter counts; one byte of vararg flags; maximum stack size; instruction count and unaligned 32-bit words; tagged constants; recursive child functions; and three debug-array counts. The native function reader at `0x010c1730` corroborates this field order and the unaligned code. The first prefix string inherits the parent value when null; its source-name role is inferred. Both prefix strings are null in the first two samples; their exported labels remain conservative.

The current profile supports only zero debug-array counts and an empty structure trailer consisting of marker `1` and a null counted string. Nonempty debug or structure sections, other headers, unsupported constant tags, invalid counts, truncated fields, and trailing data produce an error with a file offset. Nothing is silently skipped.

Supported constant encodings are nil, boolean, 32-bit light userdata, a four-byte number, counted string, and unsigned 64-bit integer. The four-byte number is preserved as raw hex and exposed as signed `integer_value` (plus legacy `declared_integral_value`). The native reader and signed DIV/LT handlers confirm signed 32-bit numeric values. Stock Lua arithmetic does not necessarily preserve game arithmetic behavior. Support for an encoding does not mean every encoding has appeared in the real fixtures.

Instruction output preserves each raw word. All 86 opcode names and IDs match the native table at `0x01973560` in the reference executable with SHA-256 `16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314`. The old `opcode_name_provisional` key remains as a compatibility alias; `opcode_name` carries the same label. Native dispatch and handlers confirm a 7-bit opcode in bits 25–31, A in bits 0–7, B in bits 17–24, C in bits 8–16, and Bx in bits 8–24. JMP confirms signed Bx bias 65535. Operand interpretation remains opcode-specific: for example CALL and GETFIELD_R1 use only the low eight C bits, and arithmetic B decoding incorporates the opcode low bit for constant operands. Selected constant, child-function, and branch indices are checked against the current function. This is not a full bytecode verifier: operand modes, register effects, control-flow semantics, and specialized instructions still need confirmation.

## Evidence and validation

All real-sample parser execution was performed on the Windows machine. The original extracted inputs remain unchanged.

| Extracted script | Payload offset | Payload bytes | Functions | Instructions | Constants |
| --- | ---: | ---: | ---: | ---: | ---: |
| `1596600.lua_bxml` — `MQ14_Alyn_Laz_Defence` | 33 | 644 | 2 | 27 | 20 |
| `441939.lua_bxml` — `SQ02` | 16 | 35,685 | 154 | 2,622 | 1,538 |
| `1701254.lua_bxml` — `ENC_SQ97_AltarEncounter` | 35 | 1,439 | 5 | 95 | 59 |

Each parse consumed the complete declared payload. The third sample was selected after the parser worked on the first two and passed without changes. This is evidence for the admitted structural profile, not coverage of all game scripts.

The first parser pass passed 32 Windows tests. Native corroboration adds reordered-type-table rejection and signed integer boundary tests; see the current validation record for final totals. The third held-out sample in the table was validated separately with the unchanged parser.

The test suite fingerprints the first two local samples and checks counts, complete consumption, and unchanged input bytes. Synthetic cases exercise every truncated prefix of a minimal raw chunk and wrapper, count/size/depth budgets, unsupported structures, invalid indices, bounded reads after file growth, and hard-link output protection. Real-fixture tests skip when the sample directory is absent; set `AMALUR_SCRIPT_SAMPLES` to override the default Windows project sample location. Game files are not included with this parser.

## Adaptation provenance and remaining work

This independent reader combines observations from the local samples with these public source references:

- [Kender2/amalur, `korevm.md`](https://github.com/Kender2/amalur/blob/314e878609f42e9f53cb407c5dab72564ad5fdeb/korevm.md): Amalur opcode names and general format research. The mapping was subsequently matched against all 86 rows of this Re-Reckoning executable’s native opcode metadata table.
- [hksc undumper](https://github.com/Jake-NotTheMuss/hksc/blob/master/src/lundump.c), [header definitions](https://github.com/Jake-NotTheMuss/hksc/blob/master/src/lundump.h), and [opcode definitions](https://github.com/Jake-NotTheMuss/hksc/blob/master/src/lopcodes.h): related Havok Script serialization and operand-layout references. The inspected `lundump.c` Git blob was `11effa08bf286bab557000218ce2feb8a3368260`.

The modern hksc layout is not treated as an exact specification for format `0x08`. In the observed Amalur profile, prefix fields precede code, code is unaligned, and child functions precede stripped debug counts. Generic format `0x0e` readers cannot simply be used unchanged; string widths, ordering, and opcode numbering differ.

Current loop/list, branch/capture, and full-archive validation are documented in `RECONSTRUCTION.md` and `outputs/loops-openlists-findings.md`. The next stage is implemented in `src/amalur_reconstruct.py`; see `RECONSTRUCTION.md` and `outputs/native-script-profile.json`. It uses an explicitly admitted native-static subset to produce register-level Lua and an instruction/control-flow IR. Branches now use a program-counter dispatcher and captured variables use shared mutable cells. Remaining work includes high-level control-flow structuring, arithmetic beyond guarded integer division/loop operations, legacy vararg tables, additional operand domains, batch wrappers, debug/structure sections, and native runtime equivalence. Header byte 12 and the second prefix-string meaning remain unnamed. These are observed-build findings, not a universal Havok Script specification.
