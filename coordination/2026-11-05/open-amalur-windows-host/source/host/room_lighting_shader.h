#ifndef OPEM_ROOM_LIGHTING_SHADER_H
#define OPEM_ROOM_LIGHTING_SHADER_H
/* Recovered terms: region cube ambient, shadow color, sun, native point attenuation.
 * Color LUT applied with the shader half-texel mapping and sRGB decoding, as measured in the running game; brightness and color_transition terms are not.
 * The sun shadow map is an authored host choice, not the game's filtering. Not implemented: specular, SSAO, fog, bloom. */
static const char opem_room_fragment[]=
 "#version 300 es\nprecision highp float;precision highp sampler3D;precision highp sampler2DShadow;\n"
 "in vec3 normal;in vec3 color;in vec2 uv;in vec3 world_position;"
 "uniform int has_texture;uniform sampler2D base_texture;uniform float alpha_cut;"
 "uniform int room_mode;uniform int room_no_lut;uniform int room_light_count;"
 "uniform sampler3D room_lut;uniform samplerCube room_cube;uniform vec3 room_sun_color;uniform vec3 room_sun_direction;uniform vec4 room_shadow_color;uniform vec4 room_position_inner[36];uniform vec4 room_color_outer[36];uniform sampler2DShadow room_shadow_map;uniform mat4 room_shadow_matrix;uniform int room_shadow_on;"
 "out vec4 outColor;void main(){"
 "float n=length(normal);vec3 N=n>0.000001?normal/n:vec3(0.0);"
 "vec4 texel=has_texture!=0?texture(base_texture,uv):vec4(color,1.0);if(texel.a<alpha_cut)discard;vec3 base=texel.rgb;vec3 illumination;"
 "if(room_mode==0){float light=0.35+0.65*max(dot(N,normalize(vec3(0.35,-0.2,0.9))),0.0);illumination=vec3(light);}"
 "else{float sunTerm=clamp(dot(N,room_sun_direction),0.0,1.0);if(room_shadow_on!=0&&sunTerm>0.0){vec4 q=room_shadow_matrix*vec4(world_position,1.0);vec3 s=q.xyz*0.5+0.5;if(s.x>0.0&&s.x<1.0&&s.y>0.0&&s.y<1.0&&s.z<1.0){float t=0.00049;float v=texture(room_shadow_map,vec3(s.xy+vec2(-t,-t),s.z))+texture(room_shadow_map,vec3(s.xy+vec2(t,-t),s.z))+texture(room_shadow_map,vec3(s.xy+vec2(-t,t),s.z))+texture(room_shadow_map,vec3(s.xy+vec2(t,t),s.z));sunTerm*=v*0.25;}}illumination=texture(room_cube,N.xzy).rgb+(1.0-sunTerm)*room_shadow_color.rgb+room_sun_color*sunTerm;for(int i=0;i<36;i++){if(i>=room_light_count)break;"
 "vec3 delta=room_position_inner[i].xyz-world_position;float d2=dot(delta,delta);float outer=room_color_outer[i].w;"
 "if(d2>=outer*outer)continue;float invDistance=inversesqrt(max(d2,0.000001));float rangeDistance=d2*invDistance;"
 "float attenuation=clamp((outer-rangeDistance)/max(outer-room_position_inner[i].w,0.000001),0.0,1.0);"
 "illumination+=room_color_outer[i].rgb*(attenuation*max(dot(N,delta*invDistance),0.0));}}"
 "vec3 lit=clamp(clamp(base,0.0,1.0)*illumination,0.0,1.0);if(room_mode!=0&&room_no_lut==0)lit=texture(room_lut,lit*0.9375+0.03125).rgb;outColor=vec4(lit,1.0);}";
#endif
