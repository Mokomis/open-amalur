# Native material state audit, rows263–295

`native-material-state-audit.json` records all33 source materials, source hashes and header words, current flags, independent-alpha bindings and proposed coverage flags.

The native material header contains shader ID at file0x18, AlphaTest at0x1c, CullMode at0x20, and cutoff byte at0x24. Source CullMode0 means NONE and2 means BACK in the correlated original pipelines.

- BACK:28 materials.
- NONE:274/489469 treebranch;275/577592 pln_sparrow;293/359202 main leaf;294/419060 sapling;295/559590 green sapling.
- Alpha-test enabled only on274 and293–295.
- Row274 uses independent native texture slot6.GREEN, texture667, cutoff100/255.
- Row293 uses slot2.GREEN, texture679, cutoff100/255.
- Rows294/295 use slot2.GREEN, texture680, cutoff128/255.

The root-proposed0x20000000 flag selects independent unit6.GREEN for alpha-tested non-leaf profiles. A separate0x10000000 flag may represent source CullModeNONE if root chooses that encoding. Neither rule should be inferred from shader family alone. Authored cutoff differences on AlphaTest0 materials do not affect coverage.

The later snapshot already includes root's row274 alpha correction. No material table was edited by this audit. Native pipeline evidence and exact black-pixel provenance are retained in the sibling `leaf-pixel-provenance` directory.
