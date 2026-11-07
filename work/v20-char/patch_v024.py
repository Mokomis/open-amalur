"""Version 0.24.0: Veil menus, configurable HUD, controller, mouse and keyboard input, saves."""
import re
from pathlib import Path
host = Path.home() / "Documents/Opem Amalur/work/v19-host"
def edit(name, pairs):
    f = host / name
    t = f.read_bytes().decode("utf-8")
    for old, new in pairs:
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (name, old[:90], t.count(old)))
        t = t.replace(old, new)
    f.write_bytes(t.encode("utf-8"))
edit("android_scene.cmake", [("oa_character_gl.c oa_sky.c ", "oa_character_gl.c oa_sky.c oa_ui.c oa_menu.c "), ("amalur_scene_mesh android log EGL GLESv3 m)", "amalur_scene_mesh android log EGL GLESv3 m dl)")])
edit("CMakeLists.txt", [("VERSION 0.23.0", "VERSION 0.24.0"), ("add_executable(amalur-exploration-input-test tests/exploration_input_test.c exploration_input.c)", "add_executable(oa-menu-test tests/oa_menu_test.c oa_menu.c exploration_input.c)\ntarget_include_directories(oa-menu-test PRIVATE tests/input_stubs .)\ntarget_link_libraries(oa-menu-test PRIVATE m)\nadd_executable(amalur-exploration-input-test tests/exploration_input_test.c exploration_input.c)")])
edit("AndroidManifest.xml", [('android:versionCode="24" android:versionName="0.23.0"', 'android:versionCode="25" android:versionName="0.24.0"')])
edit("package_android.py", [("opem-amalur-scene-v0.23-arm64.apk", "opem-amalur-scene-v0.24-arm64.apk"), ("files['assets/collision.bin']=root/'outputs/scene-v17/collision.bin'", "files['assets/collision.bin']=root/'outputs/scene-v17/collision.bin'\nfiles['assets/oa_ui.bin']=root/'work/v21-ui/oa_ui.bin'\nfiles['assets/licenses/Cinzel-OFL.txt']=root/'work/v21-ui/fonts/Cinzel-OFL.txt'\nfiles['assets/licenses/Alegreya-OFL.txt']=root/'work/v21-ui/fonts/Alegreya-OFL.txt'")])
edit("build_validate.cmd", [("--target amalur-exploration-input-test oa-character-test ", "--target amalur-exploration-input-test oa-character-test oa-menu-test "),
 ("work\\v19-host\\build-windows\\amalur-exploration-input-test.exe > outputs\\scene-v19\\input-tests.txt 2>&1\nif errorlevel 1 exit /b %errorlevel%\n".replace("\n", "\r\n") if b"\r\n" in (host / "build_validate.cmd").read_bytes() else "work\\v19-host\\build-windows\\amalur-exploration-input-test.exe > outputs\\scene-v19\\input-tests.txt 2>&1\nif errorlevel 1 exit /b %errorlevel%\n",
  ("work\\v19-host\\build-windows\\amalur-exploration-input-test.exe > outputs\\scene-v19\\input-tests.txt 2>&1\nif errorlevel 1 exit /b %errorlevel%\nwork\\v19-host\\build-windows\\oa-menu-test.exe work\\v19-host\\build-windows > outputs\\scene-v19\\menu-tests.txt 2>&1\nif errorlevel 1 exit /b %errorlevel%\n").replace("\n", "\r\n" if b"\r\n" in (host / "build_validate.cmd").read_bytes() else "\n"))])
