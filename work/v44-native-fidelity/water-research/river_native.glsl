// Reviewed translation of shipped 3316e4b0586bb12a pixel family.
// Active capture PS946 (no local point lights) and PS956 (four local lights).
// Requires native vertex UV, tangent frame, vertex red, and ORIGINAL D3D clip.
// Scene textures must be a stable PRE-WATER copy; never sample active framebuffer.
// m[6] is native96 from decoded-materials.json; m[2].w is ignored padding.
// Coordinate convention: world z up; native reflection probe is sampled in xzy.
vec2 oaSceneUV(vec2 uv,bool lowerLeft){return lowerLeft?vec2(uv.x,1.0-uv.y):uv;}
vec3 oaDecodeRiverNormal(vec4 s) {
    vec2 xz=vec2(s.r*s.a,s.g)*2.0-1.0;
    return vec3(xz.x,sqrt(clamp(1.0-dot(xz,xz),0.0,1.0)),xz.y);
}
vec3 oaDecodeRefraction(vec4 s) {
    return vec3(vec2(s.r*s.a,s.g)*2.0-1.0,0.0);
}
// Execute in VERTEX stage, then interpolate these UVs (all affine per vertex).
void oaRiverUV(vec2 uv,float time,vec4 m[6],out vec2 baseUV,out vec2 foamUV,out vec2 detailUV,out vec2 refractionUV) {
    baseUV=uv+time*vec2(m[0].w,m[1].x)*m[0].x;
    vec2 scrollingFoamUV=uv+vec2(time*m[1].y,0.0);
    foamUV=scrollingFoamUV*m[0].z;
    detailUV=scrollingFoamUV*m[0].y;
    refractionUV=uv+time*m[1].zw;
}
vec4 oaNativeRiver(
    sampler2D baseMap,sampler2D normalMap,sampler2D foamMap,
    sampler2D detailNormalMap,sampler2D refractionMap,
    sampler2D sceneColor,sampler2D sceneDepth,
    samplerCube environmentProbe,samplerCube ambientCube,
    vec4 m[6],vec2 uvBase,vec2 uvFoam,vec2 uvDetail,vec2 uvRefraction,
    vec3 worldPosition,vec3 eye,vec3 normal,vec3 tangent,vec3 binormal,
    float vertexRed,vec4 nativeClip,vec2 invDepthTransform,
    vec3 sunDirection,vec3 sunColor,vec3 shadowColor,
    vec3 waterFogGlobals,vec4 lightData[8],bool pointLights,bool sceneTextureLowerLeft,
    vec4 globalTint,vec4 luminanceFactors,vec3 luminanceTint) {
    vec3 V=normalize(eye-worldPosition);
    vec3 n1=oaDecodeRiverNormal(texture(normalMap,uvBase));
    vec3 n2=oaDecodeRiverNormal(texture(detailNormalMap,uvDetail));
    vec3 nr=normalize((n1+n2)*vec3(.5,2.0,.5));
    vec3 N=normalize(nr.y*normal+nr.x*tangent+nr.z*binormal);
    vec3 env=texture(environmentProbe,reflect(-V.xzy,nr)).rgb;
    vec3 base=mix(texture(baseMap,uvBase).rgb,env,m[2].x);
    vec2 screenUV=clamp(nativeClip.xy/nativeClip.w*vec2(.5,-.5)+.5,0.0,1.0);
    // Flip each final native-coordinate sample only; this also flips refraction Y correctly.
    float originalDepth=1.0/(invDepthTransform.x*texture(sceneDepth,oaSceneUV(screenUV,sceneTextureLowerLeft)).r+invDepthTransform.y);
    float originalDifference=originalDepth-nativeClip.z;
    vec3 originalColor=texture(sceneColor,oaSceneUV(screenUV,sceneTextureLowerLeft)).rgb;
    vec2 refractedUV=screenUV+oaDecodeRefraction(texture(refractionMap,uvRefraction)).xy*m[2].y;
    float refractedDepth=1.0/(invDepthTransform.x*texture(sceneDepth,oaSceneUV(refractedUV,sceneTextureLowerLeft)).r+invDepthTransform.y);
    bool valid=nativeClip.z<refractedDepth;
    float difference=(valid?refractedDepth:originalDepth)-nativeClip.z;
    vec3 color=valid?texture(sceneColor,oaSceneUV(refractedUV,sceneTextureLowerLeft)).rgb:originalColor;
    // Native pow receives difference; valid draw/visible-depth path is positive.
    float tintAmount=clamp(pow(difference,1.5)*m[2].z,0.0,1.0);
    color=mix(color,m[3].rgb,tintAmount);
    float depthFog=1.0-exp(-difference*m[2].z*waterFogGlobals.x);
    color+=waterFogGlobals.z*depthFog*(m[3].rgb*.4-color);
    float fresnel=clamp(clamp(dot(N,V)+m[5].z,0.0,1.0),.3,.8);
    vec3 combined=mix(base,color,fresnel);
    combined+=waterFogGlobals.z*((base*(1.0-fresnel)+color)-combined);
    float opacityScale=.01+waterFogGlobals.z*(waterFogGlobals.y-.01);
    float a=originalDifference*opacityScale;
    float alpha=clamp(a*a*a,0.0,1.0);
    combined=mix(texture(foamMap,uvFoam).rgb,combined,vertexRed);
    vec3 R=reflect(-V,N);
    vec3 diffuseLights=vec3(0.0),specularLights=vec3(0.0);
    float exponent=m[5].y*.25;
    if(pointLights)for(int i=0;i<4;i++){
        vec3 delta=lightData[i*2].xyz-worldPosition;float dist=length(delta);vec3 L=delta/dist;
        float atten=clamp(dist*lightData[i*2].w+lightData[i*2+1].w,0.0,1.0)*clamp(dot(N,L),0.0,1.0);
        diffuseLights+=lightData[i*2+1].rgb*atten;
        specularLights+=lightData[i*2+1].rgb*(atten*pow(max(clamp(dot(L,R),0.0,1.0),.00001),exponent));
    }
    float nl=clamp(dot(N,sunDirection),0.0,1.0);
    vec3 diffuse=sunColor*nl+diffuseLights+texture(ambientCube,N.xzy).rgb+(1.0-nl)*shadowColor;
    vec3 spec=sunColor*(nl*pow(max(clamp(dot(sunDirection,R),0.0,1.0),.00001),exponent))+specularLights;
    vec4 result=vec4(combined*diffuse+spec*m[5].x,alpha)*globalTint;
    float lum=dot(result.rgb,luminanceFactors.rgb);
    result.rgb+=luminanceFactors.w*(lum*luminanceTint-result.rgb);
    return result;
}
