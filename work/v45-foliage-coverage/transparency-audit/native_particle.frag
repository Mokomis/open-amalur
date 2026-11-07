#version 300 es
precision highp float;
in highp vec2 UV;
in highp float nativeParticleClipZ;
in highp float fogTransmission; // perspective interpolation of VS min(exp(-(fogA*clipW+fogB)),1)
in highp vec4 VC; // native source RGBA8 UNORM, alpha multiplied by global cb1[7].x in VS
uniform sampler2D diffuseMap;
uniform sampler2D alphaMap;
uniform highp sampler2D sceneDepth;
uniform highp vec2 inverseDepth; // original cb2[7].xy, current-camera equivalent permitted
uniform highp vec2 inverseViewport;
uniform highp vec4 globalTint;
uniform highp vec4 luminanceFactors;
uniform highp vec3 luminanceTint;
uniform int softDepth;
out vec4 outColor;
void main(){
    vec4 c=vec4(texture(diffuseMap,UV).rgb,texture(alphaMap,UV).g)*VC;
    if(softDepth!=0){
        // GL bottom-left scene depth texture: gl_FragCoord.xy/currentExtent; NO Vulkan Y flip here.
        float d=texture(sceneDepth,gl_FragCoord.xy*inverseViewport).r;
        float sceneZ=1.0/(inverseDepth.x*d+inverseDepth.y);
        float x=(sceneZ-nativeParticleClipZ)*0.0199999996;
        float fade=min(x*x,1.0);
        if(fade<=0.0)fade=1.0; // exact active PS1042 unusual zero handling
        c.a*=fade;
    }
    c*=globalTint;
    float lum=dot(c.rgb,luminanceFactors.rgb);
    c.rgb+=luminanceFactors.w*(lum*luminanceTint-c.rgb);
    outColor=vec4(c.rgb,c.a*fogTransmission);
    // BOTH RGB and alpha blend: SRC_ALPHA,ONE, ADD; RGBA8 target, LEQUAL, no depth writes.
}
