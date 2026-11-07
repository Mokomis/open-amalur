#version 300 es
#define OA_DIAGNOSTIC 1
#define OA_CHARACTER_MATERIALS 1
#define VARIANT 0
#define LIGHT_VEC4 226
#ifdef OA_DIAGNOSTIC
uniform int oa_probe;
#endif
precision highp float;precision highp int;precision highp sampler2D;precision highp samplerCube;precision highp sampler2DShadow;precision highp usampler2D;in vec3 W;in highp vec3 N0;in vec2 UV;in highp float F;in highp float VA;in highp vec4 VC;in highp vec3 TW,BW;in vec2 UV2;flat in highp uint PW;
uniform sampler2D t0,t1,t2,t3,t4,t5,t6,t7,ambient_occlusion;uniform int native_ao_on,depth_only,geometry_kind,native_alpha_slot;uniform samplerCube cube,native_reflection_cube;uniform highp vec3 reflection_environment_tint;uniform sampler2DShadow shadow_map;uniform usampler2D light_grid;uniform mat4 shadow_matrix;uniform int shadow_on,features;uniform ivec2 grid_size;
uniform vec3 eye,sun_dir,grid;uniform highp vec3 sun_color,shadow_color,fog_color;uniform highp float alpha_cut;uniform vec2 fog;uniform float game_time;uniform int material_family;uniform vec4 material_color,material_specular,material_tiling,sky_light;uniform vec2 ambient_scales;uniform float water[11];layout(std140)uniform Lights{vec4 L[LIGHT_VEC4];};out highp vec4 o;
#if VARIANT==1
uniform sampler2D terrain_paint;uniform usampler2D terrain_selector;uniform int terrain_map_ready,terrain_supported_sets,terrain_draw_set;uniform vec4 terrain_uv_scales;uniform float terrain_height_blend;uniform vec4 terrain_specular_levels,terrain_specular_powers;
#endif
#if VARIANT==0||VARIANT==1||VARIANT==2||VARIANT==3
#define SPEC 1
#else
#define SPEC 0
#endif
highp vec3 N,illum,material_emission;
#if SPEC
highp vec3 V,spec_sum;highp float spec=0.0,spec_gain=0.0,spec_power=32.0;
#endif
#if VARIANT!=6
vec3 perturb(vec3 n,vec3 m){if(material_family==7)return normalize(TW*m.x+BW*m.y+N0*m.z);if(geometry_kind==1)return normalize(BW*m.x+TW*m.y+n*m.z);if(geometry_kind==2&&dot(TW,TW)>.1)return normalize(TW*m.x+BW*m.y+n*m.z);vec3 dp1=dFdx(W),dp2=dFdy(W);vec2 du=dFdx(UV),dv=dFdy(UV);vec3 a=cross(dp2,n),b=cross(n,dp1);vec3 T=a*du.x+b*dv.x,B=a*du.y+b*dv.y;float k=inversesqrt(max(max(dot(T,T),dot(B,B)),1e-12));return normalize(T*k*m.x+B*k*m.y+n*m.z);}
highp vec3 unpack(highp vec4 s){highp vec2 xy=vec2(s.r*s.a,s.g)*2.0-1.0;return vec3(xy,sqrt(clamp(1.0-dot(xy,xy),0.0,1.0)));}
#endif
#if SPEC
highp vec4 native_point_sum;
highp vec4 oaNativePointHalf4(highp vec4 x){
 return vec4(unpackHalf2x16(packHalf2x16(x.xy)),
             unpackHalf2x16(packHalf2x16(x.zw)));
}
#endif
void light(uint id){
 int i=int(id)*2;
 vec3 D=L[i].xyz-W;
 float d2=dot(D,D),e=L[i+1].w;
 if(d2>=e*e)return;
#if SPEC
 if((features&128)!=0&&material_family>0){
  /* Native lightPosition.w=-1/(outer-inner), lightColor.w=outer/(outer-inner).
   * Equivalent linear sphere attenuation, no squared/Gaussian law. Native
   * has no special zero-distance/zero-width authoring fallback. */
  float dist=sqrt(d2);
  vec3 Ld=D*inversesqrt(d2);
  float width=e-L[i].w;
  float at=clamp(dist*(-1./width)+e/width,0.,1.);
  vec3 lightColor=L[i+1].rgb;
  float nl=clamp(dot(N,Ld),0.,1.);
  float reflected=clamp(dot(Ld,reflect(-V,N)),0.,1.);
  float lobe=exp2(log2(max(reflected,.00001))*spec_power);
  vec3 rgb=(nl*lightColor)*at;
  vec3 specRGB=((nl*lobe)*lightColor)*at;
  float a=dot(specRGB,vec3(.2126,.7152,.0722));
  /* F16 RMW happens AFTER adding this unquantized shader contribution.
   * Do NOT half-round each contribution before addition or only the final
   * total. Original target rounds after each accepted additive light draw. */
  native_point_sum=oaNativePointHalf4(native_point_sum+vec4(rgb,a));
  return;
 }
#endif
 /* Exact current legacy branch retained when native bit128 is off. */
 float inv=inversesqrt(max(d2,1e-6));
 highp float at=clamp((e-d2*inv)/max(e-L[i].w,1e-6),0.,1.);
 highp vec3 Ld=D*inv,c=L[i+1].rgb*at;
 illum+=c*max(dot(N,Ld),0.);
#if SPEC
 if(material_family>0&&(features&16)!=0)
  spec_sum+=c*(pow(max(clamp(dot(Ld,reflect(-V,N)),0.,1.),.00001),spec_power)*spec_gain);
 else if(spec>.02)
  spec_sum+=c*(pow(max(dot(N,normalize(V+Ld)),0.),32.)*spec);
#endif
}
void point_lights(){ivec2 g2=clamp(ivec2(floor((W.xy-grid.xy)*grid.z)),ivec2(0),grid_size-1);uvec4 a=texelFetch(light_grid,ivec2(g2.x*2,g2.y),0);if(a.x!=65535u){light(a.x);if(a.y!=65535u){light(a.y);if(a.z!=65535u){light(a.z);if(a.w!=65535u){light(a.w);uvec4 b=texelFetch(light_grid,ivec2(g2.x*2+1,g2.y),0);if(b.x!=65535u){light(b.x);if(b.y!=65535u){light(b.y);if(b.z!=65535u){light(b.z);if(b.w!=65535u)light(b.w);}}}}}}}}
// Source-correlated active G-buffer material contracts. GLES3-compatible helper.
// Modified mask: SPV924, shipped e64a1080a0176273.
// Vertexblend: SPV904, shipped ee25c36fd1dec8db.
// Trunk: captured source-VB identity -> SPV884, shipped3cec76619974c89f.
struct OANativeSample {vec3 albedo;vec3 normal;float specular;float rawSpecular;float gloss;};
vec3 oaNativeFrameNormal(vec2 encoded,vec3 N,vec3 T,vec3 B){
 vec2 xy=encoded*2.0-1.0;float z=sqrt(clamp(1.0-dot(xy,xy),0.0,1.0));
 return normalize(xy.x*T+xy.y*B+z*N);
}
OANativeSample oaNativeVertexBlend(sampler2D d1,sampler2D maskMap,sampler2D s1,sampler2D n1,sampler2D d2,sampler2D s2,sampler2D n2,vec2 uv,vec4 vertexColor,vec3 N,vec3 T,vec3 B,vec4 specularValues,vec4 tiling,bool modifiedMask){
 vec2 uv1=uv*tiling.xy,uv2=uv*tiling.zw;
 float weight=vertexColor.a;
 if(modifiedMask){float low=clamp(2.0*weight,0.0,1.0),high=clamp(2.0*weight-1.0,0.0,1.0);weight=texture(maskMap,uv1).g*(low-high)+high;}
 vec4 a=texture(n1,uv1),b=texture(n2,uv2);
 vec2 encoded=mix(vec2(a.r*a.a,a.g),vec2(b.r*b.a,b.g),weight);
 OANativeSample result;
 result.normal=oaNativeFrameNormal(encoded,N,T,B);
 result.albedo=clamp(mix(texture(d1,uv1).rgb,texture(d2,uv2).rgb,weight)*vertexColor.rgb,0.0,1.0);
 result.rawSpecular=mix(texture(s1,uv1).g,texture(s2,uv2).g,weight)*specularValues.x;result.specular=clamp(result.rawSpecular,0.0,1.0);
 result.gloss=specularValues.y;
 return result;
}
OANativeSample oaNativeTrunk(sampler2D diffuseMap,sampler2D specularMap,sampler2D normalMap,vec2 uv,vec4 vertexColor,vec3 N,vec3 T,vec3 B,vec4 specularValues){
 vec4 normal=texture(normalMap,uv);OANativeSample result;
 result.normal=oaNativeFrameNormal(vec2(normal.r*normal.a,normal.g),N,T,B);
 result.albedo=clamp(texture(diffuseMap,uv).rgb*vertexColor.rgb,0.0,1.0);
 result.rawSpecular=texture(specularMap,uv).g*specularValues.x;result.specular=clamp(result.rawSpecular,0.0,1.0);
 result.gloss=specularValues.y;return result;
}
// Native ambient uses raw specular before G-buffer clamping for q.
// rawSpecular remains available separately from saturated G-buffer specular.
vec3 oaNativeAmbient(OANativeSample s,samplerCube cube,vec3 V,vec4 sky,vec2 ambientScales){
 float q=s.rawSpecular*ambientScales.y;vec3 R=reflect(-V,s.normal);
 return clamp((1.0-clamp(q,0.0,1.0))*texture(cube,s.normal.xzy).rgb*s.albedo+q*sky.rgb*pow(clamp(R.z,0.0,1.0),sky.a*ambientScales.x),0.0,1.0);
}
// Deferred specular exponent is returnedGloss*.25; apply full recovered deferred lighting.
// These helpers recover material/ambient outputs and do not claim full shadow/AO parity.
vec3 oa_half3(vec3 x){vec2 a=unpackHalf2x16(packHalf2x16(x.xy));vec2 b=unpackHalf2x16(packHalf2x16(vec2(x.z,0.)));return vec3(a,b.x);}
float oa_half1(float x){return unpackHalf2x16(packHalf2x16(vec2(x,0.))).x;}
void main(){N=normalize(N0);material_emission=vec3(0.);
#if VARIANT==3
if((features&128)!=0&&geometry_kind==1){int rb=(int((PW>>8u)&255u)<<24)>>24;float dist=length(W.xy-eye.xy)-float(rb)*1500.*(.5/255.);float keep=1.-clamp(.0006666666595265*dist-2.33333325386,0.,1.);float noise=texture(t7,W.xy*.02).g;keep=keep*(1.-noise*keep)+keep*noise;if(texture(t2,UV).g*keep<alpha_cut)discard;}
#endif
#if VARIANT==1
{vec2 mp=(W.xy+102425.0)*.02;ivec2 tile=ivec2(floor(mp));int picked=7;bool use_native=terrain_map_ready!=0&&(features&32)!=0;
if(use_native&&all(greaterThanEqual(tile,ivec2(0)))&&all(lessThan(tile,ivec2(4096)))){uint code=texelFetch(terrain_selector,tile,0).r;vec2 q=fract(mp);bool first=(code&64u)!=0u?q.x+q.y<=1.0:q.y<=q.x;picked=int(first?(code&7u):((code>>3u)&7u));if(picked>=5||(terrain_supported_sets&(1<<picked))==0)picked=7;}
if(terrain_draw_set< -1)discard;if(terrain_draw_set>=0){if(!use_native||picked!=terrain_draw_set)discard;}else if(use_native&&picked<5)discard;}
#endif
if(depth_only!=0){
#if VARIANT==2||VARIANT==3
if((native_alpha_slot==6?texture(t6,UV).g:(material_family==5||material_family==6||material_family==10)?texture(t2,UV).g:texture(t0,UV).a)<alpha_cut)discard;
#endif
o=vec4(0.);return;}
#if VARIANT==4
{vec3 E=eye-W;float len=length(E);highp vec3 Vw=E/len;highp float keep=1.0-clamp((len-E.z)/(E.z*water[6]),0.0,1.0);vec2 uv1=UV*water[0]+water[2]*game_time;vec2 uv2=UV*water[1]+water[3]*game_time*vec2(0.9,1.1);highp vec3 m=normalize(unpack(texture(t1,uv1))+unpack(texture(t3,uv2))*water[5]);N=perturb(N,m);highp vec3 b=texture(t0,uv1).rgb;highp float sm=texture(t2,uv1).g*texture(t4,uv2).g;highp vec3 R=reflect(-Vw,N);highp vec3 env=(texture(cube,R.xzy).rgb-b)*vec3(water[7],water[8],water[9]);highp float nl=clamp(dot(N,sun_dir),0.0,1.0);highp float sp=pow(clamp(dot(sun_dir,R),0.00001,1.0),20.0);illum=sun_color*nl+texture(cube,N.xzy).rgb+(1.0-nl)*shadow_color;if((features&8)!=0)point_lights();o=vec4(b*illum+sun_color*(sp*nl*sm)+env*water[10],keep*water[4]);return;}
#elif VARIANT==5
{vec3 E=eye-W;highp vec3 Vw=normalize(E);vec2 uv1=UV+vec2(water[0],water[1])*game_time;vec2 uv2=UV+vec2(water[2],water[3])*game_time;highp float al=texture(t2,uv1).g*texture(t3,uv2).g*VA;if(al<0.004)discard;highp vec3 b=texture(t0,uv1).rgb*texture(t1,uv2).rgb;N=perturb(N,normalize(unpack(texture(t4,uv1))+unpack(texture(t5,uv2))));highp float nl=clamp(dot(N,sun_dir),0.0,1.0);highp vec3 R=reflect(-Vw,N);highp float sp=pow(clamp(dot(sun_dir,R),0.00001,1.0),water[5]*0.25);illum=sun_color*nl+texture(cube,N.xzy).rgb+(1.0-nl)*shadow_color;if((features&8)!=0)point_lights();o=vec4(b*illum+sun_color*(sp*nl*water[4])+vec3(water[6],water[7],water[8]),al);return;}
#elif VARIANT==6
{highp vec4 d=texture(t0,UV);if(d.a<alpha_cut)discard;o=vec4(mix(d.rgb,fog_color,F),(1.0-F)*d.a);return;}
#endif
#if VARIANT<4
highp vec3 base;
#if VARIANT==1
vec2 mp=(W.xy+vec2(102425.0))*.02;ivec2 tile=ivec2(floor(mp));int picked=7;bool use_native=(features&32)!=0&&terrain_map_ready!=0;if(use_native&&all(greaterThanEqual(tile,ivec2(0)))&&all(lessThan(tile,ivec2(4096)))){uint code=texelFetch(terrain_selector,tile,0).r;vec2 q=fract(mp);bool first=(code&64u)!=0u?q.x+q.y<=1.0:q.y<=q.x;picked=int(first?(code&7u):((code>>3u)&7u));if(picked>=5||(terrain_supported_sets&(1<<picked))==0)picked=7;}if(terrain_draw_set< -1)discard;if(terrain_draw_set>=0){if(!use_native||picked!=terrain_draw_set)discard;vec4 paint=texture(terrain_paint,(mp+.5)/4097.0);float t=1.0-paint.r;vec4 w=vec4(paint.r,paint.g*t,paint.b*(1.0-paint.g*t)*t,0.0);w.w=1.0-clamp(w.x+w.y+w.z,0.0,1.0);vec4 c0=texture(t0,mp*terrain_uv_scales.x),c1=texture(t1,mp*terrain_uv_scales.y),c2=texture(t2,mp*terrain_uv_scales.z),c3=texture(t3,mp*terrain_uv_scales.w);w*=vec4(c0.a,c1.a,c2.a,c3.a);float peak=max(max(w.x,w.y),max(w.z,w.w));w=max(w-(peak-terrain_height_blend),vec4(0.0));w/=max(dot(w,vec4(1.0)),1e-6);base=(c0.rgb*w.x+c1.rgb*w.y+c2.rgb*w.z+c3.rgb*w.w)*paint.a;if((features&4)!=0){vec4 nm=texture(t4,mp*terrain_uv_scales.x)*w.x+texture(t5,mp*terrain_uv_scales.y)*w.y+texture(t6,mp*terrain_uv_scales.z)*w.z+texture(t7,mp*terrain_uv_scales.w)*w.w;N=perturb(N,nm.rgb*2.-1.);if((features&128)!=0){spec=dot(terrain_specular_levels,w)*nm.a;spec_gain=clamp(spec*paint.a,0.,1.);spec_power=dot(terrain_specular_powers,w)*.25;}}}else{if(use_native&&picked<5)discard;highp float g=smoothstep(0.62,0.9,N.z),r=smoothstep(0.42,0.7,N.z)*(1.0-g),c=max(1.0-g-r,0.0);base=texture(t0,UV).rgb*g;if(g<0.995)base+=texture(t1,UV).rgb*r+texture(t2,UV).rgb*c;if((features&4)!=0){highp vec3 m=unpack(texture(t3,UV))*g;if(g<0.995)m+=unpack(texture(t4,UV))*r+unpack(texture(t5,UV))*c;N=perturb(N,normalize(m));}}
#elif VARIANT==3
highp vec4 d=texture(t0,UV);if(((features&128)!=0&&material_family==5?texture(t2,UV).g:d.a)<alpha_cut)discard;base=d.rgb;if((features&128)!=0){base*=VC.rgb;N=perturb(N,unpack(texture(t1,UV)));spec=texture(t2,UV).r;spec_gain=clamp(spec*material_specular.x,0.,1.);spec_power=texture(t2,UV).b*material_specular.y*.25;}
#else
highp vec4 d=texture(t0,UV);
#if VARIANT==2
if((native_alpha_slot==6?texture(t6,UV).g:material_family==6?texture(t2,UV).g:d.a)<alpha_cut)discard;
#endif
base=d.rgb;if(material_family==6&&(features&128)!=0)base*=VC.rgb;else if(material_family>0&&(features&16)!=0)base*=material_color.rgb*VC.rgb;if(material_family==6&&(features&128)!=0){vec3 mapped=perturb(N0,unpack(texture(t1,UV)));N=mapped+(N0-mapped)*material_color.z;spec=(1.-material_specular.x)*.30000001192092896;spec_gain=clamp(spec,0.,1.);spec_power=16.;}else if(material_family==8&&(features&128)!=0){base=d.rgb*VC.rgb*VC.a;vec3 nm=unpack(texture(t1,UV));N=normalize(TW*nm.x+BW*nm.y+N0*nm.z);spec=texture(t2,UV).g*material_specular.x;spec_gain=clamp(spec*VC.a,0.,1.);spec_power=material_specular.y*.25;material_emission=texture(t3,UV).g*d.rgb*material_color.rgb*material_specular.z;}else if(material_family==9&&(features&128)!=0){vec3 nm=unpack(texture(t1,UV));N=normalize(TW*nm.x+BW*nm.y+N0*nm.z);vec3 vv=normalize(eye-W);float facing=max(abs(dot(N,vv)),.00001);float fresnel=1.-clamp(exp2(log2(facing)*material_specular.z)*material_specular.w,0.,1.);float rho=fresnel*texture(t3,UV).g*VC.a*material_tiling.z;base=d.rgb*VC.rgb*(1.-rho);spec=texture(t2,UV).g*material_specular.x;spec_gain=clamp(spec,0.,1.);spec_power=material_specular.y*.25;material_emission=rho*texture(native_reflection_cube,reflect(-vv,N).xzy).rgb*material_color.rgb*reflection_environment_tint;}else if(material_family==11&&(features&128)!=0){vec3 nm=unpack(texture(t1,UV));N=normalize(TW*nm.x+BW*nm.y+N0*nm.z);vec3 vv=normalize(eye-W);float rho=texture(t3,UV).g*VC.a*material_tiling.z;base=d.rgb*VC.rgb*(1.-rho);spec=texture(t2,UV).g*material_specular.x;spec_gain=clamp(spec,0.,1.);spec_power=material_specular.y*.25;material_emission=rho*texture(native_reflection_cube,reflect(-vv,N).xzy).rgb*material_color.rgb*reflection_environment_tint;}
#ifdef OA_CHARACTER_MATERIALS
else if(material_family==12&&(features&128)!=0){vec3 nm=unpack(texture(t1,UV));N=normalize(TW*nm.x+BW*nm.y+N0*nm.z);vec3 vv=normalize(eye-W);float rim=clamp(material_specular.w*pow(1.-clamp(dot(N,vv),0.,1.),material_tiling.z),0.,1.);base=(d.rgb+vec3(material_specular.z*rim))*VC.rgb*VC.a;spec=texture(t2,UV).g*material_specular.x;spec_gain=clamp(spec*VC.a,0.,1.);spec_power=material_specular.y*.25;}
#endif
else if(material_family>=2&&material_family<=4&&(features&128)!=0){OANativeSample ns;if(material_family==2)ns=oaNativeTrunk(t0,t2,t1,UV,VC,N,normalize(TW),normalize(BW),material_specular);else ns=oaNativeVertexBlend(t0,t6,t2,t1,t3,t5,t4,UV,VC,material_family==3?N0:N,material_family==3?TW:normalize(TW),material_family==3?BW:normalize(BW),material_specular,material_tiling,material_family==4);base=ns.albedo;N=ns.normal;spec=material_specular.x!=0.?ns.rawSpecular/material_specular.x:0.;spec_gain=ns.specular;spec_power=ns.gloss*.25;}else if((features&4)!=0){N=perturb(N,unpack(texture(t1,UV)));spec=texture(t2,UV).r;if(material_family>0&&(features&16)!=0){spec_gain=clamp(spec*material_specular.x,0.0,1.0);spec_power=texture(t2,UV).b*material_specular.y*.25;}}
#endif
#ifdef OA_DIAGNOSTIC
if(oa_probe>0){vec3 probe=oa_probe==1?N*.5+.5:oa_probe==2?base:oa_probe==3?VC.rgb:oa_probe==4?texture(t0,UV).rgb:texture(cube,N.xzy).rgb*base;o=vec4(probe,1.);return;}
#endif
highp float sunTerm=clamp(dot(N,sun_dir),0.0,1.0);if(shadow_on!=0&&sunTerm>0.0){vec4 q=shadow_matrix*vec4(W,1.0);vec3 s=q.xyz*0.5+0.5;if(s.x>0.0&&s.x<1.0&&s.y>0.0&&s.y<1.0&&s.z<1.0){float t=0.00049;sunTerm*=(texture(shadow_map,vec3(s.xy+vec2(-t,-t),s.z))+texture(shadow_map,vec3(s.xy+vec2(t,-t),s.z))+texture(shadow_map,vec3(s.xy+vec2(-t,t),s.z))+texture(shadow_map,vec3(s.xy+vec2(t,t),s.z)))*0.25;}}
illum=texture(cube,N.xzy).rgb+(1.0-sunTerm)*shadow_color+sun_color*sunTerm;
#if SPEC
V=normalize(eye-W);spec_sum=vec3(0.0);if(material_family>0&&(features&16)!=0)spec_sum=sun_color*(pow(max(clamp(dot(sun_dir,reflect(-V,N)),0.0,1.0),.00001),spec_power)*sunTerm*spec_gain);else if(spec>0.02)spec_sum=sun_color*(pow(max(dot(N,normalize(V+sun_dir)),0.0),32.0)*sunTerm*spec);
#endif
if((features&8)!=0&&(features&128)==0)point_lights();
highp vec3 lit=base*illum;
#if SPEC
lit+=spec_sum*((material_family>0&&(features&16)!=0)?1.0:.9);
if(material_family>0&&(features&16)!=0){highp float q=spec*((material_family==6||material_family==8)?1.:material_specular.x)*ambient_scales.y;highp vec3 a=texture(cube,N.xzy).rgb;highp vec3 R=reflect(-V,N);highp vec3 recovered=clamp((1.0-clamp(q,0.0,1.0))*a*base+q*sky_light.rgb*pow(clamp(R.z,0.0,1.0),sky_light.a*ambient_scales.x),0.0,1.0);lit+=recovered-base*a;}
#endif
if((features&128)!=0){vec2 ah=native_ao_on!=0?texture(ambient_occlusion,gl_FragCoord.xy/vec2(textureSize(ambient_occlusion,0))).rg:vec2(1.);vec3 materialN=N;vec3 materialBase=base;N=normalize(oa_half3(N*.5+.5)*2.-1.);base=oa_half3(clamp(base,0.,1.));
#if SPEC
spec_gain=oa_half1(spec_gain);spec_power=oa_half1(spec_power*4.)*.25;
#endif
float dn=dot(N,sun_dir);float front=min(clamp(dn,0.,1.),ah.y);float back=clamp(-dn,0.,1.)*ah.x*.11999999731779099;vec3 amb=oa_half3(clamp(texture(cube,materialN.xzy).rgb*materialBase,0.,1.));illum=vec3(0.);
#if SPEC
spec_sum=vec3(0.);native_point_sum=vec4(0.);
#endif
if((features&8)!=0)point_lights();
#if SPEC
vec3 direct=material_family>0?native_point_sum.rgb:illum;vec3 native_local_spec=native_point_sum.rgb*native_point_sum.a/(dot(native_point_sum.rgb,vec3(.2126,.7152,.0722))+1.0000000116860974e-7);
#else
vec3 direct=illum;
#endif
vec3 native_spec=vec3(0.);
#if SPEC
if(material_family>0){float q=spec*((material_family==6||material_family==8)?1.:material_specular.x)*ambient_scales.y;vec3 R=reflect(-V,N);vec3 Ra=reflect(-V,materialN);amb=oa_half3(clamp((1.-clamp(q,0.,1.))*texture(cube,materialN.xzy).rgb*materialBase+q*sky_light.rgb*pow(clamp(Ra.z,0.,1.),sky_light.a*ambient_scales.x)+material_emission,0.,1.));if(material_family==9||material_family==11)amb=oa_half3(clamp(texture(cube,materialN.xzy).rgb*materialBase+material_emission,0.,1.));
#ifdef OA_CHARACTER_MATERIALS
if(material_family==12)amb=oa_half3(clamp(texture(cube,materialN.xzy).rgb*VC.a*materialBase,0.,1.));
#endif
vec2 lobes=pow(max(clamp(vec2(dot(sun_dir,R),-dot(sun_dir,R)),0.,1.),vec2(.00001)),vec2(spec_power));lobes.x*=dn>=0.?1.:0.;float nlobes=lobes.x*(front+back)+lobes.y*ah.x*.11999999731779099;native_spec=(sun_color*nlobes+native_local_spec)*spec_gain;}else native_spec=spec_sum*.9;
#endif
lit=(amb+(1.-front)*shadow_color*base)*ah.x+(sun_color*(front+back)+direct)*base+native_spec;}
if((features&128)!=0){lit=roundEven(clamp(lit,0.,1.)*255.)/255.;float z=1./gl_FragCoord.w;float transmittance=min(exp(-(fog.x*z+fog.y)),1.);float tint=.5*pow(max(dot(normalize(W-eye),sun_dir),0.),10.);vec3 nativeFog=mix(fog_color,sun_color,tint);o=vec4(mix(nativeFog,lit,transmittance),1.);}else{o=vec4(mix(lit,fog_color,F),1.0);}
#endif
}
