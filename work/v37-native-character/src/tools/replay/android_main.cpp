#include "util/oa_camera_control.h"
/*
** Copyright (c) 2018-2020 Valve Corporation
** Copyright (c) 2018-2026 LunarG, Inc.
**
** Permission is hereby granted, free of charge, to any person obtaining a
** copy of this software and associated documentation files (the "Software"),
** to deal in the Software without restriction, including without limitation
** the rights to use, copy, modify, merge, publish, distribute, sublicense,
** and/or sell copies of the Software, and to permit persons to whom the
** Software is furnished to do so, subject to the following conditions:
**
** The above copyright notice and this permission notice shall be included in
** all copies or substantial portions of the Software.
**
** THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
** IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
** FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
** AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
** LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
** FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
** DEALINGS IN THE SOFTWARE.
*/

#include "replay_settings.h"
#include "replay_main_common.h"
#include "tool_feature_options.h"

#include "application/android_context.h"
#include "application/android_window.h"
#include "decode/file_processor.h"
#include "format/format.h"
#include "util/android/activity.h"
#include "util/android/intent.h"
#include "util/logging.h"
#include "util/platform.h"
#include "util/remote_channel.h"
#include "parse_dump_resources_cli.h"

#include <android/log.h>
#include <android/window.h>

#include <cstdlib>
#include <exception>
#include <memory>
#include <string>
#include <vector>

const char kArgsExtentKey[]      = "args";
const char kDefaultCaptureFile[] = "/sdcard/gfxrecon_capture" GFXRECON_FILE_EXTENSION;

const int32_t kSwipeDistance = 200;

void    ProcessAppCmd(struct android_app* app, int32_t cmd);
int32_t ProcessInputEvent(struct android_app* app, AInputEvent* event);

// Globals required by the extern "C" query callbacks called from outside this TU.
static std::unique_ptr<gfxrecon::decode::FileProcessor>                  g_file_processor;
static std::vector<std::unique_ptr<gfxrecon::replay::ReplayFeatureBase>> g_features;

extern "C"
{
    uint64_t MainGetCurrentBlockIndex()
    {
        return g_file_processor ? g_file_processor->GetCurrentBlockIndex() : 0;
    }

    bool MainGetLoadingTrimmedState()
    {
        return g_file_processor ? g_file_processor->GetLoadingTrimmedState() : false;
    }
}

