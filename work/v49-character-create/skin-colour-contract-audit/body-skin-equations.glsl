// Source-body color equation: retained skin DXBC + active masked PS462.
// Assumes caller-proven native skinColor RGBA; do not choose/init alpha here.
vec3 oa_native_skin_base(vec3 diffuse,vec4 skinColor,vec3 N,vec3 unitView,
                        vec4 extraTerms,vec4 fresnelValues,vec4 vertexColor){
    float rim=clamp(fresnelValues.x*pow(1.-clamp(dot(N,unitView),0.,1.),fresnelValues.y),0.,1.);
    vec3 delta=skinColor.rgb*diffuse-diffuse;
    vec3 cosmetic=skinColor.a*delta+diffuse+vec3(extraTerms.x*rim);
    return cosmetic*vertexColor.rgb*vertexColor.a;
}
// Active masked body variant BEFORE this color/normal core:
// if(texture(nativeBodyMask,UV0).g-nativeAlphaCutoff < 0.) discard;
// Captured matched-profile cutoff = 0.9098039269447327 (source byte232/255).
// N=normalize(rawT*mapX+rawB*mapY+rawN*mapZ), mapX=map.R*map.A*2-1,
// mapY=map.G*2-1, mapZ=sqrt(saturate(1-mapX²-mapY²)).
// G1=half(saturate(vec4(rawBase,specMap.G*sourceStrength*vertexAlpha))).
// G0normal/gloss and G2ambient are separate stores:
// G0.a=sourceGloss (20 for MID513702, no/255/pre*.25).
// G2.rgb=half(saturate(CharacterAmbientMap(N.xzy)*vertexAlpha*rawBase)).
// No generic-world ambient q/sky-specular term and no ConstantColor multiplier.
// Original head has additional overlay/UV requirements; do not use this alone
// to label a head/hair/whole-character creator complete.
