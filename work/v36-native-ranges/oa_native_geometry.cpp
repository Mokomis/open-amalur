#include "decode/oa_native_geometry.h"
#include "util/logging.h"
#include <cstdlib>
#include <cstring>
namespace gfxrecon { namespace decode {
#include "oa_geometry_fixture.inc"
#include "oa_geometry1_fixture.inc"
#include "oa_palette_fixture.inc"
namespace {
uint32_t U32(const uint8_t*p){return uint32_t(p[0])|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24);}
bool DecodeFixture(oa_geometry0&out){
 const auto*b=oa_geometry_fixture;const size_t size=sizeof(oa_geometry_fixture);if(size!=548||U32(b)!=0x5053414f||U32(b+4)!=1||U32(b+8)!=6)return false;
 oa_guest_span spans[6];size_t pos=80;
 for(auto&s:spans){if(pos+8>size)return false;s.base=U32(b+pos);s.size=U32(b+pos+4);pos+=8;if(s.size>size-pos)return false;s.bytes=b+pos;pos+=s.size;}
 if(pos!=size)return false;oa_guest_memory memory{spans,6};return oa_decode_geometry0_sparse(&memory,U32(b+12),U32(b+16),U32(b+20),&out)!=0;
}
bool DecodeFixture1(oa_geometry1&out){
 const auto*b=oa_geometry1_fixture;const size_t size=sizeof(oa_geometry1_fixture);if(size!=596||U32(b)!=0x314b414f||U32(b+4)!=1||U32(b+8)!=7)return false;
 oa_guest_span spans[7];size_t pos=80;
 for(auto&s:spans){if(pos+8>size)return false;s.base=U32(b+pos);s.size=U32(b+pos+4);pos+=8;if(s.size>size-pos)return false;s.bytes=b+pos;pos+=s.size;}
 if(pos!=size)return false;oa_guest_memory memory{spans,7};return oa_decode_geometry1_sparse(&memory,U32(b+12),U32(b+16),U32(b+20),&out)!=0;
}
struct Submission {uint32_t vb[2]{},stride[2]{},offset[2]{},topology{},ib{},format{},index_offset{},count{},first{};int32_t base{};unsigned calls{};bool indexed{};};
void Vertices(void*c,const uint32_t b[2],const uint32_t s[2],const uint32_t o[2]){auto&r=*static_cast<Submission*>(c);std::memcpy(r.vb,b,8);std::memcpy(r.stride,s,8);std::memcpy(r.offset,o,8);++r.calls;}
void Topology(void*c,uint32_t t){auto&r=*static_cast<Submission*>(c);r.topology=t;++r.calls;}
void Indices(void*c,uint32_t b,uint32_t f,uint32_t o){auto&r=*static_cast<Submission*>(c);r.ib=b;r.format=f;r.index_offset=o;++r.calls;}
void Indexed(void*c,uint32_t n,uint32_t f,int32_t b){auto&r=*static_cast<Submission*>(c);r.count=n;r.first=f;r.base=b;r.indexed=true;++r.calls;}
void Draw(void*c,uint32_t n,uint32_t f){auto&r=*static_cast<Submission*>(c);r.count=n;r.first=f;++r.calls;}
}
OaNativeGeometryBridge::OaNativeGeometryBridge(){const char*p=std::getenv("OA_ENGINE_GEOMETRY");enabled_=p&&p[0]=='1';if(enabled_){decoded_=DecodeFixture(geometry_);decoded1_=DecodeFixture1(geometry1_);GFXRECON_LOG_INFO("OA NATIVE RANGES enabled decoded=%d targets=63022,65558,68129,68131",int(decoded1_));GFXRECON_LOG_INFO("OA NATIVE GEOMETRY enabled decoded=%d target-block=69921",int(decoded_));}}
OaNativeGeometryBridge::~OaNativeGeometryBridge(){if(enabled_)GFXRECON_LOG_INFO("OA NATIVE RANGES replacements=%llu rejections=%llu palette-copies=%llu",(unsigned long long)replacements1_,(unsigned long long)rejections1_,(unsigned long long)palette_copies_);if(enabled_)GFXRECON_LOG_INFO("OA NATIVE GEOMETRY replacements=%llu rejections=%llu",static_cast<unsigned long long>(replacements_),static_cast<unsigned long long>(rejections_));}
bool OaNativeGeometryBridge::ApplyPalette(uint8_t*data,size_t size,int pose){
 if(!enabled_||!decoded1_||!data||size<1055584||geometry1_.constant_count!=6||geometry1_.constant_address!=0x052a8260u||pose<0||pose>1)return false;
 constexpr size_t offsets[]={11712,356800,1050944,1055296};
 // All four passes consume the same recorded palette. Validate every destination before writing any.
 for(auto off:offsets)if(std::memcmp(data+off,oa_palette_capture,sizeof(oa_palette_capture)))return false;
 oa_guest_span span{geometry1_.constant_address,sizeof(oa_palette_capture),pose?oa_palette_live:oa_palette_capture};oa_guest_memory memory{&span,1};
 for(auto off:offsets)if(!oa_copy_instance_constants(&memory,geometry1_.constant_address,geometry1_.constant_count,data+off,size-off))return false;
 palette_copies_+=4;GFXRECON_LOG_INFO("OA NATIVE PALETTE copied6x48 bytes to4 passes pose=%d",pose);return true;
}
void OaNativeGeometryBridge::Begin(format::HandleId command){if(enabled_)bound_.erase(command);}
void OaNativeGeometryBridge::Track(const args::CmdBindVertexBuffers2&a){if(!enabled_)return;auto&b=bound_[a.commandBuffer];if(a.pBuffers.GetLength()<a.bindingCount||a.pOffsets.GetLength()<a.bindingCount||a.pStrides.GetLength()<a.bindingCount)return;for(uint32_t i=0;i<a.bindingCount;++i){uint32_t slot=a.firstBinding+i;if(slot<2){b.vb[slot]=a.pBuffers.GetPointer()[i];b.offset[slot]=a.pOffsets.GetPointer()[i];b.stride[slot]=a.pStrides.GetPointer()[i];}}}
void OaNativeGeometryBridge::Track(const args::CmdBindIndexBuffer&a){if(!enabled_)return;auto&b=bound_[a.commandBuffer];b.ib=a.buffer;b.ib_offset=a.offset;b.format=a.indexType;}
void OaNativeGeometryBridge::Track(const args::CmdBindPipeline&a){if(enabled_&&a.pipelineBindPoint==VK_PIPELINE_BIND_POINT_GRAPHICS)bound_[a.commandBuffer].pipeline=a.pipeline;}
bool OaNativeGeometryBridge::Rebuild(const ApiCallInfo&info,const args::CmdDrawIndexed&a,args::CmdDrawIndexed&out){
 if(!enabled_)return false;
 uint64_t pipeline=info.index==63022?13207:info.index==65558?13215:(info.index==68129||info.index==68131)?13338:0;
 if(pipeline){
  Submission s;oa_draw_backend backend{&s,Vertices,Topology,Indices,Indexed,Draw};bool submitted=decoded1_&&oa_submit_geometry1(&geometry1_,&backend);auto it=bound_.find(a.commandBuffer);
  bool native=submitted&&s.calls==4&&s.indexed&&s.vb[0]==0xaaad9890u&&s.vb[1]==0xaa902fb0u&&s.ib==0xaaad9728u&&s.stride[0]==60&&s.stride[1]==8&&s.topology==4&&s.format==57&&s.offset[0]==0&&s.offset[1]==0&&s.index_offset==0;
  bool resources=it!=bound_.end();if(resources){const auto&b=it->second;resources=b.vb[0]==7777&&b.vb[1]==1831&&b.ib==7779&&b.offset[0]==0&&b.offset[1]==0&&b.stride[0]==s.stride[0]&&b.stride[1]==s.stride[1]&&b.ib_offset==0&&b.format==VK_INDEX_TYPE_UINT16&&b.pipeline==pipeline;}
  bool arguments=a.commandBuffer==46&&a.instanceCount==1&&a.firstInstance==0&&a.indexCount==s.count&&a.firstIndex==s.first&&a.vertexOffset==s.base;
  if(!native||!resources||!arguments){++rejections1_;if(rejections1_==1)GFXRECON_LOG_ERROR("OA NATIVE RANGES guard rejected native=%d resources=%d arguments=%d",int(native),int(resources),int(arguments));return false;}
  out=a;out.indexCount=s.count;out.firstIndex=s.first;out.vertexOffset=s.base;++replacements1_;
  if(replacements1_<=4)GFXRECON_LOG_INFO("OA NATIVE RANGES submitted474 indices block=%llu pipeline=%llu",(unsigned long long)info.index,(unsigned long long)pipeline);return true;
 }
 if(info.index!=69921)return false;
 Submission s;oa_draw_backend backend{&s,Vertices,Topology,Indices,Indexed,Draw};const bool submitted=decoded_&&oa_submit_geometry0(&geometry_,&backend);auto it=bound_.find(a.commandBuffer);
 const bool native=submitted&&s.calls==4&&s.indexed&&s.vb[0]==0xaabc9270u&&s.vb[1]==0xaa902fb0u&&s.ib==0xaabca620u&&s.stride[0]==28&&s.stride[1]==28&&s.topology==4&&s.format==57&&s.offset[0]==0&&s.offset[1]==0&&s.index_offset==0;
 bool resources=it!=bound_.end();if(resources){const auto&b=it->second;resources=b.vb[0]==3704&&b.vb[1]==1831&&b.ib==3706&&b.offset[0]==0&&b.offset[1]==0&&b.stride[0]==s.stride[0]&&b.stride[1]==s.stride[1]&&b.ib_offset==0&&b.format==VK_INDEX_TYPE_UINT16&&b.pipeline==13175;}
 const bool args_match=a.commandBuffer==46&&a.instanceCount==1&&a.firstInstance==0&&a.indexCount==s.count&&a.firstIndex==s.first&&a.vertexOffset==s.base;
 if(!native||!resources||!args_match){++rejections_;if(rejections_==1)GFXRECON_LOG_ERROR("OA NATIVE GEOMETRY guard rejected native=%d resources=%d arguments=%d",int(native),int(resources),int(args_match));return false;}
 out=a;out.indexCount=s.count;out.firstIndex=s.first;out.vertexOffset=s.base;++replacements_;
 if(replacements_==1)GFXRECON_LOG_INFO("OA NATIVE GEOMETRY submitted decoded packet: draw=%u buffers=3704,1831 index=3706 pipeline=13175",s.count);
 return true;
}
}}