void android_main(struct android_app* app)
{
    gfxrecon::util::Log::Init();
    gfxrecon::util::Log::SetFatalCallback([](const char* message) { throw std::runtime_error(message); });
    GFXRECON_WRITE_CONSOLE("====== Entering android_main");

    // Keep screen on while window is active.
    ANativeActivity_setWindowFlags(app->activity, AWINDOW_FLAG_KEEP_SCREEN_ON, 0);

    // Explicit benchmark-only mode: freeze host buffer contents after the first play.
    const auto oa_static = gfxrecon::util::GetIntentExtra(app, "oa_static_memory");
    setenv("OA_STATIC_MEMORY", oa_static == "2" ? "2" : (oa_static == "1" ? "1" : "0"), 1);

    setenv("OA_CAMERA", gfxrecon::util::GetIntentExtra(app, "oa_camera") == "1" ? "1" : "0", 1);
    // This dedicated app is useful directly from its launcher, without host intent arguments.
    setenv("OA_ENGINE_GEOMETRY", (gfxrecon::util::GetIntentExtra(app, "oa_native_geometry") == "1" || gfxrecon::util::GetIntentExtra(app, kArgsExtentKey).empty()) ? "1" : "0", 1);
    std::string args = gfxrecon::util::GetIntentExtra(app, kArgsExtentKey);
    if(args.empty()) {
        const std::string base=app->activity->internalDataPath;
        args="--loop-frame 1 --remove-unsupported --memory-translation rebind --opcd --log-file "+base+"/camera-default.log "+base+"/dalentarth.gfxr";
        setenv("OA_CAMERA","1",1);setenv("OA_STATIC_MEMORY","2",1);
        FILE* control=std::fopen((base+"/camera.txt").c_str(),"w");
        if(control) {std::fputs("0 0 0 0\n",control);std::fclose(control);}
    }
    gfxrecon::replay::LoadFeatures(g_features);

    // Each Feature adds its own command-line entries to the shared name lists, so an entry exists only
    // when the build contains the Feature that reads it. The lists outlive the parser because remote
    // settings are parsed against the same names.

    std::string       options   = kOptions;
    std::string       arguments = kArguments;
    AppendFeatureOptions(g_features, options, arguments);

    gfxrecon::util::ArgumentParser arg_parser(false, args.c_str(), options, arguments);

    bool run     = true;
    bool success = false;

    // If --remote-connect or --remote-listen is specified, the controller supplies the replay settings. Because the
    // user explicitly requested remote control, treat any failure to establish it as fatal rather than silently
    // falling back to the intent arguments.
    gfxrecon::util::RemoteChannel remote_channel;
    if (gfxrecon::replay::SetupRemoteChannel(remote_channel, arg_parser, options, arguments) ==
        gfxrecon::replay::RemoteSetupResult::kFailed)
    {
        run = false;
    }

    app->onAppCmd     = ProcessAppCmd;
    app->onInputEvent = ProcessInputEvent;

    if (CheckOptionPrintUsage(kApplicationName, arg_parser))
    {
        run = false;
    }
    else if (CheckOptionPrintFeatureVersions<gfxrecon::replay::ReplayFeatureBase>(kApplicationName, arg_parser))
    {
        run = false;
    }
    else if (arg_parser.IsInvalid() || (arg_parser.GetPositionalArgumentsCount() > 1))
    {
        PrintUsage(kApplicationName);
        run = false;
    }

    if (run)
    {
        gfxrecon::util::Log::Settings log_settings;
        GetLogSettings(arg_parser, log_settings);
        gfxrecon::util::Log::UpdateWithSettings(log_settings);

        // An entry that received a value outside its accepted set gets a warning. The Feature that
        // owns the entry then uses its default value. The log settings apply before this call, so
        // --log-level controls the warning.
        CheckFeatureOptionValues(g_features, arg_parser);

        std::string filename = kDefaultCaptureFile;
        if (arg_parser.GetPositionalArgumentsCount() == 1)
        {
            filename = arg_parser.GetPositionalArguments()[0];
        }

        try
        {
            auto make_application = [&](gfxrecon::decode::FileProcessor* fp) {
                return std::make_shared<gfxrecon::application::Application>(
                    kApplicationName, fp, VK_KHR_ANDROID_SURFACE_EXTENSION_NAME, app);
            };

            success = gfxrecon::replay::RunReplay(g_file_processor, g_features, arg_parser, filename, make_application);
        }
        catch (std::runtime_error& error)
        {
            GFXRECON_WRITE_CONSOLE("Replay failed with error message: %s", error.what());
        }
        catch (const std::exception& error)
        {
            GFXRECON_WRITE_CONSOLE("Replay has encountered a fatal error and cannot continue: %s", error.what());
        }
        catch (...)
        {
            GFXRECON_WRITE_CONSOLE("Replay failed due to an unhandled exception");
        }

        // Ensure user data is cleared after either a successful run or an exception.
        app->userData = nullptr;
    }

    // Notify the controller that replay is complete. A no-op when no remote controller is connected.
    gfxrecon::replay::ShutdownRemoteChannel(remote_channel, success);

    GFXRECON_WRITE_CONSOLE("====== Exiting android_main");

    gfxrecon::util::DestroyActivity(app);

    gfxrecon::util::Log::Release();

    raise(SIGTERM);
}

