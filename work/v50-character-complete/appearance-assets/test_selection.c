#include "oa_appearance_selection.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef struct {unsigned char*b;oa_am_model m;} cache_row;
static cache_row cache[256];static unsigned cached;
static int lookup(void*u,uint32_t fab,oa_am_model*out){unsigned i;(void)u;
 for(i=0;i<cached;i++)if(cache[i].m.fab==fab){*out=cache[i].m;return 1;}return 0;}
static int test(const oa_ap_selection*s,FILE*out,int dump){
 oa_ap_plan p;float worlds[32*64*12];uint32_t c,a;unsigned tris=0;oa_am_model m;oa_am_surface sf;
 if(!oa_ap_plan_build(s,lookup,0,&p)){printf("PLAN FAIL profile%u form%u ids%u/%u/%u/%u/%u/%u\n",s->profile,s->form,s->option_ids[0],s->option_ids[1],s->option_ids[2],s->option_ids[3],s->option_ids[4],s->option_ids[5]);return 0;}
 if(!oa_ap_plan_pose(&p,lookup,0,NULL,0,worlds,32*64*12)){puts("POSEFAIL");return 0;}
 for(c=0;c<p.count;c++){float pal[78*12];oa_am_chunk bones;
  if(!lookup(0,p.component[c].fab,&m)||!oa_am_find(&m,"BONE",&bones))return 0;
  for(a=0;a<oa_am_surface_count(&m);a++){
   if(!oa_am_surface_get(&m,a,&sf))return 0;
   if(!oa_ap_component_surface_visible(&p,c,&sf))continue;
   if(!oa_am_palette(&m,a,worlds+c*64*12,bones.count,0,pal,78*12))return 0;
   tris+=sf.index_count/3;
  }
 }
 if(dump){fprintf(out,"{\"profile\":%u,\"form\":%u,\"root\":%u,\"tattoo\":%u,\"triangles\":%u,\"components\":[",s->profile,s->form,p.root_fab,p.tattoo_texture,tris);
  for(c=0;c<p.count;c++)fprintf(out,"%s{\"fab\":%u,\"source_type\":%u,\"parent\":%d,\"map\":%u,\"slot\":%u}",c?",":"",p.component[c].fab,p.component[c].source_type,p.component[c].parent,p.component[c].map_index,p.component[c].slot_key);
  fprintf(out,"]}\n");
 }
 return 1;
}
int main(int argc,char**argv){
 FILE*list,*f,*out;char path[4096];unsigned pi,form,c,oi,cases=0;uint32_t gear[]={1321542,1321543,1330206,1330207,1381439};
 if(argc!=3)return 2;list=fopen(argv[1],"r");out=fopen(argv[2],"w");if(!list||!out)return 3;
 while(fgets(path,sizeof(path),list)){long n;path[strcspn(path,"\r\n")]=0;f=fopen(path,"rb");if(!f||cached>=256)return 4;
  fseek(f,0,SEEK_END);n=ftell(f);rewind(f);cache[cached].b=malloc(n);if(!cache[cached].b||fread(cache[cached].b,1,n,f)!=(size_t)n)return 5;fclose(f);
  if(!oa_am_open(&cache[cached].m,cache[cached].b,n))return 6;cached++;}
 fclose(list);
 for(pi=0;pi<oa_ap_profile_count();pi++)for(form=0;form<2;form++){
  oa_ap_selection s;memset(&s,0,sizeof(s));s.profile=pi;s.form=form;if(form){s.equipped_type_ids=gear;s.equipped_count=5;}
  if(!test(&s,out,1))return 7;cases++;
  for(c=0;c<OA_AP_CATEGORIES;c++)for(oi=0;oi<oa_ap_option_count(pi,c);oi++){
   const oa_ap_option*o=oa_ap_option_at(pi,c,oi);s.option_ids[c]=o->simtype;
   if(!test(&s,out,0))return 8;cases++;s.option_ids[c]=0;
  }
  {unsigned hi,di,ci;
   for(hi=0;hi<oa_ap_option_count(pi,OA_AP_HEAD);hi++){
    const oa_ap_option*head=oa_ap_option_at(pi,OA_AP_HEAD,hi);s.option_ids[OA_AP_HEAD]=head->simtype;
    for(ci=OA_AP_HAIR;ci<OA_AP_CATEGORIES;ci++)if(ci!=OA_AP_TATTOO)
     for(di=0;di<oa_ap_option_count(pi,ci);di++){
      const oa_ap_option*dep=oa_ap_option_at(pi,ci,di);s.option_ids[ci]=dep->simtype;
      if(!test(&s,out,0))return 18;cases++;s.option_ids[ci]=0;
     }
   }s.option_ids[OA_AP_HEAD]=0;
  }
  s.option_ids[0]=0xffffffff;if(oa_ap_plan_build(&s,lookup,0,&(oa_ap_plan){0}))return 9;
 }

 {unsigned ck,frame,frames=0;FILE*binary=fopen("default-animated-pose-samples.bin","wb");
 for(pi=0;pi<oa_ap_profile_count();pi++){
  const oa_ap_profile*profile=oa_ap_profile_get(pi);char clip_path[256];unsigned char*clip;long clen;uint32_t nj,nf;oa_ap_selection sel;oa_ap_plan plan;
  sprintf(clip_path,"clips/%u-%u.local-trs.bin",profile->creator_fab,profile->creator_idle_clip);
  f=fopen(clip_path,"rb");if(!f)return 10;fseek(f,0,SEEK_END);clen=ftell(f);rewind(f);clip=malloc(clen);if(!clip||fread(clip,1,clen,f)!=(size_t)clen)return 11;fclose(f);
  memcpy(&nj,clip,4);memcpy(&nf,clip+4,4);if(nj!=64||clen!=12+(long)nj*nf*48)return 12;
  memset(&sel,0,sizeof(sel));sel.profile=pi;if(!oa_ap_plan_build(&sel,lookup,0,&plan))return 13;
  for(frame=0;frame<nf;frame++){
   float pose[32*64*12];if(!oa_ap_plan_pose(&plan,lookup,0,(const float*)(clip+12+frame*nj*48),nj,pose,32*64*12))return 14;
   for(ck=0;ck<plan.count*64*12;ck++)if(!isfinite(pose[ck]))return 15;
   if(frame==0||frame==nf/2||frame==nf-1){
    uint32_t h[3]={pi,frame,plan.count};fwrite(h,4,3,binary);
    for(ck=0;ck<plan.count;ck++){
     oa_am_model mod;oa_am_chunk bon;uint32_t row[4];if(!lookup(0,plan.component[ck].fab,&mod)||!oa_am_find(&mod,"BONE",&bon))return 16;
     row[0]=mod.fab;row[1]=(uint32_t)plan.component[ck].parent;row[2]=plan.component[ck].map_index;row[3]=bon.count;
     fwrite(row,4,4,binary);fwrite(pose+ck*64*12,48,bon.count,binary);
    }
   }frames++;
  }free(clip);
 }
 fclose(binary);printf("{\"creator_default_animated_frames\":%u,\"all_full_component_poses_finite\":true}\n",frames);
 }
 fclose(out);printf("{\"models\":%u,\"default_and_option_plans\":%u,\"all_parse_pose_palette_pass\":true,\"invalid_id_rejected\":true}\n",cached,cases);
 return 0;
}