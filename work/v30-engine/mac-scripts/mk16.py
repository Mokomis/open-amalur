from pathlib import Path
d=Path('work/v19-host')
lut=open('work/v19-inputs/initial_0.pak/1525613.dds','rb').read()[38:];assert len(lut)==16384
s=(d/'room_environment.inc').read_text(encoding='utf-8')
s+='/* Color-correction asset 1525613, RGBA8, indexed (r,g,b) per shipped merge and combine shaders. */\nstatic const unsigned char opem_env_lut[16384]={'+','.join(str(x) for x in lut)+'};\n'
(d/'room_environment.inc').write_text(s,encoding='utf-8')
h=(d/'room_lighting_shader.h').read_text()
h=h.replace('Not implemented: specular, SSAO, shadow maps, fog, bloom, color correction. */','Color LUT applied with the shader half-texel mapping; brightness and color_transition terms are not.\n * Not implemented: specular, SSAO, shadow maps, fog, bloom. */')
h=h.replace('"#version 300 es\\nprecision highp float;\\n"','"#version 300 es\\nprecision highp float;precision highp sampler3D;\\n"')
h=h.replace('uniform samplerCube room_cube;','uniform sampler3D room_lut;uniform samplerCube room_cube;')
a='"outColor=vec4(clamp(clamp(base,0.0,1.0)*illumination,0.0,1.0),1.0);}";'
assert a in h
h=h.replace(a,'"vec3 lit=clamp(clamp(base,0.0,1.0)*illumination,0.0,1.0);if(room_mode!=0)lit=texture(room_lut,lit*0.9375+0.03125).rgb;outColor=vec4(lit,1.0);}";')
(d/'room_lighting_shader.h').write_text(h)
x=(d/'room_lighting.h').read_text().replace('shadow_color;GLuint cube;}','shadow_color,lut_sampler;GLuint cube,lut;}');(d/'room_lighting.h').write_text(x)
c=(d/'room_lighting.c').read_text()
c=c.replace('glActiveTexture(GL_TEXTURE0);}\n return s->mode','''glActiveTexture(GL_TEXTURE2);glGenTextures(1,&s->lut);glBindTexture(GL_TEXTURE_3D,s->lut);glPixelStorei(GL_UNPACK_ALIGNMENT,1);glTexImage3D(GL_TEXTURE_3D,0,GL_RGBA8,16,16,16,0,GL_RGBA,GL_UNSIGNED_BYTE,opem_env_lut);glPixelStorei(GL_UNPACK_ALIGNMENT,4);glTexParameteri(GL_TEXTURE_3D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_3D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_3D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_3D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_3D,GL_TEXTURE_WRAP_R,GL_CLAMP_TO_EDGE);glActiveTexture(GL_TEXTURE0);s->lut_sampler=glGetUniformLocation(program,"room_lut");}\n return s->lut_sampler>=0&&s->lut&&s->mode''')
c=c.replace('glBindTexture(GL_TEXTURE_CUBE_MAP,s->cube);glActiveTexture(GL_TEXTURE0);glUniform1i(s->cube_sampler,1);','glBindTexture(GL_TEXTURE_CUBE_MAP,s->cube);glActiveTexture(GL_TEXTURE2);glBindTexture(GL_TEXTURE_3D,s->lut);glActiveTexture(GL_TEXTURE0);glUniform1i(s->cube_sampler,1);glUniform1i(s->lut_sampler,2);')
c=c.replace('if(s->cube)glDeleteTextures(1,&s->cube);s->cube=0;','if(s->cube)glDeleteTextures(1,&s->cube);if(s->lut)glDeleteTextures(1,&s->lut);s->cube=0;s->lut=0;')
assert 'room_lut' in c and 'opem_env_lut' in c and 'glUniform1i(s->lut_sampler,2)' in c
(d/'room_lighting.c').write_text(c)
m=(d/'AndroidManifest.xml').read_text().replace('android:versionCode="15" android:versionName="0.15.0"','android:versionCode="16" android:versionName="0.16.0"');(d/'AndroidManifest.xml').write_text(m)
cm=(d/'CMakeLists.txt').read_text().replace('VERSION 0.15.0','VERSION 0.16.0');(d/'CMakeLists.txt').write_text(cm)
for f in ('package_android.py',):
    t=(d/f).read_bytes().decode('utf-8').replace('opem-amalur-scene-v0.15','opem-amalur-scene-v0.16');(d/f).write_bytes(t.encode('utf-8'))
