#define main oa_legacy_menu_checks
#include "../../v19-host/tests/oa_menu_test.c"
#undef main
#include "../../v19-host/oa_creation_draft.h"
static int same_profile(const oa_creation_state *a,const oa_creation_state *b){
 unsigned char x[OA_CREATION_ENVELOPE_MAX],y[OA_CREATION_ENVELOPE_MAX];size_t nx,ny;
 return !oa_creation_serialize(a,x,sizeof x,&nx)&&!oa_creation_serialize(b,y,sizeof y,&ny)&&nx==ny&&!memcmp(x,y,nx);
}
int main(int argc,char **argv){
 const char *dir=argc>1?argv[1]:".";int r=oa_legacy_menu_checks(argc,argv);oa_menu m;oa_creation_state before,loaded,temp;
 unsigned race,sex,cat;size_t n,j,k;uint32_t id,other;char bad[1200];unsigned char saved[OA_CREATION_ENVELOPE_MAX];size_t saved_n;FILE *f;AInputEvent e;
 if(r)return r;oa_menu_init(&m,dir,0);remove(m.creation_path);oa_menu_creation_enable(&m,1);frame(&m);CHECK(m.count==4);
 tap(&m,200,400);CHECK(m.screen==OA_SCREEN_CREATION&&m.creation.phase==OA_CREATION_DRAFT);frame(&m);CHECK(m.count==9);
 tap(&m,478,190);CHECK(m.creation.race==OA_CREATION_VARANI&&m.creation_dirty);
 tap(&m,478,250);CHECK(m.creation.sex==OA_CREATION_FEMALE);
 tap(&m,478,375);CHECK(m.creation.patron==1);before=m.creation;
 tap(&m,200,430);CHECK(m.screen==OA_SCREEN_CREATION_NAME);frame(&m);CHECK(m.count==43);
 /* Physical name input is consumed, never menu navigation or game movement. */
 for(j=0;j<16;j++)press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_DEL);
 CHECK(!m.creation_name[0]);press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_R);press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_A+14);press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_A+14);press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_A+10);
 CHECK(!strcmp(m.creation_name,"ROOK"));CHECK(m.creation.revision==before.revision);
 press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_ENTER);CHECK(m.screen==OA_SCREEN_CREATION&&!strcmp(m.creation.name,"ROOK"));
 tap(&m,200,735);CHECK(m.creation_saved&&!m.creation_dirty);CHECK(!oa_creation_draft_load(&loaded,m.creation_path));CHECK(same_profile(&loaded,&m.creation));
 /* Reopen reloads the saved draft without character/quest completion. */
 press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_ESCAPE);CHECK(m.screen==OA_SCREEN_TITLE);frame(&m);
 tap(&m,200,400);CHECK(m.screen==OA_SCREEN_CREATION&&!strcmp(m.creation.name,"ROOK")&&m.creation.phase==OA_CREATION_DRAFT&&m.creation.transaction==0);
 /* Each tab and control is live using the same menu input contract. */
 press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_R1);CHECK(m.creation_page==1);frame(&m);
 before=m.creation;tap(&m,478,190);CHECK(m.creation.revision>before.revision);CHECK(!oa_creation_validate(&m.creation));
 press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_R1);CHECK(m.creation_page==2);frame(&m);CHECK(m.count==12);
 tap(&m,478,190);CHECK(!oa_creation_validate(&m.creation));
 press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_R1);CHECK(m.creation_page==3);frame(&m);tap(&m,478,190);CHECK(m.creation.customized);
 press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_R1);CHECK(m.creation_page==4);frame(&m);CHECK(m.count==4);
 /* Full-body/face inspection is independent of the chosen profile. */
 m.creation_page=3;frame(&m);tap(&m,200,375);CHECK(m.creation_advanced);frame(&m);CHECK(m.count==10);
 before=m.creation;tap(&m,312,495);CHECK(m.creation.appearance.alphas[1]<before.appearance.alphas[1]);
 tap(&m,650,740);CHECK(m.creation_face);tap(&m,1050,740);CHECK(m.creation_zoom==1&&m.creation_angle==0);
 /* Empty name confirmation preserves the prior name, matching name_win0/2. */
 m.creation_page=0;frame(&m);tap(&m,200,430);m.creation_name[0]=0;before=m.creation;
 press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_ENTER);CHECK(m.screen==OA_SCREEN_CREATION);CHECK(!strcmp(m.creation.name,before.name));
 /* Controller name keyboard uses A to select a glyph, not raw letter input. */
 m.creation_page=0;frame(&m);tap(&m,200,430);frame(&m);m.focus=0;memset(m.creation_name,0,sizeof m.creation_name);
 press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_A);CHECK(!strcmp(m.creation_name,"A"));press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_B);CHECK(m.screen==OA_SCREEN_CREATION);
 /* Source option enumeration exposes only accepted IDs, including absent defaults. */
 for(race=0;race<4;race++)for(sex=0;sex<2;sex++){
  CHECK(!oa_creation_begin(&temp,race,sex));CHECK(oa_creation_source_skills(race)!=NULL);
  for(cat=0;cat<6;cat++){
   int found=0;n=oa_creation_asset_option_count(race,sex,cat);CHECK(n>0);
   for(j=0;j<n;j++){CHECK(oa_creation_asset_option(race,sex,cat,j,&id));CHECK(oa_creation_asset_supported(race,sex,cat,id));if(id==temp.appearance.assets[cat])found=1;
    for(k=0;k<j;k++){CHECK(oa_creation_asset_option(race,sex,cat,k,&other));CHECK(id!=other);}
   }CHECK(found);CHECK(!oa_creation_asset_option(race,sex,cat,n,&id));
  }
 }
 CHECK(!oa_creation_asset_option_count(4,0,0));CHECK(!oa_creation_source_skills(4));
 /* A failed save never mutates the in-memory candidate or the existing draft. */
 before=m.creation;snprintf(bad,sizeof bad,"%s/missing-directory/draft.bin",dir);
 CHECK(oa_creation_draft_save(&m.creation,bad));CHECK(!memcmp(&m.creation,&before,sizeof before));CHECK(!oa_creation_draft_load(&loaded,m.creation_path));CHECK(!strcmp(loaded.name,"ROOK"));
 CHECK(!oa_creation_serialize(&loaded,saved,sizeof saved,&saved_n));
 temp=loaded;{oa_creation_commit candidate;CHECK(!oa_creation_finalize(&temp,123,&candidate));CHECK(oa_creation_draft_save(&temp,m.creation_path));}
 CHECK(!oa_creation_draft_load(&temp,m.creation_path));CHECK(same_profile(&temp,&loaded));
 /* Corrupt loads are atomic and preserve the caller's prior state. */
 f=fopen(m.creation_path,"wb");CHECK(f!=NULL);saved[saved_n-1]^=1;CHECK(fwrite(saved,1,saved_n,f)==saved_n);CHECK(!fclose(f));before=m.creation;
 CHECK(oa_creation_draft_load(&m.creation,m.creation_path));CHECK(!memcmp(&before,&m.creation,sizeof before));
 remove(m.creation_path);remove(m.settings_path);remove(m.save_path);
 e=key(OPEM_INPUT_KEYBOARD,AKEYCODE_ESCAPE,AKEY_EVENT_ACTION_DOWN);(void)e;
 printf("creator UI and legacy menu checks=%u failures=0\n",checks);return 0;
}
