from pathlib import Path
import shutil,difflib,json
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v33-native-camera');prev=r.parent/'v32-native-benchmark';src=r/'src'
assert not src.exists(),'Preserve existing v33 source; do not reapply'
shutil.copytree(prev/'src',src)
changes={}
def edit(n,fn):
 p=src/n;o=p.read_text();s=fn(o);assert s!=o,n;p.write_text(s);changes[n]=(o,s)
shutil.copyfile(r/'oa-camera-control.h',src/'framework/util/oa_camera_control.h')
j=json.loads((r/'camera-manifest.json').read_text());assert {m['memory'] for m in j['matrices']}=={52}
data=(r/'memory-52-prefix.bin').read_bytes();hash_value=14695981039346656037
for byte in data:hash_value=((hash_value^byte)*1099511628211)&((1<<64)-1)
text='static constexpr uint64_t oa_camera_expected_hash='+str(hash_value)+'ull;\n'+'// Generated from capture-index.json / camera-manifest.json. Capture-specific.\nstatic constexpr uint64_t oa_camera_offsets[]={'+','.join(str(m['offset']) for m in j['matrices'])+'};\n'
(src/'framework/decode/oa_camera_offsets.inc').write_text(text)
def main(s):
 s=s.replace('#include <cassert>','#include <cassert>\n#include "util/oa_camera_control.h"') if '#include <cassert>' in s else '#include "util/oa_camera_control.h"\n'+s
 needle='    gfxrecon::replay::LoadFeatures(g_features);';assert s.count(needle)==1
 s=s.replace(needle,'    setenv("OA_CAMERA", gfxrecon::util::GetIntentExtra(app, "oa_camera") == "1" ? "1" : "0", 1);\n'+needle)
 needle='int32_t ProcessInputEvent(struct android_app* app, AInputEvent* event)\n{';assert needle in s
 code='''
    if (oa_camera::Enabled() && AInputEvent_getType(event)==AINPUT_EVENT_TYPE_MOTION) {
        static float lastx=0,lasty=0,startx=0,starty=0;static bool moved=false;
        const int action=AMotionEvent_getAction(event)&AMOTION_EVENT_ACTION_MASK;
        const float x=AMotionEvent_getX(event,0),y=AMotionEvent_getY(event,0);
        if(action==AMOTION_EVENT_ACTION_DOWN) {lastx=startx=x;lasty=starty=y;moved=false;}
        else if(action==AMOTION_EVENT_ACTION_MOVE) {
            const float dx=x-lastx,dy=y-lasty;
            moved=moved || std::abs(x-startx)+std::abs(y-starty)>12;
            if(AMotionEvent_getPointerCount(event)>1) {oa_camera::pose.right-=dx;oa_camera::pose.forward-=dy;}
            else {oa_camera::pose.yaw-=dx*0.00035f;oa_camera::pose.pitch+=dy*0.00035f;}
            oa_camera::Clamp();lastx=x;lasty=y;
        } else if(action==AMOTION_EVENT_ACTION_UP) {
            if(!moved) oa_camera::pose={};
            GFXRECON_LOG_INFO("OA CAMERA TOUCH yaw=%f pitch=%f right=%f forward=%f",oa_camera::pose.yaw,oa_camera::pose.pitch,oa_camera::pose.right,oa_camera::pose.forward);
        }
        return 1;
    }
'''
 return s.replace(needle,needle+code)
def hdr(s):
 needle='    bool oa_static_memory_{ false };';assert needle in s
 return s.replace(needle,needle+'\n    std::vector<uint8_t> oa_camera_baseline_;\n    std::vector<uint8_t> oa_camera_upload_;\n    float oa_camera_last_[4]{ 1000,1000,1000,1000 };\n    void OaApplyCamera();')
def cpp(s):
 s='#include "util/oa_camera_control.h"\n'+s
 needle='    if (oa_static_memory_ && frame_loop_info_.IsRepetition())\n    {';assert s.count(needle)==1
 s=s.replace(needle,needle+'\n        if(oa_camera::Enabled() && memory_id==52 && offset==0) OaApplyCamera();')
 needle='    VulkanReplayFrameLoopConsumerBase::ProcessFillMemoryCommand(memory_id, offset, size, data);\n}'
 assert s.count(needle)==1
 s=s.replace(needle,'''    VulkanReplayFrameLoopConsumerBase::ProcessFillMemoryCommand(memory_id, offset, size, data);
    if(oa_camera::Enabled() && oa_static_resources_ && memory_id==52 && offset==0 && size==33554432) {
        // Require exact captured inputs at every selected matrix before admitting this capture-specific patch.
        constexpr size_t needed=1763904+64;
        uint64_t hash=14695981039346656037ull;for(size_t i=0;i<needed;++i)hash=(hash^data[i])*1099511628211ull;
        // The manifest is specific to one immutable captured resource image.
        if(hash!=OA_CAMERA_HASH_PLACEHOLDER) {GFXRECON_LOG_ERROR("OA CAMERA capture fingerprint mismatch; disabled");oa_camera_baseline_.clear();return;}
        oa_camera_baseline_.assign(data,data+needed);oa_camera_upload_=oa_camera_baseline_;
        for(float& v:oa_camera_last_)v=1000;
        GFXRECON_LOG_INFO("OA CAMERA initialized memory=52 bytes=%zu",needed);
        OaApplyCamera();
    }
}

#include "oa_camera_offsets.inc"
void VulkanReplayFrameLoopConsumer::OaApplyCamera() {
    if(oa_camera_baseline_.empty())return;
    auto p=oa_camera::Read();float current[4]={p.yaw,p.pitch,p.right,p.forward};
    if(std::memcmp(current,oa_camera_last_,sizeof(current))==0)return;
    // Always derive from immutable captured input; no cumulative matrix drift.
    oa_camera_upload_=oa_camera_baseline_;
    for(uint64_t off:oa_camera_offsets) {
        float before[16],after[16];std::memcpy(before,oa_camera_baseline_.data()+off,64);
        oa_camera::Transform(before,after,p);std::memcpy(oa_camera_upload_.data()+off,after,64);
    }
    VulkanReplayFrameLoopConsumerBase::ProcessFillMemoryCommand(52,0,oa_camera_upload_.size(),oa_camera_upload_.data());
    std::memcpy(oa_camera_last_,current,sizeof(current));
    GFXRECON_LOG_INFO("OA CAMERA applied matrices=%zu yaw=%f pitch=%f right=%f forward=%f",sizeof(oa_camera_offsets)/sizeof(oa_camera_offsets[0]),p.yaw,p.pitch,p.right,p.forward);
}''')
 return s.replace('OA_CAMERA_HASH_PLACEHOLDER',str(hash_value)+'ull')
edit('tools/replay/android_main.cpp',main);edit('framework/decode/vulkan_replay_frame_loop_consumer.h',hdr);edit('framework/decode/vulkan_replay_frame_loop_consumer.cpp',cpp)
(r/'native-camera.patch').write_text(''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items()))
print('Isolated v33 camera source prepared; v32 source preserved')
