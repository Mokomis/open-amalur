from pathlib import Path
import difflib,json
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark');src=r/'src';backup=r/'upstream-before-timing-fix'
changes={}
def edit(name,fn):
 p=src/name;old=p.read_text();new=fn(old)
 assert new!=old,name
 b=backup/name;b.parent.mkdir(parents=True,exist_ok=True)
 if b.exists():raise RuntimeError('Patch already attempted; refusing to overwrite backup '+name)
 b.write_text(old);p.write_text(new);changes[name]=(old,new)
def app(s):
 s=s.replace('    bool pre_frame_processed = false;','    bool pre_frame_processed = false;\n    uint64_t next_loop_measurement_frame = 0;')
 s=s.replace('                frame_loop_info_->SetLooping(true);','                frame_loop_info_->SetLooping(true);\n                next_loop_measurement_frame = frame_number;')
 start=s.index('void Application::Run()');end=s.index('\n}',start)+2
 body=s[start:end]
 needle='            if (fps_info_ != nullptr)\n'
 assert body.count(needle)==2
 body=body.replace(needle,'            // Capture position is restored by the loop; profiling counts actual plays.\n            const uint64_t timing_frame = frame_loop_info_ && frame_loop_info_->IsLooping()\n                ? next_loop_measurement_frame++ : frame_number;\n\n'+needle,1)
 for name in ['ShouldQuit','ShouldWaitIdleBeforeFrame','ShouldPreloadFrames','BeginFrame','EndFrame','ShouldWaitIdleAfterFrame']:
  body=body.replace('fps_info_->'+name+'(frame_number)','fps_info_->'+name+'(timing_frame)')
 return s[:start]+body+s[end:]
def header(s):
 s=s.replace('    void                   EndFile(uint64_t end_file_processor_frame);','    void                   EndFile(uint64_t end_file_processor_frame);\n    uint64_t GetLastCompletedFrame() const { return last_completed_frame_; }')
 return s.replace('    uint64_t start_time_;','    uint64_t last_completed_frame_{ 0 };\n    uint64_t start_time_;')
def cpp(s):return s.replace('void FpsInfo::EndFrame(uint64_t frame)\n{','void FpsInfo::EndFrame(uint64_t frame)\n{\n    last_completed_frame_ = frame;')
def main(s):
 start=s.index('    // Add one so that it matches the trim range frame number semantic.')
 end=s.index('\n    else if (file_processor_out->GetErrorState()',start)
 body=s[start:end]
 body=body.replace('    // Add one so that it matches the trim range frame number semantic.','    // Looping restores the capture position. Use the number of completed plays\n    // for timing/reporting, while retaining the file processor for error state.\n    const uint64_t completed_frames = fps_info.GetLastCompletedFrame();\n    // End is exclusive, matching measurement range semantics.')
 body=body.replace('file_processor_out->GetCurrentFrameNumber()', 'completed_frames')
 return s[:start]+body+s[end:]
edit('framework/application/application.cpp',app)
edit('framework/graphics/fps_info.h',header)
edit('framework/graphics/fps_info.cpp',cpp)
edit('tools/replay/replay_main_common.cpp',main)
patch=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items())
(r/'loop-measurement-counter.patch').write_text(patch)
print(patch)
