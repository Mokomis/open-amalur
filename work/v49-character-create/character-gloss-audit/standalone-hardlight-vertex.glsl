// Active standalone VS351, CB68 rows. Source P/UV/N/T/B/VC layout is pipeline13252.
// Position rows0..3; normal rows4..6; already-composed clip rows8..11.
// Return independent per-vertex-normalized vectors; preserve raw interpolation in PS.
vec3 oa_native_character_basis_vertex(vec3 v,vec4 r4,vec4 r5,vec4 r6) {
    return normalize(v.x*r4.xyz+v.y*r5.xyz+v.z*r6.xyz);
}
vec3 oa_native_character_world_position(vec3 p,vec4 r0,vec4 r1,vec4 r2,vec4 r3) {
    return p.x*r0.xyz+p.y*r1.xyz+p.z*r2.xyz+r3.xyz;
}
vec4 oa_native_character_clip_position(vec3 p,vec4 r8,vec4 r9,vec4 r10,vec4 r11) {
    return p.x*r8+p.y*r9+p.z*r10+r11;
}
// Runtime source SpecularValues.y=20 => G0.a=20 => shared specular exponent=5.
// Do not apply /255, clamp-to-one or pre-Gbuffer exponent conversion.
