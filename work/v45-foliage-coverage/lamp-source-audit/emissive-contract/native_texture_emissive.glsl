// Captured PS838 / VS837 textureemissive, material654012.
// N0/TW/BW are raw interpolated per-vertex-normalized basis vectors.
struct OANativeEmissiveSample {vec3 normal;vec3 baseRaw;float rawSpec;float specular;float gloss;vec3 emission;};
OANativeEmissiveSample oaNativeTextureEmissive(vec4 diffuse,vec4 normalMap,vec4 specularMap,vec4 emissiveMask,vec4 vertexColor,vec3 N0,vec3 TW,vec3 BW,vec3 emissiveRGB,vec4 specularValues){
 OANativeEmissiveSample r;vec2 xy=2.*vec2(normalMap.r*normalMap.a,normalMap.g)-1.;float z=sqrt(clamp(1.-dot(xy,xy),0.,1.));
 r.normal=normalize(xy.x*TW+xy.y*BW+z*N0);
 r.baseRaw=(diffuse.rgb*vertexColor.rgb)*vertexColor.a;
 r.rawSpec=specularMap.g*specularValues.x;r.specular=clamp(r.rawSpec*vertexColor.a,0.,1.);r.gloss=specularValues.y;
 r.emission=((emissiveMask.g*diffuse.rgb)*emissiveRGB)*specularValues.z;
 return r;
}
vec3 oaNativeTextureEmissiveG2(OANativeEmissiveSample s,vec3 cubeRGB,vec3 V,vec4 sky,vec2 ambientScales){
 float q=s.rawSpec*ambientScales.y;vec3 R=reflect(-V,s.normal);
 return clamp((1.-clamp(q,0.,1.))*cubeRGB*s.baseRaw+q*sky.rgb*pow(clamp(R.z,0.,1.),sky.a*ambientScales.x)+s.emission,0.,1.);
}
// G0=(normal*.5+.5,gloss), G1=(clamp(baseRaw),specular), G2=(above,shift).
// Store/round to native HALF, then use ordinary deferred combine/AO and fog.
// UV=sourceUV+gameTime*profileUV.zw; profileUV.xy unity, scroll0 for654012.
