#version 300 es
precision highp float;precision highp sampler2D;precision highp samplerCube;
// Source-correlated active G-buffer material contracts. GLES3-compatible helper.
// Modified mask: SPV924, shipped e64a1080a0176273.
// Vertexblend: SPV904, shipped ee25c36fd1dec8db.
// Trunk: captured source-VB identity -> SPV884, shipped3cec76619974c89f.
struct OANativeSample {vec3 albedo;vec3 normal;float specular;float gloss;};
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
 result.specular=clamp(mix(texture(s1,uv1).g,texture(s2,uv2).g,weight)*specularValues.x,0.0,1.0);
 result.gloss=specularValues.y;
 return result;
}
OANativeSample oaNativeTrunk(sampler2D diffuseMap,sampler2D specularMap,sampler2D normalMap,vec2 uv,vec4 vertexColor,vec3 N,vec3 T,vec3 B,vec4 specularValues){
 vec4 normal=texture(normalMap,uv);OANativeSample result;
 result.normal=oaNativeFrameNormal(vec2(normal.r*normal.a,normal.g),N,T,B);
 result.albedo=clamp(texture(diffuseMap,uv).rgb*vertexColor.rgb,0.0,1.0);
 result.specular=clamp(texture(specularMap,uv).g*specularValues.x,0.0,1.0);
 result.gloss=specularValues.y;return result;
}
// Native ambient uses raw specular before G-buffer clamping for q.
// For authored strength .924/1 and UNORM masks, q<=.9 so returned sample is equivalent.
vec3 oaNativeAmbient(OANativeSample s,samplerCube cube,vec3 V,vec4 sky,vec2 ambientScales){
 float q=s.specular*ambientScales.y;vec3 R=reflect(-V,s.normal);
 return clamp((1.0-clamp(q,0.0,1.0))*texture(cube,s.normal.xzy).rgb*s.albedo+q*sky.rgb*pow(clamp(R.z,0.0,1.0),sky.a*ambientScales.x),0.0,1.0);
}
// Deferred specular exponent is returnedGloss*.25; apply full recovered deferred lighting.
// These helpers recover material/ambient outputs and do not claim full shadow/AO parity.

out vec4 color;void main(){color=vec4(0);}
