#include "oa_scene_profile.h"
#include <android/asset_manager.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
AAsset *AAssetManager_open(AAssetManager*m,const char*n,int mode){(void)m;(void)n;(void)mode;return 0;}
off64_t AAsset_getLength64(AAsset*a){(void)a;return 0;}
const void *AAsset_getBuffer(AAsset*a){(void)a;return 0;}
void AAsset_close(AAsset*a){(void)a;}
int __android_log_print(int p,const char*t,const char*f,...){(void)p;(void)t;(void)f;return 0;}
#define CHECK(c) do{if(!(c)){fprintf(stderr,"FAIL %d %s\n",__LINE__,#c);return 1;}}while(0)
int main(void){FILE*f=fopen("../preview-assets/scene-profile.bin","rb");long n;unsigned char*b,*bad;oa_scene_profile s={0};float (*old)[8];unsigned nan=0x7fc00000,huge=0xffffffffu;
 CHECK(f);fseek(f,0,SEEK_END);n=ftell(f);rewind(f);b=malloc(n);bad=malloc(n);CHECK(b&&bad);CHECK(fread(b,1,n,f)==n);fclose(f);
 CHECK(oa_scene_profile_parse(&s,b,n));CHECK(s.space==1417252&&s.region==1262814&&s.light_count==113);CHECK(s.spawn[0]==4312&&s.spawn[1]==2806);old=s.lights;
 CHECK(!oa_scene_profile_parse(&s,b,n-1)&&s.lights==old);memcpy(bad,b,n);bad[0]=0;CHECK(!oa_scene_profile_parse(&s,bad,n)&&s.lights==old);
 memcpy(bad,b,n);memcpy(bad+24,&huge,4);CHECK(!oa_scene_profile_parse(&s,bad,n)&&s.lights==old);
 memcpy(bad,b,n);memcpy(bad+36,&nan,4);CHECK(!oa_scene_profile_parse(&s,bad,n)&&s.lights==old);
 memcpy(bad,b,n);memcpy(bad+152,&nan,4);CHECK(!oa_scene_profile_parse(&s,bad,n)&&s.lights==old);
 memcpy(bad,b,n);memset(bad+20,0,4);CHECK(!oa_scene_profile_parse(&s,bad,n)&&s.lights==old); /* unlabelled ambient fallback prohibited */
 CHECK(!oa_scene_profile_load(&s,0)&&s.lights==old);
 CHECK(oa_scene_profile_parse(&s,b,n));oa_scene_profile_close(&s);CHECK(!s.active&&!s.lights);oa_scene_profile_close(&s);
 free(b);free(bad);puts("PASS real opening envelope: scene/spawn/lights, malformed/truncated/NaN/count rejection, failure atomicity, explicit preview requirement, optional-asset fallback and repeat lifecycle");return 0;}
