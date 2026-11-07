#include "oa_material_probes.h"
#include "oa_cart_probe.h"
#include <android/asset_manager.h>
#include <android/log.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
typedef struct probe_row{uint32_t material,asset;GLuint texture;int attempted;}probe_row;
struct oa_material_probes{AAssetManager *assets;unsigned count;probe_row rows[64];};
oa_material_probes *oa_material_probes_open(AAssetManager *assets,unsigned material_count){
 AAsset *a=AAssetManager_open(assets,"world/material-probe-map.bin",AASSET_MODE_BUFFER);const unsigned char *b;off64_t n;uint32_t count;unsigned i,j;oa_material_probes *p=NULL;
 if(!a)return NULL;n=AAsset_getLength64(a);b=(const unsigned char*)AAsset_getBuffer(a);
 if(!b||n<12||memcmp(b,"OAPM001",8))goto done;memcpy(&count,b+8,4);
 if(count>64||n!=12+(off64_t)count*8)goto done;
 p=(oa_material_probes*)calloc(1,sizeof(*p));if(!p)goto done;p->assets=assets;p->count=count;
 for(i=0;i<count;i++){probe_row *r=p->rows+i;memcpy(&r->material,b+12+i*8,4);memcpy(&r->asset,b+16+i*8,4);
  if(r->material>=material_count||!r->asset)goto invalid;
  for(j=0;j<i;j++)if(p->rows[j].material==r->material)goto invalid;
 }
 goto done;
 invalid:free(p);p=NULL;
 done:AAsset_close(a);return p;
}
GLuint oa_material_probes_get(oa_material_probes *p,unsigned material){
 unsigned i,j;if(!p)return 0;
 for(i=0;i<p->count;i++)if(p->rows[i].material==material){probe_row *r=p->rows+i;
  if(!r->attempted){for(j=0;j<p->count;j++)if(j!=i&&p->rows[j].asset==r->asset&&p->rows[j].attempted){r->attempted=1;return r->texture=p->rows[j].texture;}
   r->attempted=1;r->texture=oa_cart_probe_open(p->assets,"world/material-probes.bin",r->asset);
   __android_log_print(r->texture?ANDROID_LOG_INFO:ANDROID_LOG_ERROR,"OpemAmalurScene","MATERIAL_PROBE material=%u source_image=%u gpu_texture=%u inherited=0",material,r->asset,r->texture);
  }return r->texture;
 }return 0;
}
void oa_material_probes_gpu_close(oa_material_probes *p){unsigned i,j;if(!p)return;
 for(i=0;i<p->count;i++){GLuint t=p->rows[i].texture;if(t){int first=1;for(j=0;j<i;j++)if(p->rows[j].texture==t)first=0;if(first)glDeleteTextures(1,&t);}}
 for(i=0;i<p->count;i++){p->rows[i].texture=0;p->rows[i].attempted=0;}
}
void oa_material_probes_close(oa_material_probes *p){free(p);}
