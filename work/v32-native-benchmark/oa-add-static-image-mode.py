from pathlib import Path
import difflib
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark');src=r/'src';backup=r/'before-static-images';changes={}
def edit(n,fn):
 p=src/n;o=p.read_text();s=fn(o);assert s!=o,n;b=backup/n;b.parent.mkdir(parents=True,exist_ok=True);assert not b.exists();b.write_text(o);p.write_text(s);changes[n]=(o,s)
def main(s):return s.replace('setenv("OA_STATIC_MEMORY", oa_static == "1" ? "1" : "0", 1);','setenv("OA_STATIC_MEMORY", oa_static == "2" ? "2" : (oa_static == "1" ? "1" : "0"), 1);')
def header(s):
 s=s.replace("oa_static_memory_ = frozen && frozen[0] == '1';","oa_static_memory_ = frozen && (frozen[0] == '1' || frozen[0] == '2');\n        oa_static_resources_ = frozen && frozen[0] == '2';")
 s=s.replace('        void Restore(format::HandleId queue);','        void Restore(format::HandleId queue);\n        void RestoreLayoutsOnly(format::HandleId queue);')
 return s.replace('    bool oa_static_memory_{ false };','    bool oa_static_memory_{ false };\n    bool oa_static_resources_{ false };\n    uint64_t oa_layout_only_restores_{ 0 };')
def impl(s):
 s=s.replace('    ResetBufferTracking();\n    ResetImageTracking();\n}', '    if (oa_static_resources_) GFXRECON_LOG_INFO("OA STATIC IMAGES: layout-only restores=%llu", static_cast<unsigned long long>(oa_layout_only_restores_));\n    ResetBufferTracking();\n    ResetImageTracking();\n}',1)
 needle='    it->second.Restore(queue);'
 assert s.count(needle)==1
 s=s.replace(needle,'    if (oa_static_resources_)\n    {\n        ++oa_layout_only_restores_;\n        it->second.RestoreLayoutsOnly(queue);\n    }\n    else\n    {\n        it->second.Restore(queue);\n    }')
 needle='void VulkanReplayFrameLoopConsumer::ImageTracking::Restore(format::HandleId queue)'
 method='''// Fixed-scene benchmark only: retain layouts but do not recopy image contents.
void VulkanReplayFrameLoopConsumer::ImageTracking::RestoreLayoutsOnly(format::HandleId queue)
{
    std::vector<VkImageMemoryBarrier> barriers;
    for (auto& [image_id, state] : image_states_)
    {
        VulkanImageInfo* info = object_table_.GetVkImageInfo(image_id);
        if (!info || info->handle == VK_NULL_HANDLE) continue;
        const size_t before = barriers.size();
        AppendImageLayoutBarriers(info, state.initial_layouts, barriers);
        if (barriers.size() != before)
        {
            info->subresource_layouts = state.initial_layouts;
            info->intermediate_layout = barriers.back().newLayout;
        }
    }
    if (barriers.empty()) return;
    VulkanDeviceInfo* device = object_table_.GetVkDeviceInfo(device_id_);
    VulkanQueueInfo* qi = object_table_.GetVkQueueInfo(queue);
    GFXRECON_ASSERT(device && qi);
    TemporaryCommandBuffer cmd(*device, device_table_);
    if (cmd.CreateAndBegin(qi->family_index, qi->handle) != VK_SUCCESS) return;
    CmdImageLayoutBarriers(device_table_, cmd.command_buffer, barriers);
    CHECK_VK_RESULT(cmd.SubmitAndDestroy(), "Static scene layout restore");
}

'''
 assert needle in s
 return s.replace(needle,method+needle,1)
edit('tools/replay/android_main.cpp',main);edit('framework/decode/vulkan_replay_frame_loop_consumer.h',header);edit('framework/decode/vulkan_replay_frame_loop_consumer.cpp',impl)
(r/'static-image-benchmark.patch').write_text(''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items()))
print('Mode2 skips snapshot image copies, preserves layout transitions and synchronization. Default/raw mode unchanged.')
