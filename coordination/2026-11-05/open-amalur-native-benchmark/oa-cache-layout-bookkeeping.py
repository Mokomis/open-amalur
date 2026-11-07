from pathlib import Path
import difflib
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark');p=r/'src/framework/decode/vulkan_replay_frame_loop_consumer.cpp';o=p.read_text();s=o
needle='    RecordBufferStates();';assert s.count(needle)==1
s=s.replace(needle,'    // Frozen host buffers never need snapshot restoration.\n    if (!oa_static_memory_) RecordBufferStates();')
needle='        GetImageTracking(device_id).RecordInitialState(image_ids, device_restorable_images[device_id]);';assert s.count(needle)==1
s=s.replace(needle,'    // In fixed-resource mode, track layouts but allocate no unused shadow images.\n        GetImageTracking(device_id).RecordInitialState(\n            image_ids, oa_static_resources_ ? std::vector<format::HandleId>{} : device_restorable_images[device_id]);')
needle='        it->second.RestoreLayoutsOnly(queue);';assert s.count(needle)==1
s=s.replace(needle,'        // With no shadow images, upstream Restore caches layout-only barriers.\n        // Reuse that cache instead of rescanning every texture on every frame.\n        it->second.Restore(queue);')
b=r/'before-layout-cache';b.mkdir(exist_ok=True);assert not (b/'vulkan_replay_frame_loop_consumer.cpp').exists();(b/'vulkan_replay_frame_loop_consumer.cpp').write_text(o);p.write_text(s)
(r/'cached-layout-bookkeeping.patch').write_text(''.join(difflib.unified_diff(o.splitlines(True),s.splitlines(True),fromfile='a/framework/decode/vulkan_replay_frame_loop_consumer.cpp',tofile='b/framework/decode/vulkan_replay_frame_loop_consumer.cpp')))
print('Cached mode now avoids unused buffer/image snapshots and uses upstream cached layout barriers.')
