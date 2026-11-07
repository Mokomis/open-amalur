// Original opaque character geometry DXBC78f3c69a187f2822.
// Newly recovered from a nonzero aPLib prefix missed by the old cache scanner.
// Source-compatible with CharacterHardLight545212's layout/resources.
// Exact named-platform-ID -> embedded-bytecode registration table is not joined.
struct OACharacterHardLight {
 vec3 normal;
 vec3 rawBase;
 float rawSpecular;
 vec3 ambient;
};
OACharacterHardLight oaCharacterHardLight(
 vec4 diffuseSample,vec4 normalSample,vec4 specularSample,vec4 vertexColor,
 vec3 rawN,vec3 rawT,vec3 rawB,vec3 unitToEye,
 vec4 specularValues,vec4 characterExtraTerms2,vec4 fresnelValues2,
 samplerCube characterAmbientCube)
{
 OACharacterHardLight o;
 vec2 xy=vec2(normalSample.a*normalSample.r,normalSample.g)*2.0-1.0;
 o.normal=normalize(rawT*xy.x+rawB*xy.y+
                    rawN*sqrt(clamp(1.0-dot(xy,xy),0.0,1.0)));
 float f=clamp(fresnelValues2.x*
               pow(1.0-clamp(dot(o.normal,unitToEye),0.0,1.0),
                   fresnelValues2.y),0.0,1.0);
 o.rawBase=(diffuseSample.rgb+vec3(characterExtraTerms2.x*f))
            *vertexColor.rgb*vertexColor.a;
 o.rawSpecular=specularSample.g*specularValues.x*vertexColor.a;
 // Independent G2 calculation uses rawBase, before G1 saturation/F16.
 o.ambient=clamp(texture(characterAmbientCube,o.normal.xzy).rgb*
                 vertexColor.a*o.rawBase,0.0,1.0);
 return o;
}
// Native full geometry outputs:
// G0=vec4(o.normal*.5+.5,SpecularValues.y);
// G1=clamp(vec4(o.rawBase,o.rawSpecular),0.,1.);
// G2=vec4(o.ambient,clamp(dynamicLuminanceShiftId,0.,1.));
// Each is stored independently to native F16 targets.
// Folded shared combine: use half(clamp(G1)) base/spec, half(G2) ambient;
// spec exponent is source SpecularValues.y*.25 (also explicit in forward peer).
// No source slot1/alpha discard, ConstantColor use, instance skin tint,
// probe/environment reflection, or rawSpec*.9 ambient in this geometry program.
