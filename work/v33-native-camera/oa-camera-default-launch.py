from pathlib import Path
import shutil,difflib
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v33-native-camera');p=r/'src/tools/replay/android_main.cpp';old=p.read_text();s=old
needle='    gfxrecon::replay::LoadFeatures(g_features);';assert s.count(needle)==1
s=s.replace(needle,'''    // This dedicated app is useful directly from its launcher, without host intent arguments.
    std::string args = gfxrecon::util::GetIntentExtra(app, kArgsExtentKey);
    if(args.empty()) {
        const std::string base=app->activity->internalDataPath;
        args="--loop-frame 1 --remove-unsupported --memory-translation rebind --opcd --log-file "+base+"/camera-default.log "+base+"/dalentarth.gfxr";
        setenv("OA_CAMERA","1",1);setenv("OA_STATIC_MEMORY","2",1);
        FILE* control=std::fopen((base+"/camera.txt").c_str(),"w");
        if(control) {std::fputs("0 0 0 0\\n",control);std::fclose(control);}
    }
'''+needle)
needle='    const std::string args      = gfxrecon::util::GetIntentExtra(app, kArgsExtentKey);';assert s.count(needle)==1;s=s.replace(needle,'')
needle='    if (oa_camera::Enabled() && AInputEvent_getType(event)==AINPUT_EVENT_TYPE_MOTION) {';assert s.count(needle)==1
s=s.replace(needle,'''    if(oa_camera::Enabled() && AInputEvent_getType(event)==AINPUT_EVENT_TYPE_KEY && AKeyEvent_getAction(event)==AKEY_EVENT_ACTION_DOWN) {
        bool handled=true;
        switch(AKeyEvent_getKeyCode(event)) {
            case AKEYCODE_DPAD_UP:case AKEYCODE_W:oa_camera::pose.forward+=20;break;
            case AKEYCODE_DPAD_DOWN:case AKEYCODE_S:oa_camera::pose.forward-=20;break;
            case AKEYCODE_DPAD_LEFT:case AKEYCODE_A:oa_camera::pose.right-=20;break;
            case AKEYCODE_DPAD_RIGHT:case AKEYCODE_D:oa_camera::pose.right+=20;break;
            case AKEYCODE_R:oa_camera::pose={};break;
            default:handled=false;break;
        }
        if(handled) {oa_camera::Clamp();GFXRECON_LOG_INFO("OA CAMERA KEY yaw=%f pitch=%f right=%f forward=%f",oa_camera::pose.yaw,oa_camera::pose.pitch,oa_camera::pose.right,oa_camera::pose.forward);return 1;}
    }
    if (oa_camera::Enabled() && AInputEvent_getType(event)==AINPUT_EVENT_TYPE_MOTION && (AInputEvent_getSource(event)&AINPUT_SOURCE_CLASS_POINTER)) {''')
backup=r/'before-camera-default-launch';backup.mkdir(exist_ok=False);shutil.copyfile(p,backup/p.name);p.write_text(s)
(r/'camera-default-launch.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='a/tools/replay/android_main.cpp',tofile='b/tools/replay/android_main.cpp')))
print('Launcher now opens private native scene directly. Arrows/WASD move camera; R resets. Raw benchmark args remain supported.')
