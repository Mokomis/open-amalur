#version 300 es
precision highp float;
out vec4 o;
/* Active fragment1895, phase106/draw72932. All inputs are the native
 * sampled/quantized G-buffer values. N and I are normalized; I points FROM
 * camera TO fragment (use -normalize(eye-W)). Do not use the surface-to-eye
 * vector directly in reflect(). g0.a is storedGloss; g1.a specular strength;
 * g2.a>.5 is native wrapped-diffuse flag, not surface opacity.
 * aoShadow=(AO,shadow), native backlight=.11999999731779099.
 */
vec3 oa_native_deferred_combine(vec3 N,vec3 I,vec4 g0,vec4 g1,vec4 g2,
 vec4 localLight,vec2 aoShadow,vec3 sunDir,vec3 sunColor,
 vec4 shadowColor,float backlightScale){
 float d=dot(N,sunDir);
 vec3 R=reflect(I,N);
 float reflected=dot(sunDir,R),power=g0.a*.25;
 vec2 lobes=pow(max(clamp(vec2(reflected,-reflected),0.,1.),vec2(.00001)),vec2(power));
 lobes.x*=d>=0.?1.:0.;
 float backscale=aoShadow.x*backlightScale;
 lobes.y*=backscale;
 bool wrap=g2.a>.5;
 float lambert=clamp(d+(wrap?.5239999890327454:0.),0.,1.)*(wrap?.6561679840087891:1.);
 float front=min(lambert,1.+shadowColor.a*(aoShadow.y-1.));
 float direct=front+clamp(-d,0.,1.)*backscale;
 float sunSpec=lobes.x*direct+lobes.y;
 vec3 shadowAmbient=(1.-front)*shadowColor.rgb;
 vec3 localSpec=localLight.a*localLight.rgb/(dot(localLight.rgb,vec3(.2126,.7152,.0722))+1.0000000116860974e-7);
 return (shadowAmbient*g1.rgb+g2.rgb)*aoShadow.x+
        (sunColor*direct+localLight.rgb)*g1.rgb+
        (sunColor*sunSpec+localSpec)*g1.a;
}

void main(){o=vec4(oa_native_deferred_combine(vec3(0,0,1),vec3(0,0,-1),vec4(0),vec4(1),vec4(0),vec4(0),vec2(1),vec3(0,0,1),vec3(1),vec4(0),.12),1.);}