/* Native bit128 only. Existing vertex fog remains for legacy paths.
 * Add `uniform vec2 fog;` to FRAGMENT declarations (same linked uniform name
 * and currentworld_draw upload as vertex). Native normalized camera GLVP has
 * clipW=physical forwardZ. Radial length(W-eye) is not the fog depth.
 */
/* At final output, source-known opaque/cutout/grass/terrain native branch:
if((features&128)!=0){
 // Mandatory native RGBA8 lighting-store saturation BEFORE screen fog.
 lit=clamp(lit,0.,1.);
 // Nominal8bit conversion if collapsing the two original render stages.
 // Rounding ties are driver dependent; a real RGBA8 intermediate is exact.
 lit=roundEven(lit*255.)/255.;
 float z=1./gl_FragCoord.w;
 float transmittance=min(exp(-(fog.x*z+fog.y)),1.);
 vec3 I=normalize(W-eye);
 float tint=.5*pow(max(dot(I,sun_dir),0.),10.);
 vec3 nativeFog=mix(fog_color,sun_color,tint);
 o=vec4(mix(nativeFog,lit,transmittance),1.);
}else{
 o=vec4(mix(lit,fog_color,F),1.);
}
*/
/* Actual captured globals: fogRGB(.4196078777,.3607843220,.2235294282),
 * density4.731020089820959e-5, start-.1552170217037201;
 * sunRGB(.7858883142), direction(0,.3654382229,.9308354855);
 * sunlightFogTintAmount=.5, sunlightFogTintPower=10.
 * Source1898 uses exp2(-1.44269502*(density*Z+start)), the same exp law.
 * Do not move sky or independently blended native water into this opaque
 * quantization/fog branch; those have separate native producers/order.
 */
