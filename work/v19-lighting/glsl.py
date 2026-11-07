import re,subprocess,glob,os,ast
s=open('work/v19-host/room_lighting_shader.h').read()
b=s[s.index('opem_room_fragment[]=')+len('opem_room_fragment[]='):s.rindex(';')]
src=''.join(ast.literal_eval(x) for x in re.findall(r'"(?:[^"\\]|\\.)*"',b))
os.makedirs('outputs/scene-v19/shader-check',exist_ok=True)
p='outputs/scene-v19/shader-check/room.frag';open(p,'w').write(src)
g=glob.glob('tools/android/android-ndk-r30/shader-tools/windows-x86_64/glslc.exe')
print(g)
if g:
    src2=src.replace('#version 300 es','#version 310 es')
    src2=re.sub(r'\bin vec3 normal;in vec3 color;in vec2 uv;in vec3 world_position;','layout(location=0) in vec3 normal;layout(location=1) in vec3 color;layout(location=2) in vec2 uv;layout(location=3) in vec3 world_position;',src2)
    src2=src2.replace('out vec4 outColor;','layout(location=0) out vec4 outColor;').replace('uniform sampler2D base_texture;','layout(binding=0) uniform sampler2D base_texture;').replace('uniform samplerCube room_cube;','layout(binding=1) uniform samplerCube room_cube;')
    q=p+'.checked.frag';open(q,'w').write(src2)
    r=subprocess.run([g[0],'-fauto-map-locations','-fauto-bind-uniforms','--target-env=opengl','-fshader-stage=frag','-o','NUL',q],capture_output=True,text=True);print('glslc rc',r.returncode,r.stderr[:800])
