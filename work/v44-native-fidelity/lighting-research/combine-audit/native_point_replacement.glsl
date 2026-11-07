/* Integration snippets for CURRENT oa_post.c (snapshotacf3b3db...)
 * No shared file edited. Native path bit128 only; legacy branch unchanged.
 * Active point1870/1871 -> additive RGBA16F -> combine1895.
 */

/* 1. Add beside N/illum/spec globals, BEFORE light(). */
#if SPEC
highp vec4 native_point_sum;
highp vec4 oaNativePointHalf4(highp vec4 x){
 return vec4(unpackHalf2x16(packHalf2x16(x.xy)),
             unpackHalf2x16(packHalf2x16(x.zw)));
}
#endif

/* 2. Replace light() with this function. N and spec_power must ALREADY be
 * decoded from half G0 and normalized/power*.25, as current native128 does.
 * V=normalize(eye-W), spec_gain=half(saturatedG1.a).
 */
void light(uint id){
 int i=int(id)*2;
 vec3 D=L[i].xyz-W;
 float d2=dot(D,D),e=L[i+1].w;
 if(d2>=e*e)return;
#if SPEC
 if((features&128)!=0){
  /* Native lightPosition.w=-1/(outer-inner), lightColor.w=outer/(outer-inner).
   * Equivalent linear sphere attenuation, no squared/Gaussian law. Native
   * has no special zero-distance/zero-width authoring fallback. */
  float dist=sqrt(d2);
  vec3 Ld=D*inversesqrt(d2);
  float width=e-L[i].w;
  float at=clamp(dist*(-1./width)+e/width,0.,1.);
  vec3 lightColor=L[i+1].rgb;
  float nl=clamp(dot(N,Ld),0.,1.);
  float reflected=clamp(dot(Ld,reflect(-V,N)),0.,1.);
  float lobe=exp2(log2(max(reflected,.00001))*spec_power);
  vec3 rgb=(nl*lightColor)*at;
  vec3 specRGB=((nl*lobe)*lightColor)*at;
  float a=dot(specRGB,vec3(.2126,.7152,.0722));
  /* F16 RMW happens AFTER adding this unquantized shader contribution.
   * Do NOT half-round each contribution before addition or only the final
   * total. Original target rounds after each accepted additive light draw. */
  native_point_sum=oaNativePointHalf4(native_point_sum+vec4(rgb,a));
  return;
 }
#endif
 /* Exact current legacy branch retained when native bit128 is off. */
 float inv=inversesqrt(max(d2,1e-6));
 highp float at=clamp((e-d2*inv)/max(e-L[i].w,1e-6),0.,1.);
 highp vec3 Ld=D*inv,c=L[i+1].rgb*at;
 illum+=c*max(dot(N,Ld),0.);
#if SPEC
 if(material_family>0&&(features&16)!=0)
  spec_sum+=c*(pow(max(clamp(dot(Ld,reflect(-V,N)),0.,1.),.00001),spec_power)*spec_gain);
 else if(spec>.02)
  spec_sum+=c*(pow(max(dot(N,normalize(V+Ld)),0.),32.)*spec);
#endif
}

/* 3. In native128 block, just BEFORE point_lights(), replace/reset: */
/*
 illum=vec3(0.);
#if SPEC
 spec_sum=vec3(0.);
 native_point_sum=vec4(0.);
#endif
 if((features&8)!=0)point_lights();
#if SPEC
 vec3 direct=native_point_sum.rgb;
 vec3 native_local_spec=native_point_sum.rgb*native_point_sum.a/
   (dot(native_point_sum.rgb,vec3(.2126,.7152,.0722))+1.0000000116860974e-7);
#else
 vec3 direct=illum;
#endif
*/

/* 4. Native final spec consumption:
 * Replace source-known-family current expression
 *   native_spec=sun_color*nlobes*spec_gain+spec_sum;
 * with
 *   native_spec=(sun_color*nlobes+native_local_spec)*spec_gain;
 * This applies material G1spec ONCE, after reconstruction. Point summation
 * itself does not contain material gain. AO/backlight do not attenuate local
 * diffuse/spec in native combine. Current family0 is an unaudited fallback;
 * its legacy spec_sum*.9 is not a native material contract. If retaining that
 * fallback, select legacy light() for family0 explicitly; don't label it exact.
 */
