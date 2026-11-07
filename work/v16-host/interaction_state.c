#include "interaction_state.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <limits.h>
static int message(char *s,size_t n,const char *v){if(s&&n)snprintf(s,n,"%s",v);return 0;}
void oa_registry_init(oa_registry *r){unsigned i;memset(r,0,sizeof(*r));for(i=0;i<32;i++)r->objects[i].generation=1;}
oa_handle oa_object_create(oa_registry *r,uint32_t source,uint32_t type,uint32_t script,const float p[3]){
 unsigned i;oa_handle invalid={0,0};if(!r||!p||!isfinite(p[0])||!isfinite(p[1])||!isfinite(p[2]))return invalid;
 for(i=0;i<32;i++)if(!r->objects[i].alive&&r->objects[i].generation){oa_object *o=&r->objects[i];o->source_id=source;o->type_id=type;o->script_id=script;memcpy(o->position,p,12);o->alive=1;invalid.slot=i;invalid.generation=o->generation;return invalid;}return invalid;
}
const oa_object *oa_object_resolve(const oa_registry *r,oa_handle h){if(!r||h.slot>=32||!h.generation||!r->objects[h.slot].alive||r->objects[h.slot].generation!=h.generation)return NULL;return r->objects+h.slot;}
int oa_object_remove(oa_registry *r,oa_handle h){oa_object *o;if(!oa_object_resolve(r,h))return 0;o=r->objects+h.slot;o->alive=0;++o->generation;/* Wrapped slots retire permanently. */return 1;}
int oa_workbench_in_reach(const oa_registry *r,oa_handle h,const float p[3],float yaw){
 const oa_object *o=oa_object_resolve(r,h);double x,y,z,d;if(!o||!p||!isfinite(p[0])||!isfinite(p[1])||!isfinite(p[2])||!isfinite(yaw))return 0;
 x=o->position[0]-p[0];y=o->position[1]-p[1];z=o->position[2]-p[2];d=sqrt(x*x+y*y);
 return d<=300&&fabs(z)<=180&&(d<45||(x*cos(yaw)+y*sin(yaw))/d>=.55);
}
uint32_t oa_inventory_count(const oa_inventory *v,uint32_t id){unsigned i;for(i=0;i<v->count;i++)if(v->items[i].id==id)return v->items[i].count;return 0;}
int oa_inventory_set(oa_inventory *v,uint32_t id,uint32_t count){unsigned i;if(!id||count>1000000||v->count>1024)return 0;for(i=0;i<v->count;i++)if(v->items[i].id==id){if(count)v->items[i].count=count;else{v->items[i]=v->items[--v->count];}return 1;}if(!count)return 1;if(v->count==1024)return 0;v->items[v->count].id=id;v->items[v->count++].count=count;return 1;}
uint32_t oa_essence_count(const oa_catalog *c,const oa_inventory *v,const char *essence){size_t i;uint64_t sum=0;for(i=0;i<c->reagent_count;i++)if(!strcmp(c->reagents[i].essence,essence))sum+=oa_inventory_count(v,c->reagents[i].id);return sum>UINT32_MAX?UINT32_MAX:(uint32_t)sum;}
int oa_can_craft(const oa_catalog *c,const oa_inventory *v,const oa_formula *f,char *reason,size_t cap){
 unsigned i,j;if(!f||!f->product||!f->need_count||f->need_count>8)return message(reason,cap,"FORMULA DATA UNAVAILABLE");
 if(!oa_inventory_count(v,f->id))return message(reason,cap,"RECIPE NOT OWNED");
 if(v->alchemy_skill<f->difficulty)return message(reason,cap,"ALCHEMY SKILL TOO LOW");
 for(i=0;i<f->need_count;i++){uint64_t sum=0;if(!f->needs[i].essence||!f->needs[i].quantity)return message(reason,cap,"INVALID FORMULA DATA");for(j=0;j<f->need_count;j++)if(!strcmp(f->needs[i].essence,f->needs[j].essence))sum+=f->needs[j].quantity;if(sum>oa_essence_count(c,v,f->needs[i].essence))return message(reason,cap,"MISSING INGREDIENTS");}
 if(oa_inventory_count(v,f->product)>=1000000)return message(reason,cap,"PRODUCT LIMIT REACHED");
 if(v->count>=1024&&!oa_inventory_count(v,f->product))return message(reason,cap,"INVENTORY FULL");
 message(reason,cap,"READY TO CRAFT");return 1;
}
int oa_craft(const oa_catalog *c,oa_inventory *v,const oa_formula *f,char *reason,size_t cap){
 oa_inventory next;unsigned i;size_t j;if(!oa_can_craft(c,v,f,reason,cap))return 0;next=*v;
 for(i=0;i<f->need_count;i++){uint32_t left=f->needs[i].quantity;for(j=0;j<c->reagent_count&&left;j++)if(!strcmp(f->needs[i].essence,c->reagents[j].essence)){uint32_t n=oa_inventory_count(&next,c->reagents[j].id),take=n<left?n:left;if(!oa_inventory_set(&next,c->reagents[j].id,n-take))return message(reason,cap,"INVENTORY UPDATE FAILED");left-=take;}if(left)return message(reason,cap,"INVENTORY CHANGED");}
 if(!oa_inventory_set(&next,f->product,oa_inventory_count(&next,f->product)+1))return message(reason,cap,"INVENTORY UPDATE FAILED");
 *v=next;message(reason,cap,"CRAFTED ONE ITEM");return 1;
}
/* Project-owned inventory format, never an Amalur save. Fixed little endian
 * words, bounded counts, checksum, duplicate-ID rejection and atomic commit. */
