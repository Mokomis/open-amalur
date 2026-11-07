from pathlib import Path
import shutil,difflib,json
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v33-native-camera');src=r/'src';rel=json.loads((r/'relative-projection-offsets.json').read_text());assert len(rel)==2
p=src/'framework/decode/vulkan_replay_frame_loop_consumer.cpp';old=p.read_text();start=old.index('    for(uint64_t off:oa_camera_offsets) {');end=old.index('    for(uint64_t off:oa_camera_records) {',start)
new='''    // Rebuild the captured object's projection from the same model/camera inputs as native0x00abc070.
    float absolute_before[16],relative_before[16],absolute_view[16],relative_view[16];
    std::memcpy(absolute_before,oa_camera_baseline_.data()+639296,64);
    std::memcpy(relative_before,oa_camera_baseline_.data()+3328,64);
    oa_camera::Transform(absolute_before,absolute_view,p);oa_camera::Transform(relative_before,relative_view,p);
    for(uint64_t off:oa_camera_offsets) {
        float model[16],after[16];std::memcpy(model,oa_camera_baseline_.data()+off-128,64);
        const bool relative=off==REL0 || off==REL1;
        oa_matrix_mul_abc070(after,relative?relative_view:absolute_view,model);
        std::memcpy(oa_camera_upload_.data()+off,after,64);
    }
'''.replace('REL0',str(rel[0])).replace('REL1',str(rel[1]))
s=old[:start]+new+old[end:];backup=r/'before-native-projection-rebuild';backup.mkdir(exist_ok=False);shutil.copyfile(p,backup/p.name);p.write_text(s)
(r/'native-projection-rebuild.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='a/framework/decode/vulkan_replay_frame_loop_consumer.cpp',tofile='b/framework/decode/vulkan_replay_frame_loop_consumer.cpp')))
print('1598 projections now rebuilt from original model and camera inputs through recovered native matrix kernel')
