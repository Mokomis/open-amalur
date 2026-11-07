from pathlib import Path
import re
root=Path.home()/"Documents/Opem Amalur";h=root/"work/v19-host"
def sub(p,pairs):
    t=p.read_text(encoding="utf-8")
    for a,b in pairs:
        assert a in t,a
        t=t.replace(a,b,1)
    p.write_text(t,encoding="utf-8",newline="\n")
sub(h/"android_scene.c",[
 ('#include "oa_audio.h"','#include "oa_audio.h"\n#include "oa_fx.h"'),
 ('if(prof.fx)oa_post_fx(&g->post,matrix,eye,c->body.feet,prof.fx,(float)(monotonic_ms()%3600000)*.001f);','if(prof.fx)oa_post_fx(&g->post,matrix,eye,c->body.feet,prof.fx,(float)(monotonic_ms()%3600000)*.001f);oa_fx_update(active_fx,eye,dt);oa_fx_draw(active_fx,matrix,oa_live_fog_color,oa_live_fog_density/500000.f,oa_live_fog_start);'),
 ('active_actors=oa_actors_open(manager);if(!active_audio)','active_actors=oa_actors_open(manager);oa_fx_close(active_fx);active_fx=NULL;if(!active_audio)'),
])
t=(h/"android_scene.c").read_text(encoding="utf-8")
print([m.group(0)[:80] for m in re.finditer(r"static [a-z_ ]*\*active_(audio|actors)[^\n]*",t)][:3])
print(t.count("oa_stream_close(active_stream);active_stream=NULL;"))
t2=(h/"CMakeLists.txt").read_text(encoding="utf-8")
for m in re.finditer(r"[^\n]*oa_nav\.c[^\n]*",t2):print(m.group(0)[:300])
