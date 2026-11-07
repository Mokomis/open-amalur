from pathlib import Path
import json
R=Path(__file__).resolve().parent;s=(R/'river_native.glsl').read_text();uv=s[s.index('void oaRiverUV'):s.index('vec4 oaNativeRiver')]
vs='''#version 300 es
precision highp float;
layout(location=0)in vec3 position;layout(location=1)in vec2 uv;layout(location=2)in vec3 n;layout(location=3)in vec3 t;layout(location=4)in vec3 b;layout(location=5)in vec4 color;
uniform mat4 vp;uniform vec4 m[6];uniform float time;
out vec3 W,N,T,B;out vec4 C,clip;out vec2 U0,U1,U2,U3;
'''+uv+'''void main(){vec4 q=vp*vec4(position,1.0);gl_Position=q;clip=vec4(q.xy,.5*(q.z+q.w),q.w);W=position;N=n;T=t;B=b;C=color;oaRiverUV(uv,time,m,U0,U1,U2,U3);}
'''
fs='''#version 300 es
precision highp float;precision highp sampler2D;precision highp samplerCube;
in vec3 W,N,T,B;in vec4 C,clip;in vec2 U0,U1,U2,U3;
uniform sampler2D baseMap,normalMap,foamMap,detailMap,refractionMap,sceneColor,sceneDepth;
uniform samplerCube probeCube,ambientCube;uniform vec4 m[6],lightData[8],globalTint,lumFactors;uniform vec3 eye,sunDirection,sunColor,shadowColor,waterFog,lumTint;uniform vec2 invDepth;uniform bool pointLights;out vec4 outputColor;
'''+s+'''void main(){outputColor=oaNativeRiver(baseMap,normalMap,foamMap,detailMap,refractionMap,sceneColor,sceneDepth,probeCube,ambientCube,m,U0,U1,U2,U3,W,eye,N,T,B,C.r,clip,invDepth,sunDirection,sunColor,shadowColor,waterFog,lightData,pointLights,true,globalTint,lumFactors,lumTint);}
'''
(R/'evidence/native-water.vert').write_text(vs);(R/'evidence/native-water.frag').write_text(fs)
body=(R/'module_body.c').read_text().replace('for(i=0;i<s->nt;i++){if(s->t[i].gpu)','for(i=0;s->t&&i<s->nt;i++){if(s->t[i].gpu)').replace('for(i=0;i<s->nm;i++){mesh*m=s->m+i;if(m->vao)','for(i=0;s->m&&i<s->nm;i++){mesh*m=s->m+i;if(m->vao)')
(R/'oa_native_water.c').write_text('#include "oa_native_water.h"\n#include <stdint.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\nstatic const char water_vs[]='+json.dumps(vs)+';\nstatic const char water_fs[]='+json.dumps(fs)+';\n'+body)
