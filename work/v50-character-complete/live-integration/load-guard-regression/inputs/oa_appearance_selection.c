#include "oa_appearance_selection.h"
#include <string.h>
#include "oa_appearance_selection_data.h"
static const uint32_t categories[]={701554,481813,1139995,771605,1756520,9441502};
static uint32_t count_options(void){return (uint32_t)(sizeof(options)/sizeof(options[0]));}
uint32_t oa_ap_profile_count(void){return (uint32_t)(sizeof(profiles)/sizeof(profiles[0]));}
const oa_ap_profile *oa_ap_profile_get(uint32_t i){return i<oa_ap_profile_count()?profiles+i:0;}
const oa_ap_option *oa_ap_option_get(uint32_t id){uint32_t i;for(i=0;i<count_options();i++)if(options[i].simtype==id)return options+i;return 0;}
static int allowed(const oa_ap_profile*p,const oa_ap_option*o,uint32_t c){
 return p&&o&&c<OA_AP_CATEGORIES&&o->category_hash==categories[c]&&(p->race_bit&o->race_mask)&&(p->sex_bit&o->sex_mask);
}
uint32_t oa_ap_option_count(uint32_t pi,uint32_t c){const oa_ap_profile*p=oa_ap_profile_get(pi);uint32_t i,n=0;
 for(i=0;i<count_options();i++)if(allowed(p,options+i,c))n++;return n;
}
const oa_ap_option *oa_ap_option_at(uint32_t pi,uint32_t c,uint32_t at){const oa_ap_profile*p=oa_ap_profile_get(pi);uint32_t i,n=0;
 for(i=0;i<count_options();i++)if(allowed(p,options+i,c)){if(n++==at)return options+i;}return 0;
}
static int child_add(oa_ap_plan*p,oa_ap_model_lookup get,void*u,uint32_t parent,uint32_t mi,
 uint32_t fab,uint32_t source,float scale){
 oa_am_model pm,cm;oa_am_child_map map;oa_am_chunk pb,cb;uint32_t i,j;oa_ap_component*n;
 if(!get(u,p->component[parent].fab,&pm)||!oa_am_child_map_get(&pm,mi,&map))return 0;
 if(!fab)return 1;
 if(!get(u,fab,&cm)||!oa_am_find(&pm,"BONE",&pb)||!oa_am_find(&cm,"BONE",&cb))return 0;
 /* Only starterUnarmed hasnonunit source scale; itsselectedFAB hasnoassembly. */
 if(scale!=1.f&&oa_am_surface_count(&cm)!=0)return 0;
 /* Native00c8b130 admission checks mapped child indices. Check parent too for safe inputs. */
 for(j=0;j<map.count;j++){int32_t pi,ci;memcpy(&pi,map.pairs12+j*12,4);memcpy(&ci,map.pairs12+j*12+4,4);
  if(pi<0||ci<0||(uint32_t)pi>=pb.count||(uint32_t)ci>=cb.count)return 0;}
 for(i=1;i<p->count;i++)if(p->component[i].parent==(int32_t)parent&&p->component[i].map_index==mi)break;
 if(i==p->count){if(p->count>=32)return 0;p->count++;}
 n=p->component+i;n->fab=fab;n->source_type=source;n->slot_key=map.slot_key;n->map_index=mi;
 n->parent=(int32_t)parent;n->native_flags=map.flags;n->source_scale=scale;return 1;
}
static int find_map(oa_ap_model_lookup get,void*u,uint32_t fab,uint32_t key,int alias,uint32_t*out){
 oa_am_model m;uint32_t i;if(!get(u,fab,&m))return 0;
 for(i=0;i<oa_am_child_map_count(&m);i++){oa_am_child_map a;if(!oa_am_child_map_get(&m,i,&a))return 0;
  if((alias?a.mount_key:a.slot_key)==key){*out=i;return 1;}}
 return 0;
}
static int by_alias(oa_ap_plan*p,oa_ap_model_lookup get,void*u,uint32_t alias,uint32_t fab,uint32_t source,float scale){
 uint32_t map,i;if(!alias||!fab)return 1;
 /* Native00f10660: root alias has priority; only missing alias falls back to Head. */
 if(find_map(get,u,p->root_fab,alias,1,&map))return child_add(p,get,u,0,map,fab,source,scale);
 for(i=1;i<p->count;i++)if(p->component[i].parent==0){
  oa_am_model root;oa_am_child_map a;if(!get(u,p->root_fab,&root)||!oa_am_child_map_get(&root,p->component[i].map_index,&a))return 0;
  if(a.mount_key==701554&&find_map(get,u,p->component[i].fab,alias,1,&map))return child_add(p,get,u,i,map,fab,source,scale);
 }
 return 0;
}
int oa_ap_plan_build(const oa_ap_selection*s,oa_ap_model_lookup get,void*u,oa_ap_plan*out){
 const oa_ap_profile*p;oa_ap_plan q;const oa_ap_option*selected[OA_AP_CATEGORIES];uint32_t i,j,sex,map;
 if(!s||!out||!get||(p=oa_ap_profile_get(s->profile))==0||s->form>1||
 (s->equipped_count&&!s->equipped_type_ids))return 0;
 memset(&q,0,sizeof(q));sex=p->sex_bit==1?0:1;q.form=s->form;
 q.root_fab=s->form?p->gameplay_fab:p->creator_fab;q.actor_type=s->form?p->gameplay_type:p->creator_type;
 for(i=0;i<OA_AP_CATEGORIES;i++){
  uint32_t id=s->option_ids[i]?s->option_ids[i]:p->default_options[i];selected[i]=id?oa_ap_option_get(id):0;
  if(id&&!allowed(p,selected[i],i))return 0;q.selected_options[i]=id;
 }
 q.component[0].fab=q.root_fab;q.component[0].source_type=q.actor_type;q.component[0].parent=-1;q.component[0].source_scale=1;q.count=1;
 for(i=0;i<base_counts[s->profile][s->form];i++){const base_pair*b=bases[s->profile][s->form]+i;
  if(find_map(get,u,q.root_fab,b->slot,0,&map)&&!child_add(&q,get,u,0,map,b->fab,q.actor_type,1))return 0;}
 /* Source head must be installed before other cosmetics use Head fallback maps. */
 for(i=0;i<OA_AP_CATEGORIES;i++)if(selected[i]){
  const oa_ap_option*o=selected[i];
  if(i==OA_AP_TATTOO){q.tattoo_texture=o->tattoo_texture;continue;}
  if(!by_alias(&q,get,u,o->mount_hash,o->model_variants[sex],o->simtype,1))return 0;
 }
 for(i=0;i<s->equipped_count;i++){
  const equip_row*e=0;for(j=0;j<sizeof(equipment)/sizeof(equipment[0]);j++)if(equipment[j].sim==s->equipped_type_ids[i]){e=equipment+j;break;}
  if(!e||!by_alias(&q,get,u,e->mount,e->fab[sex],e->sim,e->scale))return 0;
 }
 *out=q;return 1;
}
int oa_ap_plan_pose(const oa_ap_plan*p,oa_ap_model_lookup get,void*u,const float*local,
 uint32_t n,float*out,size_t cap){
 uint32_t i;oa_am_model root;if(!p||!get||!out||p->count>32||cap<(size_t)p->count*64*12||!get(u,p->root_fab,&root))return 0;
 if(local){if(!oa_am_local_pose(&root,local,n,out,64*12))return 0;}
 else if(!oa_am_rest_world(&root,out,64*12))return 0;
 for(i=1;i<p->count;i++){
  oa_am_model parent,child;oa_am_chunk pb;int32_t pi=p->component[i].parent;
  if(pi<0||(uint32_t)pi>=i||!get(u,p->component[pi].fab,&parent)||
   !get(u,p->component[i].fab,&child)||!oa_am_find(&parent,"BONE",&pb))return 0;
  if(!oa_am_child_pose(&parent,p->component[i].map_index,out+pi*64*12,pb.count,&child,out+i*64*12,64*12))return 0;
 }
 return 1;
}
int oa_ap_component_surface_visible(const oa_ap_plan*p,uint32_t c,const oa_am_surface*s){
 return p&&s&&c<p->count&&s->material_id!=0&&(s->group_mask&(1u<<1))!=0;
}
