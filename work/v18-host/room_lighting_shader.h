#ifndef OPEM_ROOM_LIGHTING_SHADER_H
#define OPEM_ROOM_LIGHTING_SHADER_H
/* Source positions/colors/ranges; authored Lambert/linear falloff and ambient.
 * Native tone mapping, ambient cubes, and final shader equivalence are pending. */
static const char opem_room_fragment[]=
 "#version 300 es\nprecision highp float;\n"
 "in vec3 normal;in vec3 color;in vec2 uv;in vec3 world_position;"
 "uniform int has_texture;uniform sampler2D base_texture;"
 "uniform int room_mode;uniform int room_light_count;"
 "uniform vec4 room_position_inner[36];uniform vec4 room_color_outer[36];"
 "out vec4 outColor;void main(){"
 "float n=length(normal);vec3 N=n>0.000001?normal/n:vec3(0.0);"
 "vec3 base=has_texture!=0?texture(base_texture,uv).rgb:color;vec3 illumination;"
 "if(room_mode==0){float light=0.35+0.65*max(dot(N,normalize(vec3(0.35,-0.2,0.9))),0.0);illumination=vec3(light);}"
 "else{illumination=vec3(0.12);for(int i=0;i<36;i++){if(i>=room_light_count)break;"
 "vec3 delta=room_position_inner[i].xyz-world_position;float d2=dot(delta,delta);float outer=room_color_outer[i].w;"
 "if(d2>=outer*outer)continue;float invDistance=inversesqrt(max(d2,0.000001));float rangeDistance=d2*invDistance;"
 "float attenuation=clamp((outer-rangeDistance)/max(outer-room_position_inner[i].w,0.000001),0.0,1.0);"
 "illumination+=room_color_outer[i].rgb*(attenuation*max(dot(N,delta*invDistance),0.0));}}"
 "outColor=vec4(clamp(clamp(base,0.0,1.0)*illumination,0.0,1.0),1.0);}";
#endif
