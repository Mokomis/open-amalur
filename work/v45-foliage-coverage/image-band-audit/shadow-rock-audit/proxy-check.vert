#version 300 es
precision highp float;
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

layout(location=0)in vec3 p;layout(location=1)in vec3 n;
uniform mat4 world,lightVP;uniform float leafPalette[12];void main(){
gl_Position=lightVP*vec4(oaShadowProxyWorld(p,n,world,10.,leafPalette),1.);
}
