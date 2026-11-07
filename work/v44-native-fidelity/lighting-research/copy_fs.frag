#version 300 es
precision highp float;in vec2 uv;uniform sampler2D s;out vec4 o;void main(){o=vec4(texture(s,uv).rgb,0.);}