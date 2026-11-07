# Generation3 combined static, leaf and river overlay

Ready output: Windows `work/v44-native-fidelity/static-overlay/world/`, with `manifest.json` generation3. Generation2 is preserved in `world-generation2/` and `manifest-generation2.json`. Existing prepared application assets and renderer source were not edited.

The44OAWE cells retain932,374baseline triangles,108,786source-correlated static triangles and4,872source-correlated leaf triangles. They suppress all6,494old river copies across all3LODs. Existing terrain and restored prop geometry remains. All positions/UV0 are preserved from the original cells, and static/leaf source-removal sets are disjoint.

Materials total296. Existing293MATS rows, native-material sidecar rows and water rows exactly match generation2 byte-for-byte. New family6rows293/294/295 map native materials359202/419060/559590. COLOR is(UseSphericalNormals,CenterZOffset,NormalDisable,TranslucencyDisable);SPEC is(SpecularDisable,TreeLeafMovementScale,0,0); tiling is all1. MATS alpha cutoffs are independently verified against the source file header byte at0x24:100,128,128. Flags route these rows through the cutout/depth phase; leaf lit-pass coverage remains the renderer's depth-EQUAL contract.

| Material row | Diffuse with combined native alphaG | Native slot3normal | Dedicated native alphaMapG |
| --- | ---: | ---: | ---: |
|293|0|678|679|
|294|17|18|680|
|295|22|18|680|

Native slot3normal1451347 gets new texture678; original alpha maps343436/477449 get new textures679/680. Sapling normal457710 reuses verified native-normal build key index18. Existing diffuse maps reuse exactly matched(assetID,alphaID,kind=d) keys. Raw alphaG is separately available at full selected source resolution for native depth sampling. File provenance and SHA256s are in `leaf-generation3/leaf-textures-and-profiles.json`. Texture count681 reserves677 for root's noise texture and655..657 for root's grass textures; this overlay writes none of those reserved files.

The foliage worker froze its final files before snapshot. `leaf-inputs-generation3/input-manifest.json` records the44input file hashes. Input layout details are preserved exactly: for family6, UV1@56 contains two float-bitcast packed-half world wind direction/palette-index words, and the final uint32@72 carries radialLength FLOAT BITS. It is not the static family's flags3 field. No interpretation, normalization or repacking was introduced by the merger.

Independent `generation3-validation.json` verifies every complete76-byte record for all4,872leaf triangles is byte-identical to the frozen OAWT input after grouping by native material. This explicitly checks packed UV1 and radialLength bits. It also verifies prior293material/profile/water rows unchanged, index cell/grass records unchanged, reserved texture IDs untouched and every output file SHA256 before promotion.

`build_static_overlay_generation3.py` creates staging output in `world-next-generation3/` and its versioned manifest. Root owns deployment, grass/noise/index merge, shader/render-state integration and GPU/visual checks. Earlier limits on unsupported material families, clustered static attributes and native mip filtering remain. This generation adds no unvalidated renderer behavior.
