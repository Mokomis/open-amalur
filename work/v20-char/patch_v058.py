from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";h=root/"work/v19-host"
def sub(p,pairs):
    t=p.read_text(encoding="utf-8")
    for a,b in pairs:
        assert a in t,a
        t=t.replace(a,b,1)
    p.write_text(t,encoding="utf-8",newline="\n")
sub(h/"android_scene.c",[
 ("static oa_audio *active_audio;","static oa_audio *active_audio;static oa_fx *active_fx;static AAssetManager *fx_manager;static int fx_tried;"),
 ("oa_actors_gpu_close(active_actors);exploration_overlay_close(&g->overlay);","oa_fx_close(active_fx);active_fx=NULL;fx_tried=0;oa_actors_gpu_close(active_actors);exploration_overlay_close(&g->overlay);"),
 ("oa_fx_update(active_fx,eye,dt);","if(!active_fx&&!fx_tried&&fx_manager){fx_tried=1;active_fx=oa_fx_open(fx_manager);LOGI(\"FX %s\",active_fx?\"ready\":\"absent\");}oa_fx_update(active_fx,eye,dt);"),
 ("oa_fx_close(active_fx);active_fx=NULL;if(!active_audio)","oa_fx_close(active_fx);active_fx=NULL;fx_tried=0;fx_manager=manager;if(!active_audio)"),
])
t=(h/"android_scene.cmake").read_text(encoding="utf-8")
assert "oa_audio.c" in t
t=t.replace("oa_audio.c","oa_audio.c oa_fx.c",1)
(h/"android_scene.cmake").write_text(t,encoding="utf-8",newline="\n")
sub(h/"package_android.py",[("files['assets/licenses/Cinzel-OFL.txt']","_fx=Path(_os.environ.get('OA_FX_FILE',str(root/'work/v25-fx/dal/fx.bin')))\nif _fx.exists():files['assets/fx/fx.bin']=_fx\nfiles['assets/licenses/Cinzel-OFL.txt']")])
print("ok")
