from pathlib import Path
r=Path.home()/"Documents/Opem Amalur/work/v19-host";f=r/"android_scene.c";s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n")
def rep(a,b):
    global s
    assert a in s,a[:60]
    s=s.replace(a,b,1)
rep(" GLuint shadow_fbo,shadow_tex,world_program;"," GLuint shadow_fbo,shadow_tex,world_program,world_programs[4];oa_lightgrid light_grid;")
rep("if(g->world_program)glDeleteProgram(g->world_program);","{int wi;for(wi=0;wi<4;wi++)if(g->world_programs[wi])glDeleteProgram(g->world_programs[wi]);g->world_program=0;}oa_lightgrid_close(&g->light_grid);")
rep('g->world_program=oa_post_program(oa_world_vertex,oa_world_fragment);if(!g->world_program)LOGE("World shader unavailable");','{int wi,all=1;for(wi=0;wi<4;wi++){g->world_programs[wi]=oa_world_program(wi,OA_LIVE_LIGHTS);all=all&&g->world_programs[wi];}if(all&&oa_lightgrid_open(&g->light_grid,oa_live_lights,OA_LIVE_LIGHTS)){g->world_program=g->world_programs[0];LOGI("LIGHT GRID lights=%d tile_refs=%u dropped=%u size=%dx%d",OA_LIVE_LIGHTS,g->light_grid.references,g->light_grid.dropped,g->light_grid.width,g->light_grid.height);}else LOGE("World shader unavailable");}')
a=s.index("static void world_draw(graphics *g,");b=s.index("static int graphics_draw(graphics *g,")
s=s[:a]+r'''static void world_draw(graphics *g,const float mvp[16],const float eye[3],int shadow_on,const float shadow_matrix[16]){
    const float *sun=opem_town_sun(),*sc=opem_town_sun_rgb(),*sh=opem_town_shadow_rgba();int v,i;
    for(v=0;v<4;v++){GLuint w=g->world_programs[v];glUseProgram(w);glUniformMatrix4fv(glGetUniformLocation(w,"mvp"),1,GL_FALSE,mvp);glUniform3fv(glGetUniformLocation(w,"eye"),1,eye);glUniform3fv(glGetUniformLocation(w,"sun_color"),1,sc);glUniform3fv(glGetUniformLocation(w,"sun_dir"),1,sun);glUniform3fv(glGetUniformLocation(w,"shadow_color"),1,sh);glUniform3fv(glGetUniformLocation(w,"fog_color"),1,oa_live_fog_color);/* The fog value is real; its scale is authored, since the mapping into the game's fog constants is not recovered. */glUniform2f(glGetUniformLocation(w,"fog"),0.f,oa_live_fog_density*1.2e-7f);glUniform1i(glGetUniformLocation(w,"features"),prof.live);glUniform1i(glGetUniformLocation(w,"shadow_on"),shadow_on);
        {static const char *names[6]={"t0","t1","t2","t3","t4","t5"};for(i=0;i<6;i++)glUniform1i(glGetUniformLocation(w,names[i]),i);}
        glUniform1i(glGetUniformLocation(w,"cube"),8);glUniform1i(glGetUniformLocation(w,"shadow_map"),9);glUniform1i(glGetUniformLocation(w,"light_grid"),10);glUniform3f(glGetUniformLocation(w,"grid"),g->light_grid.origin[0],g->light_grid.origin[1],g->light_grid.scale);glUniform2i(glGetUniformLocation(w,"grid_size"),g->light_grid.width,g->light_grid.height);
        if(shadow_on)glUniformMatrix4fv(glGetUniformLocation(w,"shadow_matrix"),1,GL_FALSE,shadow_matrix);}
    glActiveTexture(GL_TEXTURE8);glBindTexture(GL_TEXTURE_CUBE_MAP,g->room_lights.cube);
    if(shadow_on){glActiveTexture(GL_TEXTURE9);glBindTexture(GL_TEXTURE_2D,g->shadow_tex);}
    glActiveTexture(GL_TEXTURE10);glBindTexture(GL_TEXTURE_2D,g->light_grid.tex);glBindBufferBase(GL_UNIFORM_BUFFER,0,g->light_grid.ubo);
    oa_stream_draw_world(active_stream,mvp,g->world_programs);
    glActiveTexture(GL_TEXTURE0);
}
'''+s[b:]
if crlf:s=s.replace("\n","\r\n")
f.write_bytes(s.encode())
for p in (r/"package_android.py",r/"AndroidManifest.xml"):
    if p.exists():
        t=p.read_bytes().decode();t2=t.replace("0.27","0.28").replace('versionCode="29"','versionCode="30"').replace("version_code=29","version_code=30");p.write_bytes(t2.encode());print(p.name,t!=t2)
print("ok")
