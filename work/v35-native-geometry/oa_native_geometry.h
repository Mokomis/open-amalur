#pragma once
#include "decode/api_decoder.h"
#include "generated/generated_vulkan_decoder_args.h"
#include "decode/oa_geometry_sparse.h"
#include <unordered_map>
#include <cstdint>
namespace gfxrecon { namespace decode {
class OaNativeGeometryBridge {
public:
 OaNativeGeometryBridge();~OaNativeGeometryBridge();
 void Begin(format::HandleId command);
 void Track(const args::CmdBindVertexBuffers2&);
 void Track(const args::CmdBindIndexBuffer&);
 void Track(const args::CmdBindPipeline&);
 bool Rebuild(const ApiCallInfo&,const args::CmdDrawIndexed&,args::CmdDrawIndexed&);
private:
 struct Bound {uint64_t vb[2]{},offset[2]{},stride[2]{},ib{},ib_offset{},pipeline{};VkIndexType format=VK_INDEX_TYPE_MAX_ENUM;};
 bool enabled_{false},decoded_{false};uint64_t replacements_{0},rejections_{0};oa_geometry0 geometry_{};
 std::unordered_map<format::HandleId,Bound> bound_;
};
}}
