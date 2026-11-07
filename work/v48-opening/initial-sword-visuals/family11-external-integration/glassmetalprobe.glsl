// GlassMetalProbe geometry contract, original DXBC6ac6c90a39ca9861.
// Texture source slots: D=0,mask=1,S=2,N=3,probe=21.
// Shader bindings differ: ambient=t0,D=t1,mask=t2,N=t3,S=t4,probe=t5.
struct OAGlassMetalProbe {
    vec3 normal;
    vec3 rawBase;
    float rawSpecular;
    float reflectionWeight;
    vec3 reflection; // belongs INSIDE G2 saturation/F16, before ambient AO
};
OAGlassMetalProbe oaGlassMetalProbe(
    vec4 diffuseSample,vec4 reflectionMask,vec4 specularSample,vec4 normalSample,
    vec4 vertexColor,vec3 rawN,vec3 rawT,vec3 rawB,vec3 unitToEye,
    float reflectionInfluence,float specularStrength,
    samplerCube probeSampler,vec3 tintRGB,vec3 environmentTintRGB)
{
    OAGlassMetalProbe r;
    vec2 xy=vec2(normalSample.a*normalSample.r,normalSample.g)*2.0-1.0;
    r.normal=normalize(rawT*xy.x+rawB*xy.y+
                        rawN*sqrt(clamp(1.0-dot(xy,xy),0.0,1.0)));
    r.reflectionWeight=reflectionMask.g*vertexColor.a*reflectionInfluence;
    r.rawBase=diffuseSample.rgb*vertexColor.rgb*(1.0-r.reflectionWeight);
    r.rawSpecular=specularSample.g*specularStrength; // no vertexColor.a factor
    vec3 probeRGB=texture(probeSampler,reflect(-unitToEye,r.normal).xzy).rgb;
    r.reflection=r.reflectionWeight*probeRGB*tintRGB*environmentTintRGB;
    return r;
}
// Probe sampling occurs after mapped-normal reconstruction, using the exact
// native xzy swizzle. Pass a unit vector from surface to eye.
//
// Native targets for the full normal-map geometry variant:
// G0 = vec4(r.normal*.5+.5, runtimeSpecularValues.y);
// G1 = clamp(vec4(r.rawBase,r.rawSpecular),0.,1.);
// G2 = clamp(vec4(texture(ambientCube,r.normal.xzy).rgb*r.rawBase +
//                  r.reflection, dynamicLuminanceShiftId),0.,1.);
// Each target is then independently stored in native F16 format.
// No Fresnel factor, opacity blend/discard, rawSpec*.9 ambient, or extra VCa
// attenuation is present in this geometry variant.
// Source/runtime gloss uniform upload must follow existing proven host policy.