# Stubs
s = host / "tests/input_stubs/android/input.h"; t = s.read_text()
t = t.replace("typedef struct AInputEvent {int family,type,device,action,key,repeat,flags;", "typedef struct AInputEvent {int family,type,device,action,key,repeat,flags,buttons;")
t = t.replace("AMOTION_EVENT_AXIS_Z=11,AMOTION_EVENT_AXIS_RZ=14};", "AMOTION_EVENT_AXIS_Z=11,AMOTION_EVENT_AXIS_RZ=14,AMOTION_EVENT_AXIS_VSCROLL=9,AMOTION_EVENT_AXIS_HAT_X=15,AMOTION_EVENT_AXIS_HAT_Y=16,AMOTION_EVENT_AXIS_RTRIGGER=18,AMOTION_EVENT_AXIS_GAS=22,AMOTION_EVENT_ACTION_HOVER_MOVE=7,AMOTION_EVENT_ACTION_SCROLL=8,AMOTION_EVENT_BUTTON_PRIMARY=1,AMOTION_EVENT_BUTTON_SECONDARY=2};\nstatic inline int32_t AMotionEvent_getButtonState(const AInputEvent *e){return e->buttons;}")
s.write_text(t)
s = host / "tests/input_stubs/android/keycodes.h"; t = s.read_text()
want = {"AKEYCODE_ESCAPE": 111, "AKEYCODE_ENTER": 66, "AKEYCODE_SPACE": 62, "AKEYCODE_BACK": 4, "AKEYCODE_MENU": 82, "AKEYCODE_MINUS": 69, "AKEYCODE_EQUALS": 70, "AKEYCODE_PLUS": 81, "AKEYCODE_DPAD_CENTER": 23, "AKEYCODE_DPAD_UP": 19, "AKEYCODE_DPAD_DOWN": 20, "AKEYCODE_DPAD_LEFT": 21, "AKEYCODE_DPAD_RIGHT": 22, "AKEYCODE_BUTTON_B": 97, "AKEYCODE_BUTTON_START": 108, "AKEYCODE_BUTTON_SELECT": 109, "AKEYCODE_BUTTON_R1": 103, "AKEYCODE_BUTTON_R2": 105}
add = ",".join("%s=%d" % (k, v) for k, v in want.items() if k not in t)
if add:
    t = t.replace("#endif", "enum {%s};\n#endif" % add)
s.write_text(t)
edit("android_input_probe.h", [("OPEM_INPUT_JOYSTICK, OPEM_INPUT_KEYBOARD\n", "OPEM_INPUT_JOYSTICK, OPEM_INPUT_KEYBOARD, OPEM_INPUT_MOUSE\n")]) if (host / "android_input_probe.h").exists() else None
for probe in host.rglob("android_input_probe.*"):
    if "build" in str(probe):
        continue
    t = probe.read_bytes().decode("utf-8")
    if probe.suffix == ".h":
        t, n = re.subn(r"OPEM_INPUT_JOYSTICK, OPEM_INPUT_KEYBOARD(?!, OPEM_INPUT_MOUSE)", "OPEM_INPUT_JOYSTICK, OPEM_INPUT_KEYBOARD, OPEM_INPUT_MOUSE", t)
    else:
        t, n = re.subn(r"(        if \(has_source\(source, AINPUT_SOURCE_JOYSTICK\)\) return OPEM_INPUT_JOYSTICK;)", r"\1\n        if (has_source(source, AINPUT_SOURCE_MOUSE)) return OPEM_INPUT_MOUSE;", t)
    probe.write_bytes(t.encode("utf-8")); print(probe.name, n)
edit("exploration_input.h", [("    int interact_requested,lighting_requested,attack_requested;", "    int interact_requested,lighting_requested,attack_requested,menu_requested;"),
 ("float exploration_ui_scale(int width,int height);", "float exploration_ui_scale(int width,int height);\n/* Touch zones as x,y,w,h in pixels from the configured HUD. Empty means none. Until first set, the fixed development layout applies. */\nvoid exploration_input_set_zones(const float attack[4],const float interact[4],const float menu[4]);")])
edit("exploration_input.c", [("static float bounded(float v)", "static float zone_attack[4],zone_interact[4],zone_menu[4];static int zones_set;\nvoid exploration_input_set_zones(const float a[4],const float b[4],const float c[4]){memcpy(zone_attack,a,16);memcpy(zone_interact,b,16);memcpy(zone_menu,c,16);zones_set=1;}\nstatic int in_zone(const float r[4],float x,float y){return r[2]>0&&x>=r[0]&&y>=r[1]&&x<r[0]+r[2]&&y<r[1]+r[3];}\nstatic float bounded(float v)"),
 ("        if(y>h-112*scale&&y<h-60*scale&&fabsf(x-w*.5f)<160*scale){s->interact_requested=1;return 1;}\n", "        if(zones_set){if(in_zone(zone_menu,x,y)){s->menu_requested=1;return 1;}if(in_zone(zone_interact,x,y)){s->interact_requested=1;return 1;}if(in_zone(zone_attack,x,y)){s->attack_requested=1;return 1;}}\n        else{\n        if(y>h-112*scale&&y<h-60*scale&&fabsf(x-w*.5f)<160*scale){s->interact_requested=1;return 1;}\n"),
 ("        if(y<68*scale&&x>=w-140*scale){s->toggle_requested=1;return 1;}\n", "        if(y<68*scale&&x>=w-140*scale){s->toggle_requested=1;return 1;}\n        }\n")])
