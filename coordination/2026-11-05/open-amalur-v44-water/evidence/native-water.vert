#version 300 es
precision highp float;
layout(location=0)in vec3 position;layout(location=1)in vec2 uv;layout(location=2)in vec3 n;layout(location=3)in vec3 t;layout(location=4)in vec3 b;layout(location=5)in vec4 color;
uniform mat4 vp;uniform vec4 m[6];uniform float time;
out vec3 W,N,T,B;out vec4 C,clip;out vec2 U0,U1,U2,U3;
void oaRiverUV(vec2 uv,float time,vec4 m[6],out vec2 baseUV,out vec2 foamUV,out vec2 detailUV,out vec2 refractionUV) {
    baseUV=uv+time*vec2(m[0].w,m[1].x)*m[0].x;
    vec2 scrollingFoamUV=uv+vec2(time*m[1].y,0.0);
    foamUV=scrollingFoamUV*m[0].z;
    detailUV=scrollingFoamUV*m[0].y;
    refractionUV=uv+time*m[1].zw;
}
void main(){vec4 q=vp*vec4(position,1.0);gl_Position=q;clip=vec4(q.xy,.5*(q.z+q.w),q.w);W=position;N=n;T=t;B=b;C=color;oaRiverUV(uv,time,m,U0,U1,U2,U3);}
