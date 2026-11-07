#include "oa_creation.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>
static unsigned checks,failed;
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"FAIL line%u: %s\n",(unsigned)__LINE__,#x);failed++;}}while(0)
#define OK(x) CHECK((x)==OA_CREATION_OK)
static uint32_t crc(const unsigned char *p,size_t n){uint32_t c=UINT32_MAX;size_t i;unsigned j;for(i=0;i<n;i++){c^=p[i];for(j=0;j<8;j++)c=(c>>1)^(UINT32_C(0xedb88320)&(0u-(c&1u)));}return ~c;}
static void put32(unsigned char*p,uint32_t x){unsigned i;for(i=0;i<4;i++)p[i]=(unsigned char)(x>>(i*8));}
static void reseal(unsigned char*p,size_t n){put32(p+16,crc(p+32,n-32));}
static void unchanged(const oa_creation_state *a,const oa_creation_state *b){CHECK(memcmp(a,b,sizeof(*a))==0);}
static void roundtrip(const oa_creation_state *s){
 unsigned char a[OA_CREATION_ENVELOPE_MAX],b[OA_CREATION_ENVELOPE_MAX];size_t an=0,bn=0;oa_creation_state t;
 OK(oa_creation_serialize(s,a,sizeof a,&an));CHECK(an==oa_creation_serialized_size(s));OK(oa_creation_deserialize(&t,a,an));OK(oa_creation_validate(&t));OK(oa_creation_serialize(&t,b,sizeof b,&bn));CHECK(an==bn&&!memcmp(a,b,an));
}
static int bad_preset(unsigned r,unsigned s,unsigned p){return(r==0&&s==1&&p==5)||(r==1&&s==0&&p==5)||(r==1&&s==1&&p==5)||(r==2&&s==0&&p==2)||(r==3&&s==1&&p==4);}
static void source_cases(void){
 unsigned r,s,p,good=0,bad=0;oa_creation_state state,before;oa_creation_render_selection render;
 CHECK(oa_creation_source(4,0)==0);CHECK(oa_creation_source(0,2)==0);CHECK(oa_creation_source_preset(0,0,0)==0);CHECK(oa_creation_source_preset(0,0,6)==0);
 for(r=0;r<4;r++)for(s=0;s<2;s++){
  const oa_creation_source_type *type=oa_creation_source(r,s);CHECK(type!=0);OK(oa_creation_begin(&state,r,s));CHECK(!strcmp(state.name,type->default_name));OK(oa_creation_render(&state,&render));
  CHECK(render.player_simtype==(r<2?(s?669806u:669805u):(s?669808u:669807u)));CHECK(render.rig_fab==(s?611642u:456813u));CHECK(render.head_simtype==type->defaults.assets[0]);CHECK(render.hair_simtype==type->defaults.assets[1]);CHECK(render.head_diffuse_id!=0&&render.body_diffuse_id!=0);
  CHECK((render.warnings&OA_CREATION_VISUALS_NOT_IMPLEMENTED)!=0);CHECK(!!(render.warnings&OA_CREATION_FEMALE_ANIMATION_UNVERIFIED)==!!s);roundtrip(&state);
  for(p=0;p<6;p++){const oa_creation_patron *pat=oa_creation_source_patron(r,p);CHECK(pat&&pat->buff_id);OK(oa_creation_select_patron_id(&state,pat->buff_id));CHECK(state.patron==p);}
  CHECK(oa_creation_source_patron(r,5)->buff_id==1697849u);
  for(p=1;p<=5;p++){
   const oa_creation_appearance *raw=oa_creation_source_preset(r,s,p);CHECK(raw!=0);before=state;
   if(bad_preset(r,s,p)){CHECK(oa_creation_apply_preset(&state,p)==OA_CREATION_SOURCE_PRESET_UNRESOLVED);unchanged(&state,&before);bad++;}
   else{OK(oa_creation_apply_preset(&state,p));CHECK(state.preset==p&&!state.customized);OK(oa_creation_validate(&state));roundtrip(&state);good++;}
  }
 }
 CHECK(good==35&&bad==5);
 OK(oa_creation_begin(&state,0,0));OK(oa_creation_render(&state,&render));CHECK(render.head_simtype==1304307u&&render.hair_simtype==1388827u);CHECK(render.head_diffuse_id==1290637u&&render.body_diffuse_id==1290634u);CHECK(render.colors[OA_CREATION_HAIR_COLOR].words[1]!=render.colors[OA_CREATION_HAIR_COLOR].words[2]);
 OK(oa_creation_begin(&state,1,0));OK(oa_creation_render(&state,&render));CHECK(render.head_simtype==1304403u&&render.head_diffuse_id==1430980u);
 OK(oa_creation_begin(&state,2,0));CHECK(oa_creation_select_patron_id(&state,1254092u)==OA_CREATION_SELECTION);
 OK(oa_creation_begin(&state,0,0));before=state;
 CHECK(oa_creation_select_asset(&state,OA_CREATION_HEAD,1304403u)==OA_CREATION_SELECTION);unchanged(&state,&before);
 CHECK(oa_creation_select_asset(&state,6,1)==OA_CREATION_SELECTION);CHECK(oa_creation_select_color(&state,8,1)==OA_CREATION_SELECTION);CHECK(oa_creation_select_color(&state,0,0)==OA_CREATION_SELECTION);CHECK(oa_creation_select_alpha(&state,0,256)==OA_CREATION_SELECTION);
 OK(oa_creation_select_asset(&state,OA_CREATION_HEAD,1304352u));CHECK(state.customized);OK(oa_creation_select_color(&state,OA_CREATION_SKIN,1));OK(oa_creation_select_alpha(&state,OA_CREATION_TATTOO_ALPHA,0));roundtrip(&state);
}
static void names_and_selection(void){
 oa_creation_state s,before;unsigned char emoji[64];unsigned i;
 for(i=0;i<16;i++){emoji[i*4]=(unsigned char)0xf0;emoji[i*4+1]=(unsigned char)0x9f;emoji[i*4+2]=(unsigned char)0x98;emoji[i*4+3]=(unsigned char)0x80;}
 OK(oa_creation_begin(&s,0,0));CHECK(!strcmp(s.name,"Elrid"));OK(oa_creation_select_type(&s,1,1));CHECK(!strcmp(s.name,"Isolda"));OK(oa_creation_set_name(&s,"Custom",6));OK(oa_creation_select_type(&s,0,0));CHECK(!strcmp(s.name,"Custom"));CHECK(s.patron==0&&!s.name_is_default);
 OK(oa_creation_set_name(&s,(const char*)emoji,sizeof emoji));roundtrip(&s);before=s;
 CHECK(oa_creation_set_name(&s,"12345678901234567",17)==OA_CREATION_NAME);
 CHECK(oa_creation_set_name(&s,"",0)==OA_CREATION_NAME);
 CHECK(oa_creation_set_name(&s,"\xc0\xaf",2)==OA_CREATION_NAME);
 CHECK(oa_creation_set_name(&s,"\xed\xa0\x80",3)==OA_CREATION_NAME);
 CHECK(oa_creation_set_name(&s,"\xf4\x90\x80\x80",4)==OA_CREATION_NAME);
 CHECK(oa_creation_set_name(&s,"\xf0\x9f",2)==OA_CREATION_NAME);
 CHECK(oa_creation_set_name(&s,"A\0B",3)==OA_CREATION_NAME);
 CHECK(oa_creation_set_name(&s,"A\n",2)==OA_CREATION_NAME);unchanged(&s,&before);
}
static void transactions(void){
 oa_creation_state s,loaded,before;oa_creation_commit c,c2;unsigned char buf[192];size_t n;unsigned i;const uint64_t token=UINT64_C(0xfedcba9876543210);
 OK(oa_creation_begin(&s,0,0));OK(oa_creation_select_patron_id(&s,1697849u));before=s;
 CHECK(oa_creation_finalize(&s,0,&c)==OA_CREATION_ARGUMENT);unchanged(&s,&before);
 OK(oa_creation_finalize(&s,token,&c));CHECK(s.phase==OA_CREATION_PENDING);CHECK(c.transaction==token&&c.profile.phase==OA_CREATION_PENDING);CHECK(c.skill_delta_raw[0]==10&&c.skill_delta_raw[1]==20&&c.skill_delta_raw[6]==10);CHECK(c.patron_buff_id==1697849u&&c.patron_duration==-1&&c.patron_caster_tag==1731073u&&c.restore_health_to_max==1);
 before=s;CHECK(oa_creation_select_color(&s,0,1)==OA_CREATION_LOCKED);unchanged(&s,&before);
 OK(oa_creation_finalize(&s,token,&c2));CHECK(c2.transaction==c.transaction&&c2.revision==c.revision&&!memcmp(c2.skill_delta_raw,c.skill_delta_raw,sizeof c.skill_delta_raw));
 CHECK(oa_creation_finalize(&s,token-1,&c2)==OA_CREATION_TRANSACTION);CHECK(c2.patron_buff_id==0);
 OK(oa_creation_serialize(&s,buf,sizeof buf,&n));OK(oa_creation_deserialize(&loaded,buf,n));OK(oa_creation_finalize(&loaded,token,&c2));
 CHECK(oa_creation_acknowledge(&s,token-1)==OA_CREATION_TRANSACTION);OK(oa_creation_acknowledge(&s,token));CHECK(s.phase==OA_CREATION_COMMITTED);roundtrip(&s);
 CHECK(oa_creation_acknowledge(&s,token)==OA_CREATION_ALREADY_COMMITTED);CHECK(oa_creation_finalize(&s,token,&c2)==OA_CREATION_ALREADY_COMMITTED);CHECK(c2.patron_buff_id==0);for(i=0;i<9;i++)CHECK(c2.skill_delta_raw[i]==0);
 CHECK(oa_creation_cancel_pending(&s,token)==OA_CREATION_TRANSACTION);CHECK(oa_creation_select_patron(&s,0)==OA_CREATION_LOCKED);
 OK(oa_creation_cancel_pending(&loaded,token));CHECK(loaded.phase==OA_CREATION_DRAFT&&!loaded.transaction);CHECK(oa_creation_acknowledge(&loaded,token)==OA_CREATION_TRANSACTION);OK(oa_creation_finalize(&loaded,token-1,&c2));OK(oa_creation_acknowledge(&loaded,token-1));
 OK(oa_creation_serialize(&s,buf,sizeof buf,&n));OK(oa_creation_deserialize(&loaded,buf,n));CHECK(oa_creation_finalize(&loaded,token,&c2)==OA_CREATION_ALREADY_COMMITTED);
}
static void envelopes(void){
 oa_creation_state s,out,before;unsigned char good[192],bad[193],sentinel[192];size_t n,i,need;
 OK(oa_creation_begin(&s,0,0));OK(oa_creation_set_name(&s,"Tester",6));OK(oa_creation_serialize(&s,good,sizeof good,&n));CHECK(n==103);
 memset(sentinel,0xa5,sizeof sentinel);CHECK(oa_creation_serialize(&s,sentinel,n-1,&need)==OA_CREATION_CAPACITY);CHECK(need==n);for(i=0;i<sizeof sentinel;i++)CHECK(sentinel[i]==0xa5);
 CHECK(oa_creation_serialize(&s,0,192,&need)==OA_CREATION_ARGUMENT);
 OK(oa_creation_begin(&out,1,1));before=out;
 for(i=0;i<n;i++){memcpy(bad,good,n);bad[i]^=1;CHECK(oa_creation_deserialize(&out,bad,n)!=OA_CREATION_OK);unchanged(&out,&before);}
 for(i=0;i<n;i++){CHECK(oa_creation_deserialize(&out,good,i)!=OA_CREATION_OK);unchanged(&out,&before);}
 memcpy(bad,good,n);bad[n]=0;CHECK(oa_creation_deserialize(&out,bad,n+1)==OA_CREATION_CORRUPT);
 memcpy(bad,good,n);put32(bad+8,2);CHECK(oa_creation_deserialize(&out,bad,n)==OA_CREATION_VERSION);
 memcpy(bad,good,n);put32(bad+20,0);CHECK(oa_creation_deserialize(&out,bad,n)==OA_CREATION_CATALOGUE);
 memcpy(bad,good,n);bad[32]=99;reseal(bad,n);CHECK(oa_creation_deserialize(&out,bad,n)==OA_CREATION_INVALID_STATE);
 memcpy(bad,good,n);put32(bad+45,0xdeadbeefu);reseal(bad,n);CHECK(oa_creation_deserialize(&out,bad,n)==OA_CREATION_SELECTION);
 memcpy(bad,good,n);bad[36]=OA_CREATION_COMMITTED;reseal(bad,n);CHECK(oa_creation_deserialize(&out,bad,n)==OA_CREATION_INVALID_STATE);
 memcpy(bad,good,n);bad[97]=0;reseal(bad,n);CHECK(oa_creation_deserialize(&out,bad,n)==OA_CREATION_CORRUPT);
 memcpy(bad,good,n);bad[97]=0xc0;reseal(bad,n);CHECK(oa_creation_deserialize(&out,bad,n)==OA_CREATION_NAME);unchanged(&out,&before);
}
int main(void){source_cases();names_and_selection();transactions();envelopes();printf("{\"checks\":%u,\"failed\":%u,\"source_types\":8,\"source_presets\":40,\"unresolved_presets\":5,\"file_io\":false,\"gpu_test\":false}\n",checks,failed);return failed?1:0;}
