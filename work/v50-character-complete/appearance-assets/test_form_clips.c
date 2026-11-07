#define main old_selection_test_main
#include "test_selection.c"
#undef main
int main(int argc,char**argv){
 FILE*list,*f,*clips;char path[4096],cp[4096];unsigned frame_count=0,plans=0,pi,fr;
 if(argc!=3)return 2;list=fopen(argv[1],"r");if(!list)return 3;
 while(fgets(path,sizeof(path),list)){long n;path[strcspn(path,"\r\n")]=0;f=fopen(path,"rb");if(!f||cached>=256)return 4;
  fseek(f,0,SEEK_END);n=ftell(f);rewind(f);cache[cached].b=malloc(n);if(!cache[cached].b||fread(cache[cached].b,1,n,f)!=(size_t)n)return 5;fclose(f);
  if(!oa_am_open(&cache[cached].m,cache[cached].b,n))return 6;cached++;}
 fclose(list);clips=fopen(argv[2],"r");if(!clips)return 7;
 while(fgets(cp,sizeof(cp),clips)){long n;unsigned rig;unsigned char*b;uint32_t nj,nf;
  cp[strcspn(cp,"\r\n")]=0;rig=(unsigned)strtoul(strrchr(cp,'\\')?strrchr(cp,'\\')+1:cp,0,10);
  f=fopen(cp,"rb");if(!f)return 8;fseek(f,0,SEEK_END);n=ftell(f);rewind(f);b=malloc(n);if(!b||fread(b,1,n,f)!=(size_t)n)return 9;fclose(f);
  memcpy(&nj,b,4);memcpy(&nf,b+4,4);if(nj!=64||(size_t)n!=12+(size_t)nj*nf*48)return 10;
  for(pi=0;pi<oa_ap_profile_count();pi++){
   const oa_ap_profile*p=oa_ap_profile_get(pi);oa_ap_selection s;oa_ap_plan plan;uint32_t gear[]={1321542,1321543,1330206,1330207,1381439};
   if(p->creator_fab!=rig&&p->gameplay_fab!=rig)continue;memset(&s,0,sizeof(s));s.profile=pi;s.form=p->gameplay_fab==rig;
   if(s.form){s.equipped_type_ids=gear;s.equipped_count=5;}
   if(!oa_ap_plan_build(&s,lookup,0,&plan))return 11;plans++;
   for(fr=0;fr<nf;fr++){
    float pose[32*64*12];unsigned k,c,a;if(!oa_ap_plan_pose(&plan,lookup,0,(float*)(b+12+(size_t)fr*nj*48),nj,pose,32*64*12))return 12;
    for(k=0;k<plan.count*64*12;k++)if(!isfinite(pose[k]))return 13;
    if(fr==0||fr==nf/2||fr==nf-1)for(c=0;c<plan.count;c++){oa_am_model m;oa_am_chunk bon;
     if(!lookup(0,plan.component[c].fab,&m)||!oa_am_find(&m,"BONE",&bon))return 14;
     for(a=0;a<oa_am_surface_count(&m);a++){oa_am_surface sf;float pal[78*12];
      if(!oa_am_surface_get(&m,a,&sf))return 15;
      if(!oa_ap_component_surface_visible(&plan,c,&sf))continue;
      if(!oa_am_palette(&m,a,pose+c*64*12,bon.count,0,pal,78*12))return 16;
      for(k=0;k<sf.palette_count*12;k++)if(!isfinite(pal[k]))return 17;
     }}
    frame_count++;
   }
  }free(b);
 }
 fclose(clips);printf("{\"source_form_clip_plans\":%u,\"all_decoded_frames_component_pose_finite\":%u,\"endpoint_midpoint_palettes_pass\":true}\n",plans,frame_count);return 0;
}