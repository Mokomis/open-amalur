#include "interaction_lua.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
static unsigned checks;
#define CHECK(x) do{++checks;if(!(x)){fprintf(stderr,"CHECK failed line %d: %s\n",__LINE__,#x);return 1;}}while(0)
int main(int argc,char **argv){
 oa_interaction s={0};float zero[3]={0,0,0},nearby[3]={-100,0,0},far[3]={-301,0,0};oa_handle old,newer;char error[256];amalur_runtime *r;amalur_runtime_config config={0};int n;FILE *f;char *source;long len;
 oa_reagent reagents[]={{101,"TEST_REAGENT_A","TEST_ESSENCE"},{102,"TEST_REAGENT_B","TEST_ESSENCE"}};
 oa_formula formula={201,301,"TEST_FORMULA",10,2,{{"TEST_ESSENCE",2},{"TEST_ESSENCE",1}}};oa_catalog c={reagents,2,&formula,1};oa_inventory inv={0},before,loaded={0};
 CHECK(argc==4);oa_registry_init(&s.registry);old=oa_object_create(&s.registry,524875,230417,237033,zero);CHECK(oa_object_resolve(&s.registry,old)!=NULL);CHECK(oa_workbench_in_reach(&s.registry,old,nearby,0));CHECK(!oa_workbench_in_reach(&s.registry,old,nearby,3.1415926f));CHECK(!oa_workbench_in_reach(&s.registry,old,far,0));CHECK(!oa_workbench_in_reach(&s.registry,old,nearby,NAN));CHECK(oa_object_remove(&s.registry,old));CHECK(!oa_object_resolve(&s.registry,old));newer=oa_object_create(&s.registry,524875,230417,237033,zero);CHECK(newer.slot==old.slot&&newer.generation!=old.generation);
 CHECK(!oa_can_craft(&c,&inv,&formula,error,sizeof(error)));CHECK(oa_inventory_set(&inv,201,1));CHECK(oa_inventory_set(&inv,101,2));CHECK(oa_inventory_set(&inv,102,1));before=inv;CHECK(!oa_craft(&c,&inv,&formula,error,sizeof(error)));CHECK(!memcmp(&inv,&before,sizeof(inv)));inv.alchemy_skill=10;CHECK(oa_can_craft(&c,&inv,&formula,error,sizeof(error)));CHECK(oa_craft(&c,&inv,&formula,error,sizeof(error)));CHECK(oa_inventory_count(&inv,301)==1);CHECK(oa_inventory_count(&inv,201)==1);CHECK(oa_inventory_count(&inv,101)==0&&oa_inventory_count(&inv,102)==0);before=inv;CHECK(!oa_craft(&c,&inv,&formula,error,sizeof(error)));CHECK(!memcmp(&inv,&before,sizeof(inv)));CHECK(!oa_inventory_set(&inv,0,2));CHECK(!oa_inventory_set(&inv,301,1000001));
 remove(argv[3]);CHECK(oa_inventory_save(&inv,argv[3],error,sizeof(error)));CHECK(oa_inventory_load(&loaded,argv[3],error,sizeof(error)));CHECK(loaded.alchemy_skill==10&&oa_inventory_count(&loaded,301)==1);before=loaded;f=fopen(argv[3],"r+b");CHECK(f!=NULL);CHECK(fputc('X',f)!=EOF);CHECK(!fclose(f));CHECK(!oa_inventory_load(&loaded,argv[3],error,sizeof(error)));CHECK(!memcmp(&before,&loaded,sizeof(loaded)));remove(argv[3]);
 config.runtime_dir=argv[1];config.memory_limit_bytes=64u*1024u*1024u;config.instruction_budget=1000000;r=amalur_runtime_create(&config,error,sizeof(error));if(!r)fprintf(stderr,"Runtime: %s\n",error);CHECK(r!=NULL);
 s.workbench=newer;s.player=oa_object_create(&s.registry,0,0,0,zero);s.selected=s.workbench;
 f=fopen(argv[2],"rb");CHECK(f!=NULL);CHECK(!fseek(f,0,SEEK_END));len=ftell(f);CHECK(len>0&&len<1024*1024);rewind(f);source=(char*)malloc((size_t)len);CHECK(source!=NULL);CHECK(fread(source,1,(size_t)len,f)==(size_t)len);CHECK(!fclose(f));CHECK(!oa_lua_install(r,&s,source,(size_t)len,error,sizeof(error)));free(source);
 CHECK(!oa_lua_interact(r,&s,error,sizeof(error)));CHECK(s.window_open==1);s.window_open=0;s.selected=s.player;CHECK(oa_lua_interact(r,&s,error,sizeof(error))!=0);CHECK(s.window_open==0);s.selected=s.workbench;
 CHECK(!amalur_runtime_eval_source(r,"return __opem_workbench_object:source_id()",strlen("return __opem_workbench_object:source_id()"),"source-id-test",&n,error,sizeof(error)));CHECK(n==1&&lua_tonumber(amalur_runtime_state(r),1)==524875);
 CHECK(oa_object_remove(&s.registry,s.workbench));CHECK(amalur_runtime_eval_source(r,"return __opem_workbench_object:source_id()",strlen("return __opem_workbench_object:source_id()"),"stale-handle-test",&n,error,sizeof(error))!=0);CHECK(strstr(error,"expired")!=NULL);CHECK(oa_lua_interact(r,&s,error,sizeof(error))!=0);
 amalur_runtime_destroy(r);printf("{\"ok\":true,\"checks\":%u,\"original_Workbench_callback_executed\":true,\"fixture_crafting_only\":true,\"native_gameplay_parity_claim\":false}\n",checks);return 0;
}
