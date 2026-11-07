# Complete native leaf normal/alpha mip staging

The follow-up receipt check found generated mip chains in all four current leaf auxiliary bindings. Exact source chains are staged independently; no active asset or material table was changed by this producer.

| Asset / use | Staged ID | Current binding | Native authored chain | Operation |
|---|---:|---|---|---|
|1451347 main normal|678|64x64,7levels|64x64,5levels through4x4|Same-ID native-only replacement|
|343436 main alpha|679|1024x1024,11levels|2048x2048,9levels through8x8|Same-ID native-only replacement|
|477449 sapling alpha|680|1024x1024,11levels|2048x2048,9levels through8x8|Same-ID native-only replacement|
|457710 sapling normal|684|Shared texture18:1024x1024,11levels|2048x2048,9levels through8x8|Append; preserve global18|

Root merge plan: copy the four `staged-assets/t*.bin` assets; change normal slot1 from18 to684 for materials294/295 in both material tables; set texture count685. Rows293/294/295 continue to use independent alpha.GREEN on unit2 and cutoffs100/255 or128/255. Existing global texture18 remains available to its other users. The separate diffuse stage681/682/683 is unchanged.

Each OATX retains every source-authored BC1 or BC3 mip, decoded separately toRGBA8 UNORM. There is no resizing, channel baking, premultiplication, color-space conversion or mip generation. Alpha and normal RGBA channels are preserved. Native sampler149 uses repeat, linear min/mag, linear mip, zero bias and anisotropy disabled; GLES anisotropy1 matches it.

`authored-leaf-auxiliary-manifest.json` records source SHA256, compressed mip SHA256, decoded mip SHA256, staged output SHA256, old-versus-authored mip comparisons, exact bindings and merge operations. An independent scalar BC1/BC3 decoder passed148/803/805/805 pixel checks across all levels respectively. Every complete decoded level was reparsed from the OATX and compared byte-for-byte.

Source files were already available under `work/v20-inputs`:1451347 in`initial_0.pak/1451347.dds`; the other three in`DATA_0.pak/*_1.dds`. No extraction, installation, app build or GPU launch was needed. Root owns promotion and rendered validation.
