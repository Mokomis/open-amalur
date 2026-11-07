# Proven native shader parameter hash and leaf defaults

The native material member hash is recovered directly from `FUN_00af09a0` and its50-entry constant table. `FUN_00c58570` obtains D3D reflection member names and calls this hash with start0,strlen,seed0 before retaining key/byte-offset/size records. This establishes the link between shipped HLSL names and serialized material parameter keys independently of parameter values.

For ASCII names, lowercase each byte c[i], then:

    hash = seed + sum(TABLE[i % 50]*c[i] + TABLE[c[i] % 50]*(i+1)) mod 2^32

Native code walks backward and decrements the length counter; the expression above is the identical additive form. `hash_name.py` is a tested independent implementation. ASCII case variants produce identical results. Extended locale/non-ASCII `_tolower` behavior is not modeled.

| Shader member | Proven decimal key | Hex |
| --- | ---: | --- |
|UseSphericalNormals|22257620|0x01539fd4|
|CenterZOffset|8960387|0x0088b983|
|NormalDisable|10157840|0x009aff10|
|TranslucencyDisable|23106261|0x016092d5|
|SpecularDisable|13865487|0x00d3920f|
|TreeLeafMovementScale|26820802|0x019940c2|
|AlphaCutoff|6936447|0x0069d77f|
|AlphaReference|11015508|0x00a81554|

The same implementation exactly reproduces the previously known ConstantColor10276250,SpecularValues11960536 and all four UTile/VTile/UTile2/VTile2 keys. `all-material-field-keys.json` supplies the98unique material member names found in the retained shipped shader assembly collection. Extra leaf keys20600203 and11685259 do not match any of these98names; their semantics remain unknown. In particular,11685259 is not AlphaCutoff.

The table is read from original Windows koa.exe at VA0x01721040, file offset0x01320040,200bytes. Its entries and byte SHA256 plus complete binary SHA256 are recorded in `hash-key-map.json`; `native-hash-table.bin` preserves the original bytes. The native hash/reflection function exports are saved beside it. No native execution, UI or database open was needed.

Foliage's missing-parameter-default investigation was independently checked against the retained native code: `FUN_00c8dbe0` first calls `FUN_00c58d40`, which allocates a16-byte-aligned material constant span and explicitly memset-zeroes every byte. It then walks only the authored24-byte material parameter records, finds matching reflected key records and copies those values to their mapped offsets. Missing members therefore retain zero in this material construction path. This is a native initialization contract, rather than an inference from an absent DXBC default blob.

Consequently the leaf materials with only movement/spherical/center fields use NormalDisable=0,TranslucencyDisable=0,SpecularDisable=0. Main359202 explicitly supplies1 for each of those disable fields, so those values must not be carried into sapling materials by default.

Finally `FUN_00c8dbe0` injects AlphaCutoff independently: it reads one byte at materialData+0x1c (file+0x24 after the8-byteBXML wrapper), divides by the native double255.0 at VA0x013bf4d0, finds reflected key0x69d77f and copies that scalar. The255.0 bytes were read and verified from the same PE. This supports main header100→100/255 and grass header128→128/255 without calling the unrelated.01 leaf parameter an alpha cutoff.

Only new hash-params files were written. Existing tools, source, assets, original executable, saves and native databases were preserved. The recovered mapping and default contract were delivered directly to root and the foliage worker.
