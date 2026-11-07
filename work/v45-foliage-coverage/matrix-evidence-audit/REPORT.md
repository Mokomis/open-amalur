# Two-draw native matrix evidence audit

## Result

The exported world matrices are correct for the bounded pair: known draw **68811** and unmatched draw **69284**. Both transforms were independently reconstructed from the recording's descriptor layout, descriptor writes, current descriptor bind, dynamic offsets, bound buffer allocation and captured memory data. All sixteen exported world-matrix floats match the actual shader binding **bit for bit**. Neither draw uses instancing or a base-vertex offset that could hide another placement.

This rejects wrong dynamic-offset selection or stale mapped-memory data as the explanation for these two cases. It does **not** validate all 51 unmatched poses, nor identify their source producer.

## Recorded resource and bindings

Recording SHA256: `72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209`.

| Field | Known 68811 | Unmatched 69284 |
|---|---:|---:|
| Graphics pipeline / VS module | 8194 / 877 | 12356 / 903 |
| Current descriptor bind event | 68809 | 69282 |
| Descriptor set / set layout | 13920 / 7974 | 15098 / 12354 |
| Dynamic binding order | 0,1,2,4,64,65,68 | 0,1,2,4,64,68 |
| Vertex world binding | 68 | 68 |
| Buffer / bound allocation | 51 / 52 | 51 / 52 |
| Effective world-block byte offset | 1162816 | 1226816 |
| Bound block range | 256 | 256 |
| Translation X | 506.4974365234375 | -880.2670288085938 |
| Translation Y | -79625.0703125 | -76023.859375 |
| Translation Z | 5574.79833984375 | 5371.81640625 |
| Index count | 234 | 11172 |
| Instance count / first instance | 1 / 0 | 1 / 0 |
| First index / vertex offset | 0 / 0 | 0 / 0 |
| Position vertex buffer | 11824 | 11696 |
| Index buffer | 11826 | 11698 |

Buffer51 is bound to allocation52 at memoryOffset0. Each relevant descriptor's static offset is0. Binding4 aliases binding68 at the same effective offset. The descriptor writes are complete before command recording; no later update replaces either selected set. Sorting dynamic bindings by binding number is correct here, even though the captured layout's pBindings array lists vertex bindings before fragment bindings.

## Shader consumption

`module-903.spvasm`: `%29` is set0/binding68. It computes clip position from rows8..11, then computes world position from rows0..3. In particular, world translation is loaded by `%128 = OpAccessChain ... %29 ... %uint_3` and added by `%130`. Position input is location0; no InstanceIndex/VertexIndex builtin exists in this module.

`module-877.spvasm`: `%45` is set0/binding68. It computes clip position from rows8..11 (access chains `%186/%192/%200/%207`), and world position from rows0..3 (`%218/%226/%237/%248`). Its local leaf wind adjustment occurs before those transforms. This is not an instance-array lookup, and does not substitute another world matrix. No InstanceIndex/VertexIndex builtin exists.

As a separate consistency check, reconstructing `inverse(world) * worldViewProjection` gives the same camera matrix for both draws: maximum linear-part difference **2.18544e-8**. Translation-row differences are at most **0.001036** world/clip coefficient units, consistent with inversion of individually rounded float32 composed matrices. Thus the separately stored world and clip matrices also agree with each other.

## Mapped-memory timing

The raw binary recording contains exactly **one** FillMemory record for allocation52:

- block73631, file offset525920194;
- compressed stored size10516740, uncompressed size33554432;
- allocation offset0, covering the full32MB;
- decompressed SHA256 `a9433c481e510e8777abfaa9105019d735e66551125b7fb083deac6ea9e3befd`.

This fill follows **vkEndCommandBuffer73630** and precedes **vkQueueSubmit76331**, which submits command buffer46 containing both draws. The original capture extractor's use of the last allocation52 fill is therefore correct for this pair: it is also the only fill. Reading UBO data at draw-recording time would be wrong; the recorded pre-submission memory update is the relevant state.

The independently decompressed bytes equal the existing memory-52.bin byte for byte. No recorded vkCmdCopyBuffer/UpdateBuffer/FillBuffer/CopyImageToBuffer writes target buffer51. Buffer51 was created with usage17 (TRANSFER_SRC|UNIFORM_BUFFER), with no storage-buffer or transfer-destination usage.

## Exporter review and limitations

Existing `oa-analyze-camera.py` computes UBO addresses as bound allocation offset + descriptor static offset + dynamic offset. For these draws, its single-current-bind handling is sufficient: firstSet0, descriptorSetCount1, graphics bind point, and all dynamic bindings supplied. More general Vulkan patterns involving retained sets at other firstSet values are outside this audit.

Existing `oa-extract-uniforms.py` takes the last fill for memory52; the raw one-fill timing check above validates that choice here. The independent audit does not use capture-index.json to find/decompress the fill; it walks the recording's raw blocks again.

The script that later adds the world_matrix_row_major field has not yet been located in the inspected Windows work Python files. Its output is independently verified against raw bytes, so this provenance gap does not change the two-draw result. No new engine decompilation, GPU replay, live launch, source edit or asset mutation was performed.

`native-gbuffer-draws.json` is a two-draw snapshot of the existing export; its original full-file identity is retained in `export-input-provenance.json`.

Files: `audit_matrices.py` reproduces address and raw-memory validation; `matrix-evidence.json` records exact events/results; `draw-*-binding68.bin` preserves the consumed UBO blocks; `raw-bindings.json` retains descriptor/resource setup; the two shader disassemblies and existing source extractors preserve the inspected implementation evidence.

## Producer clarification received after the audit

The foliage exporter author confirms native-gbuffer-draws.json was generated by a one-off Mac Python tool cell, not a saved script. It consumed phase97 capture-index.json draws/uniforms, tracked vertex/index binds per command buffer through JSONL, and read world_matrix_row_major as the first16 float32 values at binding68 effective offset. No extra transform or transpose was applied. The original one-off cell is not retained as a script; the independent raw two-draw verification remains the reproducible proof.
