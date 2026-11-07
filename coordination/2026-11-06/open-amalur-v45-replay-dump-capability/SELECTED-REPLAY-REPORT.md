# Selected original-frame replay: result and exact pixel references

The reviewed exact argv ran once, succeeded on the first attempt (exit0), and completed in2.922seconds including launch/load. It dumped54files totaling164,275,677bytes(156.67MiB), below the200MiB budget. It did not launch Steam/the game or close the reference app. The original capture is unchanged.

All15 requested boundary draw JSONs are present. There are39 raw color/depth/stencil planes. Raw G0/G1/G2 retain little-endian RGBA16F; U8 stages retain exact RGBA8; D24 depth is24LSB little-endian UNORM with a separate U8 stencil plane; shadow depth isD16 UNORM. Every raw output and JSON file has a SHA256 inventory.

## Orientation proof

Coordinates are zero-based top-left x,y, raw row0top. FinalAA RGB matches the historical original Windows replay screenshot exactly at all3requested pixels and throughout rectangle(x450,y120,width700,height480): direct mean absolute error0; vertically flipped error43.544228. This proves the preview/sample orientation and confirms no replay divergence in that region.

## Exact material samples

|Pixel|G0 normal/gloss RGBA16F|G1 albedo/spec RGBA16F|G2 ambient/tag RGBA16F|
|---|---|---|---|
|[800, 150]|0.0776977539062, 0.242797851562, 0.5, 64|0.00141525268555, 0.0014762878418, 0.000400304794312, 0|0.000320911407471, 0.000362157821655, 9.44137573242e-05, 0.1875|
|[980, 210]|0.91455078125, 0.65234375, 0.5, 64|0.30615234375, 0.31689453125, 0.0787353515625, 0|0.0601501464844, 0.0921630859375, 0.0256958007812, 0.1875|
|[500, 35]|0.98828125, 0.392822265625, 0.5009765625, 20|0.274169921875, 0.223022460938, 0.087890625, 0.0950317382812|0.0437622070312, 0.0487976074219, 0.0213470458984, 0.1875|

The JSON retains full exact numeric values, including all four channels. FinalAO isRGBA(255,255,255,255) at all3pixels.

## Exact RGB stage samples

|Draw / stage|(800,150)|(980,210)|(500,35)|
|---|---|---|---|
|66881 / AO-generation-complete|255, 255, 255|255, 255, 255|255, 255, 255|
|66891 / AO-bilateral-horizontal-complete|255, 255, 255|255, 255, 255|255, 255, 255|
|66901 / AO-bilateral-vertical-complete|255, 255, 255|255, 255, 255|255, 255, 255|
|72932 / deferred-combine|0, 0, 0|37, 42, 10|26, 21, 8|
|72940 / scene-plus-sky|0, 0, 0|37, 42, 10|26, 21, 8|
|72984 / scene-before-fog-water-complete|0, 0, 0|37, 42, 10|26, 21, 8|
|73026 / scene-after-fog|34, 29, 18|71, 66, 33|57, 48, 27|
|73214 / scene-after-transparents|37, 34, 22|77, 77, 41|64, 61, 37|
|73404 / post-LUT-bloom-merge|35, 32, 20|116, 115, 57|70, 65, 37|
|73411 / final-AA-before-HUD|35, 32, 20|116, 115, 57|70, 65, 37|

## Residual brightness: what this proves

At(800,150), native albedo is already approximately(.001415,.001476,.000400) before lighting. Its G2ambient is approximately(.000321,.000362,.000094), and deferred combine quantizes toRGB0. It stays0 through sky/water; fog produces(34,29,18), transparents change it to(37,34,22), and color/bloom merge gives the final(35,32,20). The parent reports current port final(72,62,35).

The native reference therefore establishes a concrete material/albedo checkpoint for the brightness discrepancy. A matching custom G1/readback is still required to identify the first divergent stage; final color alone does not establish whether the cause is material sampling, geometry/visibility, lighting, fog, or the final transform. No visual tuning or renderer changes were performed.

## Artifacts

- analysis/pixel-samples.json: all stages, exact native formats, numeric values and orientation proof.
- analysis/color-pixel-samples.json: concise color-only samples.
- analysis/native-stage-contact-sheet.png:9stage overview with sample markers.
- analysis/previews/: full-resolution color previews, AOchannels, shadowdepth and optional4x ambient display. Raw values remain unchanged.
- analysis/raw-inventory-sha256.json: all54raw/metadata output file sizes and hashes.
- selected-replay-result.json and selected-replay.log: exact executed argv, exit, timing and inventory.

All core sources, captures, archives, databases and live assets remain preserved.
