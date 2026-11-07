/* Source: native FUN_00c9dc90, called by FUN_00ceb3e0.
 * sx=(height(x-dx,y)-height(x+dx,y))/(2*dx), sy analogous.
 * Preserve sx separately: native retains it across normal normalization.
 * This GLSL expresses operations; source has float/double rounding boundaries.
 */
void oa_native_terrain_basis_slopes(float sx,float sy,out vec3 N,out vec3 T,out vec3 B){
 N=normalize(vec3(sx,sy,1.));
 vec3 seed=vec3(1.,0.,sx);
 T=normalize(seed-N*dot(seed,N));
 B=cross(N,T);
}
/* When only the source vertex normal survives export. Reconstruct BEFORE
 * raster interpolation. Validated94draws/44buffers/18700vertices: maximum
 * T/B component error6.56e-7 in float32. Retain authored T/B when available for exactness.
 * Native has no fallback branch for a degenerate seed; don't invent one here.
 */
void oa_native_terrain_basis_normal(vec3 N,out vec3 T,out vec3 B){
 vec3 seed=vec3(1.,0.,N.x/N.z);
 T=normalize(seed-N*dot(seed,N));
 B=cross(N,T);
}
/* d4,d5,d6 are native worldVector row vectors cb4[4..6] (HLSL row-major).
 * Caller can instead use an equivalent GLSL column-matrix multiplication.
 * Each vector independently normalized at vertex, then perspective-interpolated.
 */
vec3 oa_native_terrain_world_vector(vec3 v,vec3 d4,vec3 d5,vec3 d6){
 return normalize(v.x*d4+v.y*d5+v.z*d6);
}
/* Native q is camera-relative. cameraRelativeGLVP must therefore contain
 * projection and view rotation only. If your q is absolute world position,
 * use FULL current GLVP and pass q-eye separately to the fragment instead.
 */
void oa_native_terrain_vertex(vec3 p,vec3 terrainVertexOffset,float terrainScale,
 vec4 texcoordMad,vec4 blendTransform,mat4 cameraRelativeGLVP,
 out vec4 clipPosition,out vec3 cameraRelativePosition,out vec4 uvBlend){
 vec3 q=p*terrainScale+terrainVertexOffset;
 clipPosition=cameraRelativeGLVP*vec4(q,1.);
 cameraRelativePosition=q; /* Native q is camera-relative; see dynamic contract. */
 uvBlend.xy=q.xy*texcoordMad.xy+texcoordMad.zw;
 uvBlend.zw=uvBlend.xy*blendTransform.xy+blendTransform.zw;
}
