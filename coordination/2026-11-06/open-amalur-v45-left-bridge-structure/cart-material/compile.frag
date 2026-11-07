#version 300 es
precision highp float;precision highp int;
// Active native VS650/PS651, shipped DXBC 8af7b90f9cc700d2.
// Source material426015 for_cart, shader358221 fresnelglassmetalprobe.
// All texture/color arithmetic is UNORM, not sRGB sampling.

// Run per vertex: native VS normalizes each transformed source basis vector.
// Interpolate these independently; do NOT normalize them again before mixing
// the normal-map components in the fragment stage. No derivative basis exists.
void oaCartVertexFrame(mat3 worldVector,vec3 sourceN,vec3 sourceT,vec3 sourceB,
                       out vec3 N,out vec3 T,out vec3 B){
    N=normalize(worldVector*sourceN);
    T=normalize(worldVector*sourceT);
    B=normalize(worldVector*sourceB);
}

struct OACartSample{
    vec3 normal;
    vec3 rawBase;       // preserve until ambient calculation; G1 clamps later
    float rawSpecular;
    float reflectionRatio;
    float gloss;
};

// profileColor = source TintColor (RGB tint affects reflection only).
// profileSpec = (SpecularValues.x,SpecularValues.y,FresnelPower,FresnelScale).
// profileUV = (1,1,ReflectionInfluence,Opacity); Opacity is unused by this PS.
// t0=D697, t1=N698, t2=S699, t3=Alpha700. All use the SAME unmodified UV.
OACartSample oaCartMaterial(vec2 uv,vec4 vertexColor,vec3 W,vec3 eye,
    vec3 interpolatedN,vec3 interpolatedT,vec3 interpolatedB,
    vec4 profileSpec,vec4 profileUV,highp sampler2D diffuseMap,
    highp sampler2D normalMap,highp sampler2D specularMap,
    highp sampler2D alphaMap){
    vec4 texN=texture(normalMap,uv);
    vec2 xy=vec2(texN.r*texN.a,texN.g)*2.0-1.0;
    float nz=sqrt(clamp(1.0-dot(xy,xy),0.0,1.0));
    vec3 N=normalize(xy.x*interpolatedT+xy.y*interpolatedB+nz*interpolatedN);
    vec3 V=normalize(eye-W);
    float facing=max(abs(dot(N,V)),0.00001);
    float fresnel=1.0-clamp(exp2(log2(facing)*profileSpec.z)*profileSpec.w,0.0,1.0);
    vec4 diffuse=texture(diffuseMap,uv);
    float alphaMask=texture(alphaMap,uv).g*vertexColor.a;
    float rho=fresnel*alphaMask*profileUV.z;
    OACartSample s;
    s.normal=N;
    s.rawBase=diffuse.rgb*vertexColor.rgb*(1.0-rho);
    s.rawSpecular=texture(specularMap,uv).g*profileSpec.x;
    s.reflectionRatio=rho;
    s.gloss=profileSpec.y;
    return s;
}

// Use in place of generic material ambient/sky-specular attenuation for family9.
// Native CB1.environmentTint.rgb@96 = (1,1,1) in this capture; profile OARE001.
// Reflection is native dynamic probe image3594; ambient is existing cube7496.
vec3 oaCartAmbient(OACartSample s,vec3 W,vec3 eye,vec3 tintColor,
    vec3 environmentTint,highp samplerCube ambientCube,
    highp samplerCube reflectionCube){
    vec3 V=normalize(eye-W);
    vec3 R=reflect(-V,s.normal);
    vec3 a=texture(ambientCube,s.normal.xzy).rgb*s.rawBase;
    vec3 reflected=texture(reflectionCube,R.xzy).rgb*tintColor*environmentTint;
    return clamp(a+s.reflectionRatio*reflected,0.0,1.0);
}

// Exact G-buffer contract (round the three targets to RGBA16F on storage):
// G0 = vec4(sample.normal*.5+.5, sample.gloss).
// G1 = clamp(vec4(sample.rawBase,sample.rawSpecular),0,1).
// G2 = vec4(oaCartAmbient(...),clamp(dynamicLuminanceShiftId,0,1)).
// Captured dynamicLuminanceShiftId=0.4375 (CB4@252), per draw, not a material key.
// Shared deferred exponent = G0.a*.25. Shared direct/specular lighting unchanged.
// No alpha discard, alpha blend, distance fog or generic q/sky term in this PS.

uniform highp sampler2D d,n,sp,al;uniform highp samplerCube a,r;layout(location=0)out vec4 g0;layout(location=1)out vec4 g1;layout(location=2)out vec4 g2;void main(){OACartSample v=oaCartMaterial(vec2(.2),vec4(1),vec3(0),vec3(0,0,2),vec3(0,0,1),vec3(1,0,0),vec3(0,1,0),vec4(1.7697,100,1.584,1.3),vec4(1),d,n,sp,al);g0=vec4(v.normal*.5+.5,v.gloss);g1=clamp(vec4(v.rawBase,v.rawSpecular),0.,1.);g2=vec4(oaCartAmbient(v,vec3(0),vec3(0,0,2),vec3(.9,.7,.52),vec3(1),a,r),.4375);}
