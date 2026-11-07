#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stddef.h>
#include <math.h>
#include <assert.h>
#include "oa_items.h"
static const char SAVE_MAGIC[8]={'O','A','S','A','V','0','0','2'};
typedef struct oa_save{char magic[8];int world;float feet[3],yaw,pitch,health;oa_bag bag;uint32_t space;}oa_save;
typedef struct legacy_save{char magic[8];int world;float feet[3],yaw,pitch,health;oa_bag bag;}legacy_save;
int oa_save_write(const oa_save *save,const char *path){oa_save t=*save;FILE *f;int ok;if(t.space>0x0fffffffu)return 0;memcpy(t.magic,SAVE_MAGIC,8);f=fopen(path,"wb");if(!f)return 0;ok=fwrite(&t,sizeof(t),1,f)==1;return fclose(f)==0&&ok;}
int oa_save_read(oa_save *save,const char *path){FILE *f=fopen(path,"rb");oa_save t;size_t bytes;int ok,i;if(!f)return 0;memset(&t,0,sizeof(t));bytes=fread(&t,1,sizeof(t),f);ok=!ferror(f)&&(bytes==offsetof(oa_save,space)||bytes==sizeof(t));if(ok)ok=fgetc(f)==EOF&&!ferror(f);fclose(f);if(!ok||memcmp(t.magic,SAVE_MAGIC,8)||t.world<0||t.world>1||t.space>0x0fffffffu)return 0;for(i=0;i<3;i++)if(!isfinite(t.feet[i]))return 0;if(!isfinite(t.yaw)||!isfinite(t.pitch)||!isfinite(t.health))return 0;oa_bag_sanitize(&t.bag);*save=t;return 1;}
int legacy_save_read(legacy_save *save,const char *path){FILE *f=fopen(path,"rb");legacy_save t;int ok,i;if(!f)return 0;ok=fread(&t,sizeof(t),1,f)==1;fclose(f);if(!ok||memcmp(t.magic,SAVE_MAGIC,8)||t.world<0||t.world>1)return 0;for(i=0;i<3;i++)if(!isfinite(t.feet[i]))return 0;if(!isfinite(t.yaw)||!isfinite(t.pitch)||!isfinite(t.health))return 0;oa_bag_sanitize(&t.bag);*save=t;return 1;}
static unsigned checks;
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"line%d %s\n",__LINE__,#x);return 1;}}while(0)
static void bytes(const char *p,const void *b,size_t n){FILE*f=fopen(p,"wb");assert(f);assert(fwrite(b,1,n,f)==n);assert(fclose(f)==0);}
static size_t get(const char*p,unsigned char *b,size_t n){FILE*f=fopen(p,"rb");size_t k;assert(f);k=fread(b,1,n,f);assert(!ferror(f));assert(fclose(f)==0);return k;}
int main(void){oa_save s={0},out,bad,sentinel;legacy_save legacy;unsigned char buf[128]={0},prefix[88];size_t i,n;uint32_t ids[]={0,431638,431646,431650,0x0fffffff};
 CHECK(sizeof(legacy_save)==88);CHECK(sizeof(oa_save)==92);CHECK(offsetof(oa_save,space)==88);
 memcpy(s.magic,SAVE_MAGIC,8);s.world=1;s.feet[0]=1575.065f;s.feet[1]=-62759.402f;s.feet[2]=5146.719f;s.yaw=1.25f;s.pitch=-.3f;s.health=53.5f;oa_bag_new(&s.bag);s.bag.gold=12345;memcpy(prefix,&s,88);
 bytes("legacy.bin",&s,88);memset(&out,0xaa,sizeof(out));CHECK(oa_save_read(&out,"legacy.bin"));CHECK(out.space==0);CHECK(!memcmp(&out,prefix,88));
 for(i=0;i<sizeof(ids)/sizeof(ids[0]);i++){s.space=ids[i];CHECK(oa_save_write(&s,"new.bin"));n=get("new.bin",buf,sizeof buf);CHECK(n==92);CHECK(!memcmp(buf,prefix,88));CHECK(!memcmp(buf,"OASAV002",8));memset(&out,0xaa,sizeof out);CHECK(oa_save_read(&out,"new.bin"));CHECK(!memcmp(&out,&s,sizeof s));CHECK(legacy_save_read(&legacy,"new.bin"));CHECK(!memcmp(&legacy,prefix,88));}
 memset(&sentinel,0xa5,sizeof sentinel);out=sentinel;CHECK(!oa_save_read(&out,"missing.bin"));CHECK(!memcmp(&out,&sentinel,sizeof out));
 s.space=431646;memcpy(buf,&s,sizeof s);for(n=0;n<96;n++){if(n==88||n==92)continue;bytes("bad.bin",buf,n);out=sentinel;CHECK(!oa_save_read(&out,"bad.bin"));CHECK(!memcmp(&out,&sentinel,sizeof out));}
 bad=s;bad.magic[0]='X';bytes("bad.bin",&bad,92);CHECK(!oa_save_read(&out,"bad.bin"));
 bad=s;bad.world=2;bytes("bad.bin",&bad,92);CHECK(!oa_save_read(&out,"bad.bin"));
 bad=s;bad.space=0x10000000u;bytes("bad.bin",&bad,92);CHECK(!oa_save_read(&out,"bad.bin"));
 bytes("guard.bin",prefix,88);CHECK(!oa_save_write(&bad,"guard.bin"));CHECK(get("guard.bin",buf,sizeof buf)==88);CHECK(!memcmp(buf,prefix,88));
 for(i=0;i<6;i++){bad=s;if(i<3)bad.feet[i]=NAN;else if(i==3)bad.yaw=INFINITY;else if(i==4)bad.pitch=NAN;else bad.health=-INFINITY;bytes("bad.bin",&bad,92);CHECK(!oa_save_read(&out,"bad.bin"));}
 printf("{\"passed\":true,\"checks\":%u,\"legacy_bytes\":88,\"new_bytes\":92,\"space_offset\":88,\"user_files_touched\":false}\n",checks);return 0;}
