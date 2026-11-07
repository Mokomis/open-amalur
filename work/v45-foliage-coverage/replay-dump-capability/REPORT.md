# Original bridge replay: selected attachment dumping

Status: isolated tool built; help/version smoke checks passed. **No GPU replay has run. Parent review is required before first replay.**

The prior successful Windows image used stock `work/v31-native-slice/capture-tools/windows-x64/gfxreconstruct-v0.9.18/gfxrecon-replay.exe`, version0.9.18(v0.9.18:a4ad90b+dx12), Vulkanheaders1.3.239. Actual help supports final-swapchain BMP screenshots, without selected attachment dumps. Existing capture-tools/replay-windows.cmd invokes it directly with --screenshot-all --opcd; Steam and the game are not involved.

Original capture: `work/v31-native-slice/captures/amalur_trim_trigger_20261105T113036.gfxr`,566,260,898bytes, SHA72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209, original frame50994. This matches the capture used for all preceding native shader/resource research.

## Isolated available tool

Built from existing work/v33-native-camera/src, in the requested new build directory. Actual --version says `1.0.5-unknown (unknown-build-source) Release`, Vulkanheaders1.4.363. Build-manifest.json records exact relevant source hashes; this source copy has no usable Git version identity. Build used local MSVC19.51.36260.0, Ninja, LZ4/Zstd/zlib/nlohmann dependencies. No downloads, installations, system reconfiguration or existing source edits.

Executable: build/tools/replay/gfxrecon-replay.exe
SHA256: `c330152751f150e7e3eea62b931c1d276e5fa1cf5667970a04ccd47300de7871`

The Windows help emphasizes submit/command/draw tuple mode, but the source explicitly accepts Vulkan JSON paths in replay_vulkan_feature.cpp:460–478 and parse_dump_resources_cli.cpp:555–571. The prepared command uses verified block-index JSON. The --api switch is excluded from this Vulkan-only build and is omitted.

Exact prepared command; **not executed**:

```cmd
"C:\Users\rwill\Documents\Opem Amalur\work\v45-foliage-coverage\replay-dump-capability\build\tools\replay\gfxrecon-replay.exe" --opcd --wsi win32 --dump-resources "C:\Users\rwill\Documents\Opem Amalur\work\v45-foliage-coverage\replay-dump-capability\dump-all-selected.json" --dump-resources-dir "C:\Users\rwill\Documents\Opem Amalur\work\v45-foliage-coverage\replay-dump-capability\selected-output" "C:\Users\rwill\Documents\Opem Amalur\work\v31-native-slice\captures\amalur_trim_trigger_20261105T113036.gfxr"
```

Prepared-replay-command.json is the authoritative argv. Dump-all-selected.json contains the selection. selected-output is a new path. No swapchain screenshot option is enabled.

## Actual selection indices

Capture JSONL index and research draw index are the actual Vulkan block index. Analysis phase numbers are not executable selection indices. All selected commands belong to command buffer46, vkBeginCommandBuffer block62473, vkQueueSubmit block76331. Enclosing begin/end dynamic-rendering blocks were recovered for every selected draw; there are no secondary command buffers.

|Stage|Block|Phase|Images|
|---|---|---|---|
|AO-generation-complete|66881|94|173 color,167 depth|
|AO-bilateral-horizontal-complete|66891|95|176 color,167 depth|
|AO-bilateral-vertical-complete|66901|96|179 color,167 depth|
|main-G0-G1-G2|69912|97|155 color,158 color,161 color,167 depth|
|shadow-cascade0|71740|99|182 depth|
|shadow-cascade1|72264|101|182 depth|
|shadow-cascade2|72641|103|182 depth|
|deferred-combine|72932|106|173 color,167 depth|
|scene-plus-sky|72940|107|173 color,167 depth|
|scene-before-fog-water-complete|72984|108|176 color,167 depth|
|scene-after-fog|73026|110|173 color,167 depth|
|scene-after-transparents|73214|111|173 color,167 depth|
|generated-color-LUT|73395|134|1862 color|
|post-LUT-bloom-merge|73404|135|179 color,167 depth|
|final-AA-before-HUD|73411|136|119 color,123 depth|

G0/G1/G2 images155/158/161 are1536x864 RGBA16F. Raw output preserves half-float data. AO stages use173/176/179 RGBA8. Shadow image182 is reused per cascade,1024x1024 D16; three selected checkpoints retain the three cascade versions. Pre-fog image176 is captured after water, then fog output173 afterPS1898. LUT image1862 is256x16. Merge output179 and final pre-HUD119 are separate checkpoints.

## Output bound and remaining validation

One replay selects15 draw boundaries. Raw attachment output preserves original dimensions. Vertex/index buffers, all descriptors, all image subresources and before-command duplicates are disabled. Estimated raw attachment data is149,635,072bytes(142.7MiB), plus stencil-plane/JSON/log overhead; reserve200MiB. Three optional category JSONs total96,550,912rawbytes but require separate replays of the same frame. These are static estimates, not observed output sizes.

Help and version are validated; GPU replay and attachment-dump correctness remain untested pending review. Use the dump metadata to correlate format, imageID and drawblock: images are reused across stages. No original captures, screenshots, saves, tools, renderer sources or databases were changed.
