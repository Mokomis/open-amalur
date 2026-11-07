from pathlib import Path
import difflib
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark');src=r/'src';backup=r/'before-static-memory';changes={}
def edit(name,fn):
 p=src/name;old=p.read_text();new=fn(old);assert new!=old,name
 b=backup/name;b.parent.mkdir(parents=True,exist_ok=True)
 if b.exists():raise RuntimeError('Refusing second patch application')
 b.write_text(old);p.write_text(new);changes[name]=(old,new)
def android(s):
 needle='    gfxrecon::replay::LoadFeatures(g_features);'
 assert s.count(needle)==1
 return s.replace(needle,'    // Explicit benchmark-only mode: freeze host buffer contents after the first play.\n    const auto oa_static = gfxrecon::util::GetIntentExtra(app, "oa_static_memory");\n    setenv("OA_STATIC_MEMORY", oa_static == "1" ? "1" : "0", 1);\n\n'+needle)
def header(s):
 s=s.replace('#include <utility>','#include <utility>\n#include <cstdlib>')
 needle='        frame_loop_info_(frame_loop_info)\n    {}'
 assert needle in s
 s=s.replace(needle,'        frame_loop_info_(frame_loop_info)\n    {\n        const char* frozen = std::getenv("OA_STATIC_MEMORY");\n        oa_static_memory_ = frozen && frozen[0] == \'1\';\n    }')
 needle='    virtual void ProcessStateEndMarker(uint64_t frame_number) override;'
 s=s.replace(needle,needle+'\n\n    void ProcessFillMemoryCommand(uint64_t memory_id, uint64_t offset, uint64_t size, const uint8_t* data) override;')
 needle='    graphics::FrameLoopInfo& frame_loop_info_;'
 assert s.count(needle)==1
 return s.replace(needle,needle+'\n    bool oa_static_memory_{ false };\n    uint64_t oa_skipped_fill_calls_{ 0 };\n    uint64_t oa_skipped_fill_bytes_{ 0 };\n    uint64_t oa_skipped_buffer_restores_{ 0 };')
def impl(s):
 needle='VulkanReplayFrameLoopConsumer::~VulkanReplayFrameLoopConsumer()\n{'
 assert needle in s
 s=s.replace(needle,needle+'\n    if (oa_static_memory_)\n    {\n        GFXRECON_LOG_INFO("OA STATIC MEMORY: skipped fills=%llu bytes=%llu buffer-restores=%llu",\n            static_cast<unsigned long long>(oa_skipped_fill_calls_),\n            static_cast<unsigned long long>(oa_skipped_fill_bytes_),\n            static_cast<unsigned long long>(oa_skipped_buffer_restores_));\n    }')
 needle='void VulkanReplayFrameLoopConsumer::FixupDeviceBuffers(format::HandleId device)\n{'
 assert needle in s
 s=s.replace(needle,needle+'\n    // Frozen-scene benchmark: do not restore pre-frame buffer data after first play.\n    // Image/layout, fence, event and semaphore fixups retain upstream behavior.\n    if (oa_static_memory_) { ++oa_skipped_buffer_restores_; return; }')
 marker='VulkanReplayFrameLoopConsumer::~VulkanReplayFrameLoopConsumer()'
 function='''void VulkanReplayFrameLoopConsumer::ProcessFillMemoryCommand(uint64_t memory_id, uint64_t offset,
                                                              uint64_t size, const uint8_t* data)
{
    if (oa_static_memory_ && frame_loop_info_.IsRepetition())
    {
        ++oa_skipped_fill_calls_;
        oa_skipped_fill_bytes_ += size;
        return;
    }
    VulkanReplayFrameLoopConsumerBase::ProcessFillMemoryCommand(memory_id, offset, size, data);
}

'''
 return s.replace(marker,function+marker,1)
edit('tools/replay/android_main.cpp',android)
edit('framework/decode/vulkan_replay_frame_loop_consumer.h',header)
edit('framework/decode/vulkan_replay_frame_loop_consumer.cpp',impl)
(r/'static-memory-benchmark.patch').write_text(''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items()))
print('Static-memory mode is explicit and disabled by default. Raw replay path preserved.')