edit("android_scene.c", [
 ('#include "oa_sky.h"\n', '#include "oa_sky.h"\n#include "oa_ui.h"\n#include "oa_menu.h"\n#include <dlfcn.h>\n'),
 ("    oa_sky sky;\n} graphics;", "    oa_sky sky;\n    oa_ui ui;\n} graphics;\n/* Worker-only UI asset, kept for surface recreation. */\nstatic uint8_t *ui_bytes;static size_t ui_size;"),
 ("    float move_scale;\n", "    float move_scale,look_speed;\n    int invert_look;\n"),
 ("        exploration_overlay_close(&g->overlay);", "        exploration_overlay_close(&g->overlay);oa_ui_close(&g->ui);"),
 ('    if(!exploration_overlay_open(&g->overlay)){LOGE("Exploration overlay initialization failed");goto fail;}', '    if(!exploration_overlay_open(&g->overlay)){LOGE("Exploration overlay initialization failed");goto fail;}\n    if(!ui_bytes||!oa_ui_open(&g->ui,ui_bytes,ui_size))LOGE("Veil UI unavailable");'),
 ("const oa_interaction *interaction,int room_lighting,const char *door_prompt){\n    float hud[3];", "const oa_interaction *interaction,int room_lighting,const char *door_prompt,oa_menu *menu,int world,float dt){\n    float hud[3];"),
 ("    if(mesh->vertices){float matrix[16],eye[3];", "    if(mesh->vertices&&menu->screen!=OA_SCREEN_TITLE&&!(menu->screen==OA_SCREEN_OPTIONS&&menu->from==OA_SCREEN_TITLE)){float matrix[16],eye[3];"),
 ("""    /* Test aid: adb shell setprop debug.opem.hud off hides the overlay for clean captures. */
        {char hud_prop[PROP_VALUE_MAX]={0};if(!(__system_property_get("debug.opem.hud",hud_prop)>0&&!strcmp(hud_prop,"off")))
        exploration_overlay_draw(&g->overlay,width,height,input,c->walking,c->collision_ready,interaction,room_lighting,door_prompt,c->foe_ready?hud:NULL);}
""", """    if(interaction&&interaction->window_open)exploration_overlay_draw(&g->overlay,width,height,input,c->walking,c->collision_ready,interaction,room_lighting,door_prompt,NULL);
    else{oa_hud_view view;char hud_prop[PROP_VALUE_MAX]={0};const float *door=oa_doors[world];memset(&view,0,sizeof(view));
        view.health=c->foe_ready?hud[0]:1.f;view.foe=c->foe_ready?hud[1]:-1.f;view.dead=c->foe_ready&&hud[2]>0;view.health_now=c->combat.player_hp;view.health_max=c->combat.player_max;view.yaw=c->walk_yaw;view.feet_x=c->body.feet[0];view.feet_y=c->body.feet[1];view.target_x=door[0];view.target_y=door[1];view.has_target=1;view.room_lighting=room_lighting;
        view.location=world?"Gorhart":"Alchemy Shop";view.prompt=view.dead?"You Have Fallen":interaction&&interaction->ready&&interaction->selected.generation?"Alchemy":door_prompt;
        view.move_active=input->move_id>=0;view.move_origin_x=input->move_origin_x;view.move_origin_y=input->move_origin_y;view.move_x=input->move_x;view.move_y=input->move_y;
        /* Test aid: adb shell setprop debug.opem.hud off hides the HUD for clean captures. */
        view.show_hud=!(__system_property_get("debug.opem.hud",hud_prop)>0&&!strcmp(hud_prop,"off"));
        oa_ui_begin(&g->ui);if(g->ui.ready)oa_menu_frame(menu,&g->ui,width,height,&view,dt);oa_ui_end(&g->ui,width,height);}
"""),
 ("        c->walk_yaw=remainderf(c->walk_yaw-input->look_dx-yaw*dt,6.283185307f);\n        c->walk_pitch=clampf(c->walk_pitch-input->look_dy+pitch*dt,-1.45f,1.45f);", "        c->walk_yaw=remainderf(c->walk_yaw-(input->look_dx+yaw*dt)*c->look_speed,6.283185307f);\n        c->walk_pitch=clampf(c->walk_pitch+(pitch*dt-input->look_dy)*c->look_speed*(c->invert_look?-1.f:1.f),-1.45f,1.45f);"),
 ("static void input_drain(AInputQueue *queue,exploration_input *input,const graphics *g,int enabled,oa_interaction *interaction,const char *inventory_path){", "static void input_drain(AInputQueue *queue,exploration_input *input,const graphics *g,int enabled,oa_interaction *interaction,const char *inventory_path,oa_menu *menu){"),
 ("exploration_input_clear(input);}else handled=exploration_input_event(input,event,g->width,g->height);}", "exploration_input_clear(input);}else{handled=oa_menu_event(menu,event,g->width,g->height,input);if(!handled&&menu->screen==OA_SCREEN_GAME)handled=exploration_input_event(input,event,g->width,g->height);}}"),
 ("static void *worker_main(void *argument){", """static void frame_rate_apply(ANativeWindow *window,int rate){
    /* API 30 and later; older systems keep their default. */
    typedef int32_t (*set_rate)(ANativeWindow*,float,int8_t);static set_rate call;static int looked;
    if(!looked){void *lib=dlopen("libandroid.so",RTLD_NOW);looked=1;if(lib)call=(set_rate)dlsym(lib,"ANativeWindow_setFrameRate");}
    if(call&&window){int32_t r=call(window,(float)rate,0);LOGI("Frame rate request %d Hz result=%d",rate,r);}
}
static void *worker_main(void *argument){"""),
 ("    input_host inputs={0};amalur_runtime *realm=NULL;", "    static oa_menu menu;static oa_save loaded;int pending_load=0,applied_rate=-1;ANativeWindow *rate_window=NULL;float last_dt=0;\n    input_host inputs={0};amalur_runtime *realm=NULL;"),
 ("c.move_scale=1;oa_combat_reset(&c.combat);\n", "c.move_scale=1;c.look_speed=1;oa_combat_reset(&c.combat);\n    oa_menu_init(&menu,s->activity->internalDataPath,0);\n    {AAsset *asset=AAssetManager_open(s->activity->assetManager,\"oa_ui.bin\",AASSET_MODE_BUFFER);if(asset){size_t size=(size_t)AAsset_getLength64(asset);uint8_t *bytes=(uint8_t*)malloc(size);if(bytes&&AAsset_read(asset,bytes,size)==(int)size){ui_bytes=bytes;ui_size=size;}else free(bytes);AAsset_close(asset);}else LOGE(\"UI asset missing\");}\n"),
 ('!strcmp(prop,"town")){world_request=1;c.spawn_hint=oa_doors[1];}}', '!strcmp(prop,"town")){world_request=1;c.spawn_hint=oa_doors[1];oa_menu_open(&menu,OA_SCREEN_GAME);}}'),
 ("input_drain(s->attached_queue,&movement,&g,resumed&&focused,&interaction,inventory_path);}", "input_drain(s->attached_queue,&movement,&g,resumed&&focused,&interaction,inventory_path,&menu);}"),
 ("""                oa_npcs_update(&c.npcs,dt);
                if(c.foe_ready&&c.collision_ready&&!interaction.window_open){""", """                int playing;
                if(movement.menu_requested){movement.menu_requested=0;oa_menu_open(&menu,OA_SCREEN_PAUSE);}
                playing=menu.screen==OA_SCREEN_GAME;c.look_speed=menu.settings.look_speed;c.invert_look=menu.settings.invert_look;last_dt=dt;
                if(s->active_window!=rate_window||applied_rate!=menu.settings.rate){rate_window=s->active_window;applied_rate=menu.settings.rate;frame_rate_apply(rate_window,oa_menu_rate(&menu));}
                if(playing)oa_npcs_update(&c.npcs,dt);
                if(playing&&c.foe_ready&&c.collision_ready&&!interaction.window_open){"""),
 ("if(focused&&!interaction.window_open)exploration_update(&c,&movement,dt);else{exploration_input_clear(&movement);last_frame_ms=0;}", "if(focused&&!interaction.window_open&&playing)exploration_update(&c,&movement,dt);else{exploration_input_clear(&movement);if(playing)last_frame_ms=0;}"),
 ("                if(!interaction.window_open){\n                    interaction.selected.generation=0;", "                if(!interaction.window_open&&playing){\n                    interaction.selected.generation=0;"),
 ("oa_character_pose(&c.character);}\n                    exploration_input_clear(&movement);last_frame_ms=0;lighting_started_ms=0;", "oa_character_pose(&c.character);}\n                    if(pending_load&&c.collision_ready){pending_load=0;c.walk_yaw=loaded.yaw;c.walk_pitch=loaded.pitch;c.character.facing=loaded.yaw;c.combat.player_hp=clampf(loaded.health,1,c.combat.player_max);oa_character_pose(&c.character);}\n                    exploration_input_clear(&movement);last_frame_ms=0;lighting_started_ms=0;"),
 ("if(!graphics_draw(&g,&mesh,&materials,&c,&movement,&interaction,room_lighting,door_prompt)){pthread_mutex_lock(&s->mutex);graphics_close(&g);pthread_mutex_unlock(&s->mutex);}", """if(!graphics_draw(&g,&mesh,&materials,&c,&movement,&interaction,room_lighting,door_prompt,&menu,world,last_dt)){pthread_mutex_lock(&s->mutex);graphics_close(&g);pthread_mutex_unlock(&s->mutex);}
                switch(menu.action){
                    case OA_ACTION_NEW_GAME:c.spawn_hint=NULL;pending_load=0;oa_menu_open(&menu,OA_SCREEN_GAME);
                        if(world!=0)world_request=0;else{exploration_reset(&c);oa_combat_reset(&c.combat);oa_character_stop(&c.character);c.character.facing=c.walk_yaw;memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));oa_character_pose(&c.character);}
                        LOGI("Menu new game");break;
                    case OA_ACTION_LOAD:if(oa_save_read(&loaded,menu.save_path)){c.spawn_hint=loaded.feet;oa_menu_open(&menu,OA_SCREEN_GAME);pending_load=1;
                            if(world!=loaded.world)world_request=loaded.world;
                            else{exploration_reset(&c);memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));if(c.collision_ready){pending_load=0;c.walk_yaw=loaded.yaw;c.walk_pitch=loaded.pitch;c.character.facing=loaded.yaw;c.combat.player_hp=clampf(loaded.health,1,c.combat.player_max);oa_character_pose(&c.character);}}
                            LOGI("Menu loaded save world=%d feet=(%.0f %.0f %.0f) ready=%d",loaded.world,loaded.feet[0],loaded.feet[1],loaded.feet[2],c.collision_ready);}
                        else oa_menu_status(&menu,"No saved game could be read");break;
                    case OA_ACTION_SAVE:{oa_save save;memset(&save,0,sizeof(save));save.world=world;memcpy(save.feet,c.body.feet,sizeof(save.feet));save.yaw=c.walk_yaw;save.pitch=c.walk_pitch;save.health=c.combat.player_hp;
                        if(c.collision_ready&&oa_save_write(&save,menu.save_path)){menu.has_save=1;oa_menu_status(&menu,"Game saved");LOGI("Menu saved world=%d",world);}else oa_menu_status(&menu,"Could not save");break;}
                    case OA_ACTION_EXIT:LOGI("Menu exit");ANativeActivity_finish(s->activity);break;
                    case OA_ACTION_TOGGLE_LIGHTING:room_lighting=!room_lighting;break;
                    case OA_ACTION_APPLY_RATE:case OA_ACTION_NONE:default:break;}
                menu.action=OA_ACTION_NONE;"""),
 ("    opem_android_scripts_stop(realm);\n", "    opem_android_scripts_stop(realm);\n    free(ui_bytes);ui_bytes=NULL;ui_size=0;\n"),
])
print("patched")
