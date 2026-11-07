# Authored leaf diffuse mip staging

Three independent staged OATX assets retain the original BC1 UNORM diffuse chains. Each source is2048x2048 with9 authored levels through8x8. All levels are decoded separately toRGBA8; no mip is resized or generated, no coverage alpha is baked, and no RGB/gamma transformation is applied.

| Native diffuse asset | Staged texture | Family6 material | Previous shared texture | Bytes |
|---|---:|---:|---:|---:|
|343437|681|293|0|22,369,592|
|457709|682|294|17|22,369,592|
|566740|683|295|22|22,369,592|

Root merge plan: append `staged-assets/t681.bin` through`t683.bin`; set texture count684; update diffuse slot0 in both `materials.bin` and the84-byte native-material sidecar for rows293/294/295. Preserve global textures0/17/22 because legacy cutout rows and fallback paths still use their combined alpha. Native family6 coverage continues to use independent raw alpha on`t2.GREEN`.

`authored-leaf-diffuse-manifest.json` records each source SHA, each compressed BC1 mip SHA, each decoded RGBA mip SHA, complete output SHA, exact merge assignments, and individual decoded sample checks. An independent scalar BC1 decoder matched803/805/805 sampled pixels across the three complete chains. Serialized OATX levels were reparsed and their entire decoded payloads compared byte-for-byte.

Native captured main diffuse image13901 is2048x2048,9mips, `VK_FORMAT_BC1_RGBA_UNORM_BLOCK`. Every compressed mip matches source343437 exactly, and every decoded captured RGBA mip matches staged texture681 exactly. Evidence is in `native-capture-image-identity.json` and `captured-main-decoded-identity.json`.

The two sapling source headers and their complete authored chains are verified. No exact source mip-base match was found among215 recorded BC1 images with base dimensions256/512/1024/2048 in the retained single-frame capture. Their runtime GPU image identities are therefore unconfirmed; source dimensions are not presented as observed GPU bindings.

Native leaf diffuse, normal and raw-alpha samplers use sampler149: linear min/mag, linear mip, repeat U/V/W, zero mip bias, anisotropy disabled. GLES maximum anisotropy1 reproduces that setting. The ambient cube uses sampler336, also anisotropy disabled, with clamp U/V. `native-leaf-sampler-contract.json` retains the exact descriptor and sampler records.

All files remain staged under this private directory. This producer changes neither the live pack nor any material table. Existing normal and raw-alpha assets are outside this diffuse-only stage. Rendering and visual validation belong to the root integration task.
