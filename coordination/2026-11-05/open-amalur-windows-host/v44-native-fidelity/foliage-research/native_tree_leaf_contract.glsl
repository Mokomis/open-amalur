// Exact captured tree-leaf family: native343437 diffuse image13901 hash match;
// pipeline8194 VS877 PS878, 71 live draws. Cull NONE; color depth EQUAL.
// cb0 captured rows: (0,0,1,1), (1,0,0,0).
// Vertex native layout: position@0, UV@12, SNORM16x4 N@20,
// SNORM16x4 tangent1@28,tangent2@36, UNORM8x4 vertexColor@44.
// Source (8859) leaf material differs materially from grass8861.
// Joined OAWT76 family6 extension (no UV1 in original48-byte source):
// UV1@56 = float-bitcast of four half values [worldWindDirection.xyz,index].
// flags@72 = float radialLength; expose as float attribute loc8.
// worldWindDirection includes authored instance scale and rotation.
void native_leaf_joined_deform(inout vec3 W,inout vec3 radialN,vec2 packedUV1,
                               float radialLength,float movementScale,
                               float useSphericalNormals,float palette[12]) {
    vec2 xy=unpackHalf2x16(floatBitsToUint(packedUV1.x));
    vec2 zi=unpackHalf2x16(floatBitsToUint(packedUV1.y));
    vec3 delta=vec3(xy,zi.x)*(movementScale*palette[int(zi.y)]);
    W+=delta;
    if(useSphericalNormals<0.5) delta.z=0.0;
    radialN=normalize(radialN*radialLength+delta);
}
vec3 native_leaf_deform(vec3 localPosition,vec3 sourceNormal,vec4 randomRows[3],
                        float windAmplitude) {
    uint i=uint(fract(dot(abs(localPosition),vec3(1.0))*0.1)*10.0);
    float randomValue=randomRows[i>>2u][i&3u]; // globals[75..77]
    return localPosition+normalize(sourceNormal)*(randomValue*windAmplitude);
}
vec3 native_leaf_normal(vec3 W,vec3 instancePivot,vec2 normalMode) {
    // normalMode = material cb0[0].xy; captured=(0,0).
    vec3 radial=W-instancePivot-vec3(0.0,0.0,normalMode.y);
    if(normalMode.x<0.5) radial=vec3(W.xy-instancePivot.xy,0.0);
    return normalize(radial);
}
void native_leaf_gbuffer(vec2 uv,vec3 W,vec3 radialN,vec3 rawT1,vec3 rawT2,
                         vec3 vertexRGB,sampler2D diffuseMap,sampler2D normalMap,
                         samplerCube ambientCube,vec3 cameraPosition,
                         vec4 mat0,vec4 mat1,vec4 global79,vec4 global80,
                         vec4 skyLightColor,float luminanceShiftId,
                         out vec4 G0,out vec4 G1,out vec4 G2) {
    vec4 nt=texture(normalMap,uv);
    vec2 xy=vec2(nt.r*nt.a,nt.g)*2.0-1.0;
    vec3 mappedN=normalize(rawT1*xy.x+rawT2*xy.y+
                          radialN*sqrt(clamp(1.0-dot(xy,xy),0.0,1.0)));
    // Native does NOT normalize the result of this material-controlled blend.
    vec3 N=mappedN+(radialN-mappedN)*mat0.z;
    vec3 D=texture(diffuseMap,uv).rgb*vertexRGB;
    float spec=(1.0-mat1.x)*global79.y;
    G0=vec4(N*0.5+0.5,global79.z);
    G1=clamp(vec4(D,spec),0.0,1.0);
    float k=spec*global80.x;
    vec3 V=normalize(cameraPosition-W);
    vec3 R=V-2.0*dot(V,N)*N;
    vec3 sky=pow(clamp(-R.z,0.0,1.0),skyLightColor.a*global79.w)*skyLightColor.rgb*k;
    vec3 cube=texture(ambientCube,N.xzy).rgb*(1.0-clamp(k,0.0,1.0));
    G2=vec4(clamp(cube*D+sky,0.0,1.0),clamp(luminanceShiftId,0.0,1.0));
}
// Captured mat1.y=0 => no leaf vertex displacement in these draws.
// Captured mat0.z=1 => N=radialN exactly; spec=0.
// Color PS has no alpha sample/discard because coverage is established by
// the earlier depth pass. Tree alpha asset343436 is correctly GREEN already.
bool native_leaf_depth_keep(vec2 uv,float alphaCutoff,float instanceDissolve,
                            sampler2D alphaMap,sampler2D noiseMap) {
    return texture(noiseMap,uv).b<=instanceDissolve &&
           texture(alphaMap,uv).g>=alphaCutoff;
}
