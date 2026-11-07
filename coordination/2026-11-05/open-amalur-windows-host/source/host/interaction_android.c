#include "interaction_android.h"
#include "exploration_input.h"
#include "integration_data.inc"
#include "workbench_placement.inc"
#include <android/keycodes.h>
#include <android/log.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,"OpemAmalurInteraction",__VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurInteraction",__VA_ARGS__)
int oa_android_start(oa_interaction *s,amalur_runtime *r,AAssetManager *assets,const char *path){
 AAsset *asset=NULL;char *source=NULL,error[256];off64_t length;size_t offset=0,i,j;oa_reagent *reagents=NULL;oa_formula *formulas=NULL;const float player_position[3]={0,0,0};
 memset(s,0,sizeof(*s));oa_registry_init(&s->registry);s->workbench=oa_object_create(&s->registry,OA_WORKBENCH_SOURCE,OA_WORKBENCH_TYPE,OA_WORKBENCH_SCRIPT,oa_workbench_position);s->player=oa_object_create(&s->registry,0,0,0,player_position);
 if(!r)goto fail;
 reagents=(oa_reagent*)calloc(OA_REAGENT_COUNT,sizeof(*reagents));formulas=(oa_formula*)calloc(OA_FORMULA_CATALOG_COUNT,sizeof(*formulas));if(!reagents||!formulas)goto fail;
 for(i=0;i<OA_REAGENT_COUNT;i++){reagents[i].id=oa_reagents[i].id;reagents[i].symbol=oa_reagents[i].symbol;reagents[i].essence=oa_reagents[i].essence;}
 for(i=0;i<OA_FORMULA_CATALOG_COUNT;i++){formulas[i].id=oa_formula_catalog[i].id;formulas[i].symbol=oa_formula_catalog[i].symbol;for(j=0;j<OA_FORMULA_COUNT;j++)if(oa_formulas[j].id==formulas[i].id){unsigned k;if(oa_formulas[j].need_count>8)goto fail;formulas[i].product=oa_formulas[j].product;formulas[i].difficulty=oa_formulas[j].difficulty;formulas[i].need_count=oa_formulas[j].need_count;for(k=0;k<formulas[i].need_count;k++){formulas[i].needs[k].essence=oa_formulas[j].needs[k].essence;formulas[i].needs[k].quantity=oa_formulas[j].needs[k].quantity;}}}
 s->catalog.reagents=reagents;s->catalog.reagent_count=OA_REAGENT_COUNT;s->catalog.formulas=formulas;s->catalog.formula_count=OA_FORMULA_CATALOG_COUNT;
 asset=AAssetManager_open(assets,"interactions/Workbench.lua",AASSET_MODE_STREAMING);if(!asset)goto fail;length=AAsset_getLength64(asset);if(length<1||length>1024*1024)goto fail;source=(char*)malloc((size_t)length);if(!source)goto fail;
 while(offset<(size_t)length){int n=AAsset_read(asset,source+offset,(size_t)length-offset);if(n<=0)goto fail;offset+=(size_t)n;}
 if(oa_lua_install(r,s,source,(size_t)length,error,sizeof(error))){LOGE("Recovered Workbench registration failed: %s",error);goto fail;}
 free(source);AAsset_close(asset);s->inventory_writable=1;
 {FILE *f=fopen(path,"rb");if(f){fclose(f);if(!oa_inventory_load(&s->inventory,path,error,sizeof(error))){s->inventory_writable=0;LOGE("Preserved unreadable project inventory: %s",error);}}}
 LOGI("Workbench ready source=%u type=%u script=%u position=(%.3f %.3f %.3f) engine_owned_handles=1 native_handle_abi=0",OA_WORKBENCH_SOURCE,OA_WORKBENCH_TYPE,OA_WORKBENCH_SCRIPT,oa_workbench_position[0],oa_workbench_position[1],oa_workbench_position[2]);
 LOGI("Alchemy catalog source_sha256=%s profile=%s reagents=%u catalog_recipes=%u verified_formula_rows=%u inventory_entries=%u imported_native_save=0 production_grants=0",oa_catalog_input_sha256,oa_catalog_content_profile,OA_REAGENT_COUNT,OA_FORMULA_CATALOG_COUNT,OA_FORMULA_COUNT,s->inventory.count);return 1;
fail:if(asset)AAsset_close(asset);free(source);free(reagents);free(formulas);s->catalog.reagents=NULL;s->catalog.formulas=NULL;s->ready=0;LOGE("Workbench interaction unavailable; no Lua dispatch enabled");return 0;
}
void oa_android_close(oa_interaction *s){free((void*)s->catalog.reagents);free((void*)s->catalog.formulas);memset(s,0,sizeof(*s));}
static void page(oa_interaction *s,int direction){size_t n=s->tab?s->catalog.formula_count:s->catalog.reagent_count;int max=(int)((n+5)/6)-1;if(max<0)max=0;s->page+=direction;if(s->page<0)s->page=0;if(s->page>max)s->page=max;if(s->tab)s->recipe_selected=s->page*6;}
static void tab(oa_interaction *s,int value){s->tab=value;s->page=0;s->recipe_selected=0;snprintf(s->status,sizeof(s->status),value?"CATALOG BROWSING - OWNERSHIP COMES FROM INVENTORY":"INVENTORY COUNTS ARE FROM THIS ANDROID SESSION");}
static void craft(oa_interaction *s,const char *path){oa_inventory old;const oa_formula *f;if(!s->tab||(unsigned)s->recipe_selected>=s->catalog.formula_count)return;f=s->catalog.formulas+s->recipe_selected;if(!s->inventory_writable){snprintf(s->status,sizeof(s->status),"INVENTORY FILE NEEDS RECOVERY - NO ITEMS CHANGED");return;}old=s->inventory;
 if(oa_craft(&s->catalog,&s->inventory,f,s->status,sizeof(s->status))){char error[128];if(!oa_inventory_save(&s->inventory,path,error,sizeof(error))){s->inventory=old;snprintf(s->status,sizeof(s->status),"SAVE FAILED - NO ITEMS CHANGED");LOGE("Alchemy commit failed: %s",error);}else LOGI("Alchemy crafted recipe=%u product=%u inventory_entries=%u",f->id,f->product,s->inventory.count);}else LOGI("Alchemy blocked recipe=%u reason=%s inventory_unchanged=1",f->id,s->status);
}
int oa_android_modal_event(oa_interaction *s,AInputEvent *e,int w,int h,const char *path){
 int type=AInputEvent_getType(e);float scale=exploration_ui_scale(w,h);
 if(type==AINPUT_EVENT_TYPE_KEY&&AKeyEvent_getAction(e)==AKEY_EVENT_ACTION_DOWN&&!AKeyEvent_getRepeatCount(e)&&!(AKeyEvent_getFlags(e)&AKEY_EVENT_FLAG_CANCELED)){
  int k=AKeyEvent_getKeyCode(e);if(k==AKEYCODE_BACK||k==AKEYCODE_ESCAPE||k==AKEYCODE_BUTTON_B)s->window_open=0;
  else if(k==AKEYCODE_DPAD_LEFT)page(s,-1);else if(k==AKEYCODE_DPAD_RIGHT)page(s,1);
  else if(k==AKEYCODE_TAB)tab(s,!s->tab);
  else if(k==AKEYCODE_DPAD_UP||k==AKEYCODE_DPAD_DOWN){if(s->tab){int v=s->recipe_selected+(k==AKEYCODE_DPAD_DOWN?1:-1);if(v>=0&&(size_t)v<s->catalog.formula_count){s->recipe_selected=v;s->page=v/6;}}}
  else if(k==AKEYCODE_E||k==AKEYCODE_BUTTON_A)craft(s,path);
 }
 if(type==AINPUT_EVENT_TYPE_MOTION&&(AInputEvent_getSource(e)&AINPUT_SOURCE_TOUCHSCREEN)==AINPUT_SOURCE_TOUCHSCREEN&&((AMotionEvent_getAction(e)&AMOTION_EVENT_ACTION_MASK)==AMOTION_EVENT_ACTION_DOWN)&&AMotionEvent_getPointerCount(e)){
  float x=AMotionEvent_getX(e,0)/scale,y=AMotionEvent_getY(e,0)/scale,W=w/scale,H=h/scale;if(!isfinite(x)||!isfinite(y))return 1;
  if(y>=20&&y<=60&&x>=W-140)s->window_open=0;
  else if(y>=88&&y<=124&&x>=32&&x<=484)tab(s,x>=264);
  else if(y>=H-100&&y<=H-58){if(x>=32&&x<=172)page(s,-1);else if(x>=390&&x<=530)page(s,1);else if(x>=W-240&&x<=W-32)craft(s,path);}
  else if(s->tab&&y>=163&&y<385){int row=(int)((y-163)/37),idx=s->page*6+row;if((size_t)idx<s->catalog.formula_count){char reason[100];const oa_formula *f=s->catalog.formulas+idx;s->recipe_selected=idx;oa_can_craft(&s->catalog,&s->inventory,f,reason,sizeof(reason));snprintf(s->status,sizeof(s->status),"%s",reason);}}
 }return 1;
}
