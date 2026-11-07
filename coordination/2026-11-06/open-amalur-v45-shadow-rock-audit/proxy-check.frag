#version 300 es
precision highp float;
// Native depth pixel contract. Identity UNORM BC1 view, raw GREEN, same UV0,
// linear min/mag/mip + REPEAT + anisotropy OFF. No vertex-alpha multiplication.
void oaShadowProxyAlpha(highp sampler2D alphaMap,highp vec2 sourceUV,
    highp float alphaCutoff) {
    if(texture(alphaMap,sourceUV).g-alphaCutoff<0.0)discard;
}
// Captured movementScale=10; alphaCutoff=100/255. No fog/normal/albedo/specular
// calculation or alpha blend. Native cullNONE, LEQUAL, depthWriteON, no bias.
// Current renderer converts native objectWVP depth via GLz=2*D3Dz-W once.

in vec2 uv;uniform highp sampler2D alphaMap;out vec4 color;void main(){
oaShadowProxyAlpha(alphaMap,uv,100./255.);color=vec4(0,0,0,1);
}
