from pathlib import Path
import json,shutil,difflib
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v33-native-camera');src=r/'src';backup=r/'before-shared-camera';backup.mkdir(exist_ok=False);changes={}
def edit(name,new):
 p=src/name;old=p.read_text();assert new!=old;(backup/name).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,backup/name);p.write_text(new);changes[name]=(old,new)
# The portable recovered kernel has passed original x86 and ARM64 output comparison.
shutil.copyfile(r/'oa_recovered_matrix.h',src/'framework/util/oa_recovered_matrix.h')
p=src/'framework/util/oa_camera_control.h';s=p.read_text().replace('#include <algorithm>','#include <algorithm>\n#include "oa_recovered_matrix.h"');s=s.replace('inline void Transform(const float* src,float* dst,const Pose& p)', 'inline void DirectTransform(const float* src,float* dst,const Pose& p)')
# Insert before namespace closing, retaining DirectTransform as an independent diagnostic oracle.
end=s.rfind('\n}');assert end>0
s=s[:end]+'''
inline bool IsZero(const Pose& p) {return p.yaw==0 && p.pitch==0 && p.right==0 && p.forward==0;}
inline void Transform(const float* src,float* dst,const Pose& p) {
 if(IsZero(p)) {std::memcpy(dst,src,64);return;}
 const float identity[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};float delta[16];
 DirectTransform(identity,delta,p);
 oa_matrix_mul_abc070(dst,delta,src);
}
inline void TransformShared(const float* src,float* dst,const Pose& p) {
 std::memcpy(dst,src,144);if(IsZero(p))return;
 Transform(src,dst,p);
 constexpr double fx=1.311106091287448,fy=2.330855274807898;
 const double cy=std::cos(p.yaw),sy=std::sin(p.yaw),cp=std::cos(p.pitch),sp=std::sin(p.pitch);
 for(int i=0;i<3;++i) {
  const double right=src[i*4]/fx,up=src[i*4+1]/fy,forward=src[i*4+3];
  dst[16+i]=static_cast<float>(src[16+i]+p.right*right+p.forward*forward);
  dst[20+i]=static_cast<float>(sp*up+cp*(sy*right+cy*forward));
 }
}
'''+s[end:]
edit('framework/util/oa_camera_control.h',s)
records=json.loads((r/'shared-camera-records.json').read_text());offsets=sorted(v['offset'] for v in records);needed=max(offsets)+144;data=(r/'memory-52-prefix-v7.bin').read_bytes();assert len(data)==needed
hash_value=14695981039346656037
for byte in data:hash_value=((hash_value^byte)*1099511628211)&((1<<64)-1)
p=src/'framework/decode/oa_camera_offsets.inc';s=p.read_text()+'\nstatic constexpr uint64_t oa_camera_records[]={'+','.join(map(str,offsets))+'};\n';edit('framework/decode/oa_camera_offsets.inc',s)
p=src/'framework/decode/vulkan_replay_frame_loop_consumer.cpp';s=p.read_text();old='constexpr size_t needed=1763904+64;';assert old in s;s=s.replace(old,'constexpr size_t needed='+str(needed)+';')
import re
s=re.sub(r'if\(hash!=\d+ull\)',f'if(hash!={hash_value}ull)',s)
needle='    VulkanReplayFrameLoopConsumerBase::ProcessFillMemoryCommand(52,0,oa_camera_upload_.size(),oa_camera_upload_.data());';assert s.count(needle)==1
s=s.replace(needle,'''    for(uint64_t off:oa_camera_records) {
        float before[36],after[36];std::memcpy(before,oa_camera_baseline_.data()+off,144);
        oa_camera::TransformShared(before,after,p);std::memcpy(oa_camera_upload_.data()+off,after,144);
    }
'''+needle)
s=s.replace('OA CAMERA applied matrices=%zu yaw=', 'OA CAMERA applied matrices=%zu shared-records=%zu yaw=').replace('sizeof(oa_camera_offsets)/sizeof(oa_camera_offsets[0]),p.yaw','sizeof(oa_camera_offsets)/sizeof(oa_camera_offsets[0]),sizeof(oa_camera_records)/sizeof(oa_camera_records[0]),p.yaw')
edit('framework/decode/vulkan_replay_frame_loop_consumer.cpp',s)
(r/'shared-camera-and-native-kernel.patch').write_text(''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items()))
print('Prepared',len(offsets),'shared camera records and native matrix kernel; prefix bytes',needed)
