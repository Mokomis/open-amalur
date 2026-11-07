// Native VS292/PS293, middle caster draw72203; source MID1744210.
// Source-space phase, BEFORE any instance rotation/translation/scale.
int oaShadowProxyPhase(highp vec3 sourcePosition) {
    highp float total=dot(abs(sourcePosition),vec3(1.0));
    return int(uint(fract(total*0.10000000149011612)*10.0));
}
// Native vertex contract: position wind uses source SNORM normal, normalized
// in OBJECT space, then the entire displaced position passes through world.
highp vec3 oaShadowProxyWorld(highp vec3 sourcePosition,
    highp vec3 sourceSNORMNormal,highp mat4 world,
    highp float movementScale,highp float leafPalette[12]) {
    int phase=oaShadowProxyPhase(sourcePosition);
    highp vec3 p=sourcePosition+normalize(sourceSNORMNormal)
        *(movementScale*leafPalette[phase]);
    return (world*vec4(p,1.0)).xyz;
}
// Equivalent after source-only preprocessing. worldWindDirection is
// mat3(world)*normalize(sourceSNORMNormal), including forward instance SCALE;
// it is not an inverse-transpose normal and must NOT be normalized afterward.
highp vec3 oaShadowProxyWorldPrepared(highp vec3 baseWorld,
    highp vec3 worldWindDirection,int phase,highp float movementScale,
    highp float leafPalette[12]) {
    return baseWorld+worldWindDirection*(movementScale*leafPalette[phase]);
}
// Native depth pixel contract. Identity UNORM BC1 view, raw GREEN, same UV0,
// linear min/mag/mip + REPEAT + anisotropy OFF. No vertex-alpha multiplication.
void oaShadowProxyAlpha(highp sampler2D alphaMap,highp vec2 sourceUV,
    highp float alphaCutoff) {
    if(texture(alphaMap,sourceUV).g-alphaCutoff<0.0)discard;
}
// Captured movementScale=10; alphaCutoff=100/255. No fog/normal/albedo/specular
// calculation or alpha blend. Native cullNONE, LEQUAL, depthWriteON, no bias.
// Current renderer converts native objectWVP depth via GLz=2*D3Dz-W once.
