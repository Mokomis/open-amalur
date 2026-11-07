"""Create work/v19-host from v18-host with recovered room lighting. Does not modify v18."""
import shutil,sys,json,re,hashlib
from pathlib import Path
sys.path.insert(0,'work/v19-lighting')
import decode_scene_lighting as D
src=Path('work/v18-host');dst=Path('work/v19-host');out=Path('outputs/scene-v19')
if dst.exists():raise SystemExit('v19-host exists')
shutil.copytree(src,dst,ignore=shutil.ignore_patterns('build-*','*.log','__pycache__'))
for f in ('Workbench.lua','workbench-integration.json','room-lighting.json'):shutil.copy2('outputs/scene-v18/'+f,out/f)
b=open('work/v19-inputs/DATA_0.pak/524912.region_bxml','rb').read();r=D.decode_region(b);p=b[8:]
E=r['environment'];T=E['time_keyed']
K='Noon'
for n in T:
    vals={json.dumps(T[n][k]['value'],sort_keys=True) for k in D.KEYS}
    if len(vals)>1 and not n.endswith('_index'):print('varies by key',n)
amb=r['ambient_cubes'][T['ambient_cube_index'][K]['value']]
faces=[p[o:o+256] for o in amb['face_texel_offsets']]
sun=T['directional_light_color'][K]['value'];si=T['directional_light_intensity'][K]['value']
shadow=T['shadow_color'][K]['value'];op=T['shadow_opacity'][K]['value'];d=E['directional_light_direction']['value']
scale=sun['intensity']*si
sc=[c*scale for c in sun['rgb']];sd=[-x for x in d];n=(sum(x*x for x in sd))**.5;
fmt=lambda s:','.join(format(float(x),'.9e')+'f' for x in s)
L=['/* Generated from region 524912 by work/v19-lighting/mk19.py. Noon key; values and evidence in outputs/scene-v19. */',
'static const float opem_env_sun_color[3]={%s};'%fmt(sc),'static const float opem_env_sun_direction[3]={%s};'%fmt(sd),
'static const float opem_env_shadow_color[4]={%s};'%fmt(shadow['rgb']+[op]),
'static const unsigned char opem_env_cube[6][256]={']
for f in faces:L.append('{'+','.join(str(x) for x in f)+'},')
L+=['};','']
(dst/'room_environment.inc').write_text('\n'.join(L),encoding='utf-8')
print('env',sc,sd,shadow,op,amb['pixels_sha256'][:8])
# shader
s=(dst/'room_lighting_shader.h').read_text()
s=s.replace('/* Source positions/colors/ranges; authored Lambert/linear falloff and ambient.\n * Native tone mapping, ambient cubes, and final shader equivalence are pending. */','/* Recovered terms: region cube ambient, shadow color, sun, native point attenuation.\n * Not implemented: specular, SSAO, shadow maps, fog, bloom, color correction. */')
s=s.replace('uniform vec4 room_position_inner[36];','uniform samplerCube room_cube;uniform vec3 room_sun_color;uniform vec3 room_sun_direction;uniform vec4 room_shadow_color;uniform vec4 room_position_inner[36];')
s=s.replace('else{illumination=vec3(0.12);for','else{float sunTerm=clamp(dot(N,room_sun_direction),0.0,1.0);illumination=texture(room_cube,N.xzy).rgb+(1.0-sunTerm)*room_shadow_color.rgb+room_sun_color*sunTerm;for')
assert 'room_cube,N.xzy' in s
(dst/'room_lighting_shader.h').write_text(s)
h=(dst/'room_lighting.h').read_text().replace('typedef struct opem_room_lighting {GLint mode,number,position_inner,color_outer;}','typedef struct opem_room_lighting {GLint mode,number,position_inner,color_outer,cube_sampler,sun_color,sun_direction,shadow_color;GLuint cube;}')
h=h.replace('const char *opem_room_lighting_identity(void);','void opem_room_lighting_close(opem_room_lighting *);\nconst char *opem_room_lighting_identity(void);')
(dst/'room_lighting.h').write_text(h)
c=(dst/'room_lighting.c').read_text()
c=c.replace('#include "room_lights.inc"','#include "room_lights.inc"\n#include "room_environment.inc"')
c=c.replace('return s->mode>=0&&s->number>=0&&s->position_inner>=0&&s->color_outer>=0;','''s->cube_sampler=glGetUniformLocation(program,"room_cube");s->sun_color=glGetUniformLocation(program,"room_sun_color");s->sun_direction=glGetUniformLocation(program,"room_sun_direction");s->shadow_color=glGetUniformLocation(program,"room_shadow_color");
 {unsigned f;glGenTextures(1,&s->cube);glActiveTexture(GL_TEXTURE1);glBindTexture(GL_TEXTURE_CUBE_MAP,s->cube);glPixelStorei(GL_UNPACK_ALIGNMENT,1);for(f=0;f<6;f++)glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+f,0,GL_RGBA8,8,8,0,GL_RGBA,GL_UNSIGNED_BYTE,opem_env_cube[f]);glPixelStorei(GL_UNPACK_ALIGNMENT,4);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_R,GL_CLAMP_TO_EDGE);glActiveTexture(GL_TEXTURE0);}
 return s->mode>=0&&s->number>=0&&s->position_inner>=0&&s->color_outer>=0&&s->cube_sampler>=0&&s->sun_color>=0&&s->sun_direction>=0&&s->shadow_color>=0&&s->cube;''')
