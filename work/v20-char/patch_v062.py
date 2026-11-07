from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";h=root/"work/v19-host"
def sub(p,pairs):
    t=p.read_text(encoding="utf-8")
    for a,b in pairs:
        assert a in t,a
        t=t.replace(a,b,1)
    p.write_text(t,encoding="utf-8",newline="\n")
sub(h/"oa_sky.c",[
 ("uniform int use_lut;out vec4 color;","uniform int use_lut;uniform vec3 below;out vec4 color;"),
 ("vec3 c=mix(vec3(.4196,.3608,.2235),g.rgb,","vec3 c=mix(below,g.rgb,"),
 ('glUseProgram(s->program);glUniformMatrix4fv(s->mvp,1,GL_FALSE,mvp);','glUseProgram(s->program);glUniform3fv(glGetUniformLocation(s->program,"below"),1,oa_sky_below);glUniformMatrix4fv(s->mvp,1,GL_FALSE,mvp);'),
 ('static const char *vertex_source=','float oa_sky_below[3];\nstatic const char *vertex_source='),
])
sub(h/"oa_sky.h",[("void oa_sky_close(oa_sky *s);","void oa_sky_close(oa_sky *s);\n/* Colour below the horizon: the zone's fog colour. */\nextern float oa_sky_below[3];")])
sub(h/"android_scene.c",[("if(g->sky.ready&&!(prof.skip&1))oa_sky_draw(","memcpy(oa_sky_below,oa_live_fog_color,sizeof(oa_sky_below));if(g->sky.ready&&!(prof.skip&1))oa_sky_draw(")])
print("ok")
