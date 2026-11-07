# Native water authored mip chains: version2

Ready new files beside the preserved version1 files:

- `water-native-mips.bin`,51,897,504bytes, SHA256 `82ff8c07847bf8aef4e35b0b9db50c6cfa6cfbf041590c9762a5f056fc4fa911`
- `oa_native_water_mips.c`, same `oa_native_water.h` API

Use the new source in place of the version1 implementation, and load the version2 pack. If retaining the existing asset path, deploy the new pack under that path; do not compile both source implementations together. Neither the original implementation/pack nor the generation3world overlay was changed by this follow-up.

## What changed

All12captured texture resources now retain every actual recorded mip:8two-dimensional maps and4reflection cubes,86texture/level combinations and206individual face/level subresources. The portable pack stores decoded RGBA8 for each authored level. There is no mip resampling, glGenerateMipmap call or invented tail level. Texture base/max levels are explicitly0 and originalMipCount-1, preserving the truncated native views rather than extending them to1x1.

| Captured image | Type/size | Actual levels | Last level size |
| --- | --- | ---: | ---: |
|3549,3574,3594,5807|cube128²x6|6|4²|
|5752|2D128²|6|4²|
|14037,14044,14067|2D512²|8|4²|
|14062,14104|2D2048²|9|8²|
|14456,14461|2D256²|7|4²|

All12top mip payloads are byte-identical to version1. The complete8draw payload is copied verbatim, including meshes, vertex attributes, native materials, texture/probe associations, point-light data and tint/luminance vectors. Vertex/fragment shader source literals and the public header are unchanged. Live camera/time behavior therefore remains with the existing API; this change addresses resource mip content and upload only.

## Capture layout and provenance

Input is the previously validated frame recording and its exact InitImage decompressed payloads. `water-mip-pack-manifest.json` preserves image format/extents/layer count/mip count, original recording block/file offsets/hashes, each tight BC face byte range/SHA256, and every decoded RGBA face/level SHA256. It records the unchanged draw-tail hash and offsets in both pack versions.

Mip starts follow the recorded level_sizes array. For these resources, recorded allocation size equals faces*align(tightBCfaceBytes,512), but this is NOT a per-face payload stride. Cube face payloads are tightly contiguous WITHIN each mip; excess allocation bytes are unused at the LEVEL TAIL.42,104total padding bytes are excluded from the portable pixel payload.

This distinction was verified before final handoff. `snapshot-layout-evidence.cpp` preserves the retained GFXReconstruct replay contract: bufferRowLength0,bufferImageHeight0 and a single copy region with the full layerCount per level. `cube-padding-continuity-check.json` independently corroborates all12lower-cube-level layouts against their previous authored levels. Incorrectly treating allocation alignment as an internal face stride produces large semantic discontinuities. The final pack uses tight face strides and passes every comparison.

The BC1/BC3 decoder is exactly the reviewed version1 integer decoder, preserving its top-level colors and alpha handling. PortableRGBA8 endpoint/interpolation rounding can differ slightly from direct native BC sampling; this pre-existing quantization qualification remains. The authored lower levels themselves are now recovered rather than generated.

## Version2 pack framing

Little-endian header: OAWP,u32version2,u32textureCount,u32drawCount.

For each texture: six uint32 values: imageID,faces,topWidth,topHeight,mipCount,totalDecodedRGBAbytes. Then each mip contains uint32width,height,RGBAbytes followed by tightly packed face-major RGBA8 pixels. Cube face order remains +X,-X,+Y,-Y,+Z,-Z. After the texture records, the entire version1draw payload follows unchanged.

The loader validates dimensions, face count, level count, byte totals and pack boundaries. Each captured mip/face is uploaded individually with glTexImage2D; GL_TEXTURE_MAX_LEVEL is set to the actual last level. CPU mip data remains owned for GPU context recreation, matching the prior lifecycle API.

## Verification

`water-mip-source-validation.json` proves source shader/header identity and absence of glGenerateMipmap. `gpu-mip-validation.json` records the FINAL pack hash tested on Windows with the existing host headers, MSVC and ANGLE offscreen context.

- Actual shader compile/link, all texture/VBO uploads and8draw submissions passed with GLerror0.
- Every byte of all206uploaded face/level subresources was read back from GPU attachments and compared with the portable pack:51,816,320RGBA bytes exactly matched.
- gpu_close followed by recreation/draw passed; all206subresources were read back and matched again.
- Original version1source and pack SHA256s were checked unchanged.

This was a private offscreen resource/upload smoke with no original-game or desktop UI launch. Root owns integrated visual comparison and Android validation. All new artifacts are confined to water-research/new mip files and water-mips/.
