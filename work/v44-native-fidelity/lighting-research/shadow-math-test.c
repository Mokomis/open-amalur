#include "oa_native_shadow_math.h"
int parameters(oa_native_shadow_cascade *o,float *ab,const float *v,const float *eye,const float *sun){oa_native_shadow_config c;oa_native_shadow_defaults(&c);c.projection_scale[0]=1.f/.7627148628234863f;c.projection_scale[1]=1.f/.42902708053588867f;return oa_native_shadow_parameters(o,ab,v,eye,sun,&c);}