static uint32_t hash(const unsigned char *b,size_t n){uint32_t h=2166136261u;size_t i;for(i=0;i<n;i++)h=(h^b[i])*16777619u;return h;}
static void put(unsigned char *p,uint32_t x){unsigned i;for(i=0;i<4;i++)p[i]=(unsigned char)(x>>(i*8));}
static uint32_t get(const unsigned char *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
int oa_inventory_load(oa_inventory *v,const char *path,char *error,size_t cap){unsigned char b[8220];size_t n;unsigned i;oa_inventory next={0};FILE *f=fopen(path,"rb");if(!f)return message(error,cap,"INVENTORY FILE ABSENT");n=fread(b,1,sizeof(b),f);if(ferror(f)||fgetc(f)!=EOF){fclose(f);return message(error,cap,"INVENTORY READ FAILED");}fclose(f);
 if(n<20||memcmp(b,"OAINV001",8)||get(b+8)>1024||get(b+12)>100||n!=20+8*(size_t)get(b+8)||hash(b,n-4)!=get(b+n-4))return message(error,cap,"INVENTORY FILE INVALID");
 next.alchemy_skill=get(b+12);for(i=0;i<get(b+8);i++){uint32_t id=get(b+16+8*i),count=get(b+20+8*i);if(!id||!count||oa_inventory_count(&next,id)||!oa_inventory_set(&next,id,count))return message(error,cap,"INVENTORY ENTRY INVALID");}*v=next;return 1;
}
int oa_inventory_save(const oa_inventory *v,const char *path,char *error,size_t cap){unsigned char b[8220];char tmp[1024];size_t n;unsigned i;FILE *f;int okay;
 if(v->count>1024||v->alchemy_skill>100||snprintf(tmp,sizeof(tmp),"%s.pending",path)>=(int)sizeof(tmp))return message(error,cap,"INVENTORY SAVE INVALID");
 memcpy(b,"OAINV001",8);put(b+8,v->count);put(b+12,v->alchemy_skill);for(i=0;i<v->count;i++){if(!v->items[i].id||!v->items[i].count||v->items[i].count>1000000)return message(error,cap,"INVENTORY ENTRY INVALID");put(b+16+8*i,v->items[i].id);put(b+20+8*i,v->items[i].count);}n=20+8*v->count;put(b+n-4,hash(b,n-4));
 f=fopen(tmp,"wb");if(!f)return message(error,cap,"INVENTORY SAVE FAILED");okay=fwrite(b,1,n,f)==n;if(fflush(f))okay=0;if(fclose(f))okay=0;if(!okay||rename(tmp,path)){remove(tmp);return message(error,cap,"INVENTORY COMMIT FAILED");}return 1;
}
