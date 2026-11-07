from pathlib import Path
import shutil,difflib
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v36-native-ranges');src=r/'src';prev=r.parent/'v35-native-geometry/src';assert not src.exists();shutil.copytree(prev,src)
for n in ['oa_geometry_sparse.h','oa_geometry_sparse.c','oa_geometry_kind1.h','oa_geometry_kind1.c','oa_native_geometry.h','oa_native_geometry.cpp','oa_geometry1_fixture.inc','oa_palette_fixture.inc']:shutil.copyfile(r/n,src/'framework/decode'/n)
p=src/'framework/decode/CMakeLists.txt';s=p.read_text();p.write_text(s+'\ntarget_sources(gfxrecon_decode PRIVATE ${CMAKE_CURRENT_LIST_DIR}/oa_geometry_kind1.c)\n')
p=src/'framework/decode/vulkan_replay_frame_loop_consumer.h';s=p.read_text();marker='    OaNativeGeometryBridge oa_native_geometry_;';assert marker in s;s=s.replace(marker,marker+'\n    int oa_palette_last_=-1;');p.write_text(s)
p=src/'framework/decode/vulkan_replay_frame_loop_consumer.cpp';s=p.read_text();s=s.replace('if(std::memcmp(current,oa_camera_last_,sizeof(current))==0)return;','''int palette=0;FILE*pf=std::fopen("/data/user/0/org.openamalur.nativebenchmark/files/palette.txt","r");if(pf){int value=0;if(std::fscanf(pf,"%d",&value)==1&&value==1)palette=1;std::fclose(pf);}
    if(std::memcmp(current,oa_camera_last_,sizeof(current))==0&&palette==oa_palette_last_)return;''')
s=s.replace('    VulkanReplayFrameLoopConsumerBase::ProcessFillMemoryCommand(52,0,oa_camera_upload_.size(),oa_camera_upload_.data());','    oa_native_geometry_.ApplyPalette(oa_camera_upload_.data(),oa_camera_upload_.size(),palette);oa_palette_last_=palette;\n    VulkanReplayFrameLoopConsumerBase::ProcessFillMemoryCommand(52,0,oa_camera_upload_.size(),oa_camera_upload_.data());')
p.write_text(s)
print('Prepared isolatedv36, preservingv35 source/build/APK')
