#version 300 es
precision highp float;
/* Concise algebraic translation of ACTIVE captured PS792, matching shipped
 * 1bc6cb4d0dcff9cf. Native F16 render targets still saturate G1 and G2 explicitly.
 * texDiffuse/Normal are four sampled RGBA values in material order. diffuse.a
 * is height-blend input; normal.a is specular strength. paint.a is the sampled terrain-blend alpha.
 */
vec4 oa_native_terrain_weights(vec4 paint,vec4 diffuseAlpha,float heightBlend){
 float remaining=1.-paint.r;
 float second=paint.g*remaining;
 float third=paint.b*(1.-paint.g*remaining)*remaining;
 vec4 w=vec4(paint.r,second,third,1.-clamp(paint.r+second+third,0.,1.));
 vec4 h=w*diffuseAlpha;
 float top=max(max(h.x,h.y),max(h.z,h.w));
 return max(h-vec4(top-heightBlend),vec4(0.));
}
void oa_native_terrain_material(vec4 w,vec4 d0,vec4 d1,vec4 d2,vec4 d3,
 vec4 n0,vec4 n1,vec4 n2,vec4 n3,vec4 levels,vec4 powers,
 float paintAlpha,vec3 interpN,vec3 interpT,vec3 interpB,
 out vec3 N,out vec3 paintedAlbedo,out float rawSpec,out float storedSpec,
 out float storedGloss){
 float invSum=1./(((w.x+w.y)+w.z)+w.w);
 vec4 n=((n0*w.x+n1*w.y)+n2*w.z)+n3*w.w;
 n*=invSum;
 vec3 nt=n.rgb*2.-1.;
 N=normalize(nt.x*interpT+nt.y*interpB+nt.z*interpN);
 vec3 albedo=((d0.rgb*w.x+d1.rgb*w.y)+d2.rgb*w.z)+d3.rgb*w.w;
 paintedAlbedo=(albedo*invSum)*paintAlpha;
 rawSpec=(dot(levels,w)*invSum)*n.a;
 storedSpec=clamp(rawSpec*paintAlpha,0.,1.);
 storedGloss=dot(powers,w)*invSum;
}
/* Pass camera-to-fragment I=normalize(cameraRelativePosition), NOT E=-I.
 * Native cube samples N.xzy (worldZ-up cube ordering), not N.xyz.
 * Native reflection factor is saturate(reflect(I,N).z), exponent
 * skyLight.a*ambientDiffuseScale, captured5. AO is applied later in combine.
 * Do not clamp Q until computing cube attenuation. Sky branch uses raw Q.
 */
vec3 oa_native_terrain_ambient(vec3 N,vec3 I,vec3 paintedAlbedo,float rawSpec,
 samplerCube ambientCube,vec4 skyLight,float ambientDiffuseScale,
 float ambientSpecularScale){
 float Q=rawSpec*ambientSpecularScale;
 float r=clamp(reflect(I,N).z,0.,1.);
 float sky=exp2(log2(r)*(skyLight.a*ambientDiffuseScale));
 vec3 spec=(sky*skyLight.rgb)*Q;
 vec3 cube=texture(ambientCube,N.xzy).rgb*(1.-clamp(Q,0.,1.));
 return clamp(cube*paintedAlbedo+spec,0.,1.);
}
/* G0=vec4(N*.5+.5,storedGloss);
 * G1=vec4(clamp(paintedAlbedo,0,1),storedSpec);
 * G2=vec4(ambient,clamp(dynamicLuminanceShiftId,0,1)).
 * Direct sunlight's power is storedGloss*.25 in the deferred combine.
 * Material ambient uses paintedAlbedo before G1 clamping/quantization.
 */

out vec4 o;void main(){o=vec4(0.);}
