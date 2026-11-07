# Barrel02 serialized FAB bind evidence

## Finding
For FAB1425589 descriptor0 / bone2, use the authored FAB quaternion conjugated for the port's standard column-vector rotation math. The resulting local transform is +15 degrees around Z, zero translation, unit scale. The current external2018 candidate is the opposite rotation. This is a forward pose transform, not an inverse-bind matrix operation.

This pass establishes serialized-FAB -> instance pose-buffer conversion/parent composition by exact native assembly and standalone execution of the original reviewed kernel. It does not claim an observed original-game draw, complete draw-path recovery, animation or general skinning correctness.

## Artifact identity
- Original cs:15032 koa.exe SHA256:16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314.
- Source FAB:work/v20-inputs/initial_0.pak/1425589.fab_bxml, SHA256:b51f2dfc5980dfc025ce5364ab36d9a9bb15ab018bf3db472f6a8738b4da2a39.
- Reused existing Ghidra exports in work/v30-engine/decomp; no database changes.

## Native data flow
1. BHG_FabInstanceRender::vf1 at00d35150 initializes a FAB instance. At00d351c2 it loads instance+0x184 scale, at00d351cd passes FabRender+4, at00d351d6 sets ECX=instance+0x34, at00d351d9 calls00cea2a0. This resolves the previously hidden destination argument.
2. 00cea2a0 reads source skeleton blob from (FabRender+4)+0x18 = FabRender+0x1c. It reads u16 count at blob+0x10, allocates/sets the 0x30-stride array at instance+0x34, and calls00c9a9b0 at00cea319 with the same array and FabRender+4.
3. 00c9a9b0 calls00c44f20 for each index. 00c44f39 loads the skeleton blob;00c44f42..49 resolve its relative transform pointer at blob+0x18. Index stride is0x30. Source+0x00..0x0f is quaternion XYZW; +0x10..0x1f position XYZW; +0x20..0x2b scale XYZ.00c44fa3 calls00adcd40 with that q,position,scale.
4. 00adcd40 copies position into internal+0, quaternion unchanged into internal+0x10, scale into internal+0x20, and sets active-component flags at+0x2c. Identity values are initialized by00aced20. There is no q sign change or inversion in this loader.
5. 00c9aa31..47 reads signed parents through blob+0x1c relative pointer. Invalid/negative parent copies local to world[i]. A valid parent calls00ac5770 with ECX=world[i], stack args world[parent], converted local. Thus the serialized pose reaches the exact instance buffer consumed by the existing00caf5f0 anchor.
6. 00caf645 reads descriptor+0x34 bone index;00caf652..660 copies instance pose at instance+0x34+bone*0x30.00caf665..671 calls00ac5770(destination, instance+0x124 world, selected bone pose), then applies descriptor+0x2c scalar through00ac56f0. This corroborates forward world-with-local composition, without an inverse-bind step in this path.
7. Descriptor reader00d196c0 allocates0x5c runtime records, reads serialized descriptor's last37 bytes into runtime+0x2c. For no-remap barrel this maps file412 bone index2 to runtime+0x34. File404 scalar=1 maps runtime+0x2c.

## Real barrel fields
- blob=file+4. Count=u16 at file20=4.
- Transform relative field=file28,value72,target100.
- Parent relative field=file32,value260,target292.
- Bone2 record=file196; q=(0,0,-0.13052602112293243,0.9914449453353882); position=(0,0,0,1); scale=(1,1,1,0).
- Bone2 parent=file296,u16=0. Bone0 is identity root with signed parent-1.
- Mesh descriptor0=file372; bone=file412,index2; zero remaps; scalar=file404=1.

## Native execution and independent comparison
barrel_native_pose.cpp is a new standalone harness adapted from the existing clip-bake private-image loader. It reserves/maps a private copy of the pinned executable; does not invoke its PE entrypoint, TLS, imports, original process, graphics/device path or UI. It supplies a preallocated4-entry pose array and small mock base object containing the real skeleton pointer to00c9a9b0, which invokes the exact conversion and parent-composition callees above. It then invokes original pure00ac3a70 on each resulting pose. The success path's callees were reviewed in saved pseudocode. Each run has isolated scratch globals. Build and run exit0; all4 bones output.

The original matrix uses row vectors. Transpose it before comparing with the parser's row-major storage / column-vector math. For bone2, native converted column-vector rotation is:

    [0.965925931930542, -0.25881871581077576, 0, 0]
    [0.25881871581077576, 0.965925931930542, 0, 0]
    [0, 0, 1, 0]
    [0, 0, 0, 1]

External2018 direct candidate max entry error=0.5176374435649187. Conjugating authored q (equivalently transposing the candidate's3x3 rotation only for THIS zero-translation unit-scale barrel) gives max entry error=1.6310910400108014e-8. A100-unit X point maps to approximately(96.5925932,25.8818716,0). Identity bones and translated bone3 agree with native as recorded in barrel-native-pose-result.json.

## Implementation recommendation and limits
Admit this one independently identified static/unskinned barrel using bone2 forward bind with conjugated authored quaternion and world placement composed afterward in the port convention. Preserve zero translation and unit scale. Do not apply the descriptor position as another translation: this pass does not identify it as a pose. Do not invert the full candidate matrix. Do not generalize the result to remap matrices, all FABs, nonuniform-scale hierarchy or animation.

The missing serialized-FAB-to-instance-buffer link is now answered. A full original draw-chain or actual game-frame observation remains separate:00caf5f0 has no direct callers in the saved pseudocode, and its result should be described as a native transform query/composition anchor rather than an observed draw. Candidate command builder00c92150 converts supplied transforms via00ac3a70, but this bounded pass did not establish every upstream pointer through those command builders. If policy requires a complete draw chain before admitting props, that remains the exact blocker; continue from per-element transform producer, not broad offset scans.

## Files and reproducibility
- native-bind-pseudocode.txt: exact saved exports.
- 00d35150-asm.txt and00d351c2-asm.txt: hidden this resolved.
- 00cea2a0-asm.txt,00c9a9b0-asm.txt,00c44f20-asm.txt,00adcd40-asm.txt,00caf5f0-asm.txt: raw native flow.
- build_barrel_native_pose.cmd,barrel_native_pose.cpp: isolated harness; native-pose-build.log/native-pose-run.log.
- barrel-native-pose-output.bin: count followed by each48-byte internal pose+64-byte matrix.
- barrel-native-pose-result.json: raw source fields, parser candidate, native output and errors.

All writes are confined to this new placement-research folder. No engine, packer, preview, original databases, game files, credentials, saves, worker or model settings were changed.

## Exact Windows reproduction

    cd /d "C:\Users\rwill\Documents\Opem Amalur\work\v43-scene-fidelity\placement-research"
    build_barrel_native_pose.cmd
    "C:\Users\rwill\AppData\Local\Programs\Python\Python312\python.exe" verify_barrel_native_pose.py --run

The verifier pins both SHA256 values and independently reconstructs standard quaternion rotation, comparing direct/conjugated results. Existing recorded output is read when--run is omitted;--run writes a separate recheck output.

To reproduce the isolated overlay from scratch in a new empty output scope, review build_barrel02_overlay.py. Its current barrel02-overlay output is intentionally protected from overwrite. Successful recorded build:16 placements,10 cells,31 files,10,176 triangles added per LOD. It reuses material299790/index255 and writes only index/cell files. barrel02-validation.json records unchanged original draw/vertex/index blocks and draw/index/bounds checks. This output is not deployed.
