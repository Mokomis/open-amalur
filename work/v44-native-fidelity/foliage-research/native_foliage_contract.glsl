// Recovered source: capture VS893/PS894 and depth PS327; exported
// DXBC VS565c3c6abcc6eb75 / PSba5e9f9d993a0e37. No shared source changed.
// OAWF40: p@0, packedWindU32@12, UV@16, normal@24, RGBA8@36.
// These helpers describe native shader outputs, not the later light/post passes.
vec3 native_foliage_wind(vec3 p,uint packedWind,vec4 palette[64]) {
    return p+palette[int(packedWind&255u)].xyz;
}
// Run in vertex stage, then interpolate N,B,T separately. Derive the basis
// from native local baked N before any draw worldVector rotation. For emitted
// world-baked OAWF the draw worldVector is identity.
void native_foliage_basis(vec3 sourceNormal,out vec3 N,out vec3 B,out vec3 T) {
    N=normalize(sourceNormal);
    T=normalize(vec3(-sourceNormal.z,0.,sourceNormal.x));
    B=normalize(cross(sourceNormal,T));
}
struct NativeFoliageGBuffer {vec4 normalPower;vec4 diffuseSpec;vec4 ambient;};
NativeFoliageGBuffer native_foliage_gbuffer(vec2 uv,vec4 vertexColor,vec3 W,
    vec3 N0,vec3 B,vec3 T,vec3 camera,vec2 specularValues,
    float ambientSpecularScale,float ambientDiffuseScale,vec4 skyLightColor,
    float luminanceShiftId,sampler2D diffuseMap,sampler2D packedAlphaSpecMap,
    sampler2D normalMap,samplerCube ambientMap) {
    vec4 nt=texture(normalMap,uv);
    vec2 xy=vec2(nt.r*nt.a,nt.g)*2.-1.;
    vec3 N=normalize(B*xy.x+T*xy.y+N0*sqrt(clamp(1.-dot(xy,xy),0.,1.)));
    vec3 D=texture(diffuseMap,uv).rgb*vertexColor.rgb;
    vec4 aspec=texture(packedAlphaSpecMap,uv);
    float spec=aspec.r*specularValues.x;
    float power=aspec.b*specularValues.y;
    float k=spec*ambientSpecularScale;
    vec3 V=normalize(camera-W);
    vec3 R=V-2.*dot(V,N)*N;
    vec3 sky=pow(clamp(-R.z,0.,1.),skyLightColor.a*ambientDiffuseScale)*skyLightColor.rgb*k;
    vec3 ambient=texture(ambientMap,N.xzy).rgb*(1.-clamp(k,0.,1.));
    NativeFoliageGBuffer o;
    o.normalPower=vec4(N*.5+.5,power);
    o.diffuseSpec=clamp(vec4(D,spec),0.,1.);
    o.ambient=clamp(vec4(ambient*D+sky,luminanceShiftId),0.,1.);
    return o;
}
// Native depth PS327: alpha/spec atlas GREEN, not RED. Root may consume
// diffuseMap.a instead when using the corrected RGB+G merged texture.
// Native input is signed int4 BONEINDEX; sign-extend second packed byte.
float native_foliage_coverage(vec2 uv,vec3 W,vec3 camera,uint packedWind,
    vec4 veggieDissolveValues,sampler2D packedAlphaSpecMap,sampler2D noiseMap) {
    int randomByte=(int((packedWind>>8u)&255u)<<24)>>24;
    float d=length(W.xy-camera.xy)-float(randomByte)*veggieDissolveValues.z*(.5/255.);
    float keep=1.-clamp(veggieDissolveValues.x*d+veggieDissolveValues.y,0.,1.);
    float noiseG=texture(noiseMap,W.xy*.02).g;
    keep=keep*(1.-noiseG*keep)+keep*noiseG;
    return texture(packedAlphaSpecMap,uv).g*keep;
}
// Native kill condition coverage-AlphaCutoff<0; alpha equality survives.
