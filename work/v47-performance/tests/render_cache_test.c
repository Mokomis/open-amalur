#include "oa_render_cache.h"
#include "oa_cpu_policy.h"
#include <stdio.h>
#ifdef _WIN32
#include <windows.h>
#endif
#include <stdlib.h>
#include <string.h>
static unsigned queries,active,binds,epoch;static GLuint physical[8];
#define CHECK(c) do{if(!(c)){fprintf(stderr,"FAIL line%d: %s\n",__LINE__,#c);return 1;}}while(0)
GLint glGetUniformLocation(GLuint p,const char *s){queries++;return !strcmp(s,"missing")?-1:(GLint)(p*31u+(unsigned char)s[0]+epoch);}
void glActiveTexture(GLenum unit){active=unit-GL_TEXTURE0;}
void glBindTexture(GLenum target,GLuint texture){(void)target;if(active>=8)abort();physical[active]=texture;binds++;}
int main(void){GLuint slots[8];unsigned i,j;GLint a;char name[96];
 oa_render_cache_reset();oa_render_cache_enabled=1;
 a=oa_cached_uniform(1,"mvp");CHECK(queries==1);
 CHECK(oa_cached_uniform(1,"mvp")==a&&queries==1);
 CHECK(oa_cached_uniform(2,"mvp")!=a&&queries==2);
 CHECK(oa_cached_uniform(1,"missing")==-1);
 CHECK(oa_cached_uniform(1,"missing")==-1&&queries==3);
 oa_render_cache_begin_frame();CHECK(oa_render_cache_get_stats()->uniform_requests==0);
 CHECK(oa_cached_uniform(1,"mvp")==a&&queries==3);
 CHECK(oa_render_cache_get_stats()->uniform_hits==1);
 oa_render_cache_enabled=0;oa_cached_uniform(1,"mvp");CHECK(queries==4);
 oa_render_cache_enabled=1;epoch=100;oa_render_cache_reset();
 CHECK(oa_cached_uniform(1,"mvp")==a+100&&queries==5);
 memset(name,'x',sizeof(name)-1);name[sizeof(name)-1]=0;
 oa_cached_uniform(1,name);oa_cached_uniform(1,name);CHECK(queries==7);
 for(i=0;i<1100;i++){snprintf(name,sizeof(name),"uniform_%u",i);CHECK(oa_cached_uniform(3,name)==3*31+'u'+100);}
 /* The table can saturate without corrupting cached or fallback results. */
 CHECK(oa_cached_uniform(1,"mvp")==a+100);
 for(i=0;i<8;i++)slots[i]=~0u;
 for(i=0;i<8;i++)oa_cached_bind_texture(slots,i,100+i);
 CHECK(binds==8);
 for(j=0;j<50;j++){for(i=0;i<8;i++)oa_cached_bind_texture(slots,i,100+i);for(i=0;i<8;i++)CHECK(physical[i]==100+i);}
 CHECK(binds==8&&oa_render_cache_get_stats()->texture_hits==400);
 /* Disabled path always binds; new phase invalidation prevents external-state reuse. */
 oa_render_cache_enabled=0;oa_cached_bind_texture(slots,3,103);CHECK(binds==9);
 oa_render_cache_enabled=1;physical[3]=777;for(i=0;i<8;i++)slots[i]=~0u;
 oa_cached_bind_texture(slots,3,103);CHECK(physical[3]==103&&binds==10);
 CHECK(oa_cpu_stream_workers(0,0)==1&&oa_cpu_stream_workers(1,0)==1);
 CHECK(oa_cpu_stream_workers(2,0)==1&&oa_cpu_stream_workers(4,0)==1);
 CHECK(oa_cpu_stream_workers(6,0)==2&&oa_cpu_stream_workers(8,0)==3);
 CHECK(oa_cpu_stream_workers(12,0)==4&&oa_cpu_stream_workers(64,0)==4);
 for(i=1;i<256;i++)for(j=0;j<12;j++){unsigned n=oa_cpu_stream_workers(i,(int)j);CHECK(n>=1&&n<=4&&n<=i);}
 CHECK(oa_cpu_available()>=1);
#ifdef _WIN32
 {DWORD_PTR old=0,system=0,subset=0;unsigned n=0,bit;
 CHECK(GetProcessAffinityMask(GetCurrentProcess(),&old,&system));
 for(bit=0;bit<sizeof(DWORD_PTR)*8;bit++)if(old&((DWORD_PTR)1<<bit)){
  subset|=(DWORD_PTR)1<<bit;n++;
  if(n==1||n==2||n==4){
   CHECK(SetProcessAffinityMask(GetCurrentProcess(),subset));
   CHECK(oa_cpu_available()==n);
  }
  if(n==4)break;
 }
 CHECK(SetProcessAffinityMask(GetCurrentProcess(),old));
 }
#endif
 printf("PASS cache lifecycle, negative locations, saturation, binding-state equivalence, disabled fallback; worker policy and %u live available CPUs\n",oa_cpu_available());return 0;}