void ProcessAppCmd(struct android_app* app, int32_t cmd)
{
    if (app->userData != nullptr)
    {
        using namespace gfxrecon::application;
        auto application = reinterpret_cast<Application*>(app->userData);
        assert(application);

        switch (cmd)
        {
            case APP_CMD_INIT_WINDOW:
            {
                auto android_context = reinterpret_cast<AndroidContext*>(
                    application->GetWsiContext(VK_KHR_ANDROID_SURFACE_EXTENSION_NAME));
                assert(android_context);
                android_context->InitWindow();
                break;
            }
            case APP_CMD_GAINED_FOCUS:
            {
                GFXRECON_LOG_INFO("Application gained focus.")
                application->SetPaused(false);
                break;
            }
            case APP_CMD_LOST_FOCUS:
            {
                GFXRECON_LOG_INFO("Application lost focus.")
                application->SetPaused(true);
                break;
            }
        }
    }
}

int32_t ProcessInputEvent(struct android_app* app, AInputEvent* event)
{
    if(oa_camera::Enabled() && AInputEvent_getType(event)==AINPUT_EVENT_TYPE_KEY && AKeyEvent_getAction(event)==AKEY_EVENT_ACTION_DOWN) {
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
    if (oa_camera::Enabled() && AInputEvent_getType(event)==AINPUT_EVENT_TYPE_MOTION && (AInputEvent_getSource(event)&AINPUT_SOURCE_CLASS_POINTER)) {
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

    if (app->userData != nullptr)
    {
        int32_t type = AInputEvent_getType(event);

        if (type == AINPUT_EVENT_TYPE_MOTION)
        {
            static int32_t start_pointer_id = 0;
            static int32_t start_x          = 0;
            static int32_t start_y          = 0;

            int32_t action = AMotionEvent_getAction(event);

            if (action == AMOTION_EVENT_ACTION_UP)
            {
                auto application = reinterpret_cast<gfxrecon::application::Application*>(app->userData);
                assert(application);
                int32_t horizontal_distance = 0;
                int32_t vertical_distance   = 0;

                if (start_pointer_id == AMotionEvent_getPointerId(event, 0))
                {
                    horizontal_distance = AMotionEvent_getX(event, 0) - start_x;
                    vertical_distance   = AMotionEvent_getY(event, 0) - start_y;
                }

                if (abs(horizontal_distance) > kSwipeDistance)
                {
                    if ((horizontal_distance < 0) && (abs(horizontal_distance) > abs(vertical_distance)) &&
                        application->GetPaused())
                    {
                        // Treat as swipe right-to-left to advance frame while paused.
                        application->PlaySingleFrame();
                    }
                }
                else if (abs(vertical_distance) > kSwipeDistance)
                {
                    // Ignore vertical swipe.
                }
                else
                {
                    // Treat as a tap to toggle pause state.
                    application->SetPaused(!application->GetPaused());
                }

                return 1;
            }
            else if (action == AMOTION_EVENT_ACTION_DOWN)
            {
                start_pointer_id = AMotionEvent_getPointerId(event, 0);
                start_x          = AMotionEvent_getX(event, 0);
                start_y          = AMotionEvent_getY(event, 0);
                return 1;
            }
        }
        else if (type == AINPUT_EVENT_TYPE_KEY)
        {
            int32_t key    = AKeyEvent_getKeyCode(event);
            int32_t action = AKeyEvent_getAction(event);

            // Key input can be simulated with 'adb shell input keyevent <keycode>'. Relevant keycodes are:
            //  Space = 62
            //  P     = 44
            //  Right = 22
            //  N     = 42
            if (action == AKEY_EVENT_ACTION_UP)
            {
                auto application = reinterpret_cast<gfxrecon::application::Application*>(app->userData);
                assert(application);
                switch (key)
                {
                    case AKEYCODE_SPACE:
                    case AKEYCODE_P:
                        application->SetPaused(!application->GetPaused());
                        break;
                    default:
                        break;
                }
            }
            else if (action == AKEY_EVENT_ACTION_DOWN)
            {
                auto application = reinterpret_cast<gfxrecon::application::Application*>(app->userData);
                assert(application);
                switch (key)
                {
                    case AKEYCODE_DPAD_RIGHT:
                    case AKEYCODE_N:
                        if (application->GetPaused())
                        {
                            application->PlaySingleFrame();
                        }
                        break;
                    default:
                        break;
                }
            }
        }
    }

    return 0;
}
