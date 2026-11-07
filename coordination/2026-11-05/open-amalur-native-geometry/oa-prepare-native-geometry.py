from pathlib import Path
import shutil,difflib
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v35-native-geometry');prev=r.parent/'v33-native-camera';src=r/'src';assert not src.exists();shutil.copytree(prev/'src',src);changes={}
def edit(n,fn):
 p=src/n;old=p.read_text();new=fn(old);assert new!=old,n;p.write_text(new);changes[n]=(old,new)
for n in ['oa_native_geometry.h','oa_native_geometry.cpp','oa_geometry_sparse.h','oa_geometry_sparse.c','oa_geometry_fixture.inc']:shutil.copyfile(r/n,src/'framework/decode'/n)
def hdr(s):
 s=s.replace('#include "util/defines.h"','#include "util/defines.h"\n#include "decode/oa_native_geometry.h"')
 marker='    virtual void ProcessStateEndMarker(uint64_t frame_number) override;'
 text='\n'.join('    void Process_vk'+name+'(const ApiCallInfo&, args::'+name+'&) override;' for name in ['CmdBindVertexBuffers2','CmdBindIndexBuffer','CmdBindPipeline','CmdDrawIndexed'])
 s=s.replace(marker,marker+'\n'+text)
 marker='    graphics::FrameLoopInfo& frame_loop_info_;';assert marker in s
 return s.replace(marker,marker+'\n    OaNativeGeometryBridge oa_native_geometry_;')
def impl(s):
 marker='void VulkanReplayFrameLoopConsumer::Process_vkBeginCommandBuffer(const ApiCallInfo& call_info,\n                                                               args::BeginCommandBuffer& args)'
 # Preserve upstream spelling/spacing by selecting the exact function opening.
 idx=s.index('void VulkanReplayFrameLoopConsumer::Process_vkBeginCommandBuffer(');brace=s.index('{',idx);s=s[:brace+1]+'\n    oa_native_geometry_.Begin(args.commandBuffer);'+s[brace+1:]
 methods=''
 for n in ['CmdBindVertexBuffers2','CmdBindIndexBuffer','CmdBindPipeline']:
  methods+=f'\nvoid VulkanReplayFrameLoopConsumer::Process_vk{n}(const ApiCallInfo& info, args::{n}& args) {{ oa_native_geometry_.Track(args); VulkanReplayFrameLoopConsumerBase::Process_vk{n}(info,args); }}\n'
 methods+='''
void VulkanReplayFrameLoopConsumer::Process_vkCmdDrawIndexed(const ApiCallInfo& info, args::CmdDrawIndexed& args) {
    gfxrecon::decode::args::CmdDrawIndexed rebuilt{};
    if(oa_native_geometry_.Rebuild(info,args,rebuilt))VulkanReplayFrameLoopConsumerBase::Process_vkCmdDrawIndexed(info,rebuilt);
    else VulkanReplayFrameLoopConsumerBase::Process_vkCmdDrawIndexed(info,args);
}
'''
 idx=s.rfind('GFXRECON_END_NAMESPACE(decode)');assert idx>=0;return s[:idx]+methods+s[idx:]
def android(s):
 marker='    std::string args = gfxrecon::util::GetIntentExtra(app, kArgsExtentKey);';assert marker in s
 return s.replace(marker,'    setenv("OA_ENGINE_GEOMETRY", (gfxrecon::util::GetIntentExtra(app, "oa_native_geometry") == "1" || gfxrecon::util::GetIntentExtra(app, kArgsExtentKey).empty()) ? "1" : "0", 1);\n'+marker)
edit('framework/decode/vulkan_replay_frame_loop_consumer.h',hdr);edit('framework/decode/vulkan_replay_frame_loop_consumer.cpp',impl);edit('tools/replay/android_main.cpp',android)
edit('framework/decode/CMakeLists.txt',lambda s:s+'\ntarget_sources(gfxrecon_decode PRIVATE ${CMAKE_CURRENT_LIST_DIR}/oa_geometry_sparse.c ${CMAKE_CURRENT_LIST_DIR}/oa_native_geometry.cpp)\n')
(r/'native-geometry-bridge.patch').write_text(''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items()))
print('Prepared isolated v35 native geometry integration; v33 source/build preserved')