c=c.replace('glUniform1i(s->number,OPEM_ROOM_LIGHT_COUNT);if(!mode)return;','glUniform1i(s->number,OPEM_ROOM_LIGHT_COUNT);if(!mode)return;\n glActiveTexture(GL_TEXTURE1);glBindTexture(GL_TEXTURE_CUBE_MAP,s->cube);glActiveTexture(GL_TEXTURE0);glUniform1i(s->cube_sampler,1);glUniform3fv(s->sun_color,1,opem_env_sun_color);glUniform3fv(s->sun_direction,1,opem_env_sun_direction);glUniform4fv(s->shadow_color,1,opem_env_shadow_color);')
c+='void opem_room_lighting_close(opem_room_lighting *s){if(s->cube)glDeleteTextures(1,&s->cube);s->cube=0;}\n'
(dst/'room_lighting.c').write_text(c)
a=(dst/'android_scene.c').read_text()
a=a.replace('if(g->program)glDeleteProgram(g->program);','opem_room_lighting_close(&g->room_lights);if(g->program)glDeleteProgram(g->program);');assert 'opem_room_lighting_close' in a
a=a.replace('shader_equation=authored_linear_Lambert ambient_fallback=0.12 native_global_preset_pending=1','shader_equation=recovered_cube_shadow_sun_point native_parity=0')
(dst/'android_scene.c').write_text(a)
m=(dst/'AndroidManifest.xml').read_text().replace('android:versionCode="14" android:versionName="0.14.0"','android:versionCode="15" android:versionName="0.15.0"');(dst/'AndroidManifest.xml').write_text(m)
cm=(dst/'CMakeLists.txt').read_text().replace('VERSION 0.14.0','VERSION 0.15.0');(dst/'CMakeLists.txt').write_text(cm)
for f in ('package_android.py','verify_android_package_inputs.py','build_validate.cmd','build_windows_android.cmd'):
    t=(dst/f).read_bytes().decode('utf-8')
    t=t.replace('work/v18-host','work/v19-host').replace('work\\v18-host','work\\v19-host').replace('v18-apk','v19-apk').replace("'outputs/scene-v18'","'outputs/scene-v19'").replace('outputs/scene-v18','outputs/scene-v19').replace('outputs\\scene-v18','outputs\\scene-v19').replace('opem-amalur-scene-v0.14','opem-amalur-scene-v0.15')
    (dst/f).write_bytes(t.encode('utf-8'))
print([str(x.name) for x in dst.iterdir()][:6],'v18 sha',hashlib.sha256(open('work/v18-host/room_lighting.c','rb').read()).hexdigest()[:8])
