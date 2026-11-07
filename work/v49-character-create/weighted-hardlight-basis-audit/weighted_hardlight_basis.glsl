// Captured VS375 only: NOT a universal weighted-character convention.
// Native palettes: binding69 has234 vec4 rows =>78 three-row affine entries.
// Native entity block68: world rows0..3, direction rows4..6, composed clip rows8..11.
vec4 oa375Weights(vec4 decodedSNORMWeights) {
    return vec4(decodedSNORMWeights.xyz,
        dot(vec4(-1.,-1.,-1.,1.),vec4(decodedSNORMWeights.xyz,1.)));
}
vec3 oa375BonePoint(vec3 p,int joint,vec4 b[234]) {
    int i=joint*3;vec4 q=vec4(p,1.);
    return vec3(dot(b[i],q),dot(b[i+1],q),dot(b[i+2],q));
}
vec3 oa375BoneDirection(vec3 v,int joint,vec4 b[234]) {
    int i=joint*3;
    return vec3(dot(b[i].xyz,v),dot(b[i+1].xyz,v),dot(b[i+2].xyz,v));
}
vec3 oa375SkinPoint(vec3 p,ivec4 j,vec4 w,vec4 b[234]) {
    vec3 r=oa375BonePoint(p,j.y,b)*w.y;
    r=oa375BonePoint(p,j.x,b)*w.x+r;
    r=oa375BonePoint(p,j.z,b)*w.z+r;
    return oa375BonePoint(p,j.w,b)*w.w+r;
}
vec3 oa375SkinDirection(vec3 v,ivec4 j,vec4 w,vec4 b[234]) {
    vec3 r=oa375BoneDirection(v,j.y,b)*w.y;
    r=oa375BoneDirection(v,j.x,b)*w.x+r;
    r=oa375BoneDirection(v,j.z,b)*w.z+r;
    return oa375BoneDirection(v,j.w,b)*w.w+r;
}
vec3 oa375EntityDirection(vec3 v,vec4 c[12]) {
    vec3 r=v.y*c[5].xyz;r=v.x*c[4].xyz+r;
    return v.z*c[6].xyz+r;
}
void oa375NativeBasis(vec3 sourceN,vec3 sourceT,vec3 sourceB,
                     ivec4 joints,vec4 decodedSNORMWeights,
                     vec4 c68[12],vec4 b69[234],
                     out vec3 worldN,out vec3 worldT,out vec3 worldB) {
    vec4 w=oa375Weights(decodedSNORMWeights);
    worldN=normalize(oa375EntityDirection(oa375SkinDirection(sourceN,joints,w,b69),c68));
    worldT=normalize(oa375EntityDirection(oa375SkinDirection(sourceT,joints,w,b69),c68));
    // Deliberate captured asymmetry: do not skin B, cross(N,T), or orthogonalize.
    worldB=normalize(oa375EntityDirection(sourceB,c68));
}
// If caller uses EXISTING oa_character_bones WORLD rows, entity facing is already
// in those rows: N/T=normalize(skinDirection_world(sourceN/T)), and P=skinPoint_world.
// B still needs ENTITY-ONLY direction transform (current producer: facing rotation).
// Do not apply the entity transform to world-skinned N/T a second time.
// After interpolation PS376 uses normalize(T*map.x+B*map.y+N*map.z).
