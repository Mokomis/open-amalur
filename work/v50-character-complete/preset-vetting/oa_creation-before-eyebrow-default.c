#include "oa_creation.h"
#include "oa_creation_source_tables.h"
#include <string.h>
#define GUARD UINT32_C(0x4f414352)
#define ENVELOPE_VERSION 1u
#define HEADER_SIZE 32u
#define PAYLOAD_FIXED 65u
static unsigned type_index(unsigned race,unsigned sex){return race*2u+sex;}
static size_t bounded_name(const char *s){size_t n;for(n=0;n<=OA_CREATION_NAME_BYTES;n++)if(!s[n])return n;return OA_CREATION_NAME_BYTES+1u;}
static int utf8_name(const char *p,size_t n){
 size_t i=0;unsigned count=0;
 if(!p||!n||n>OA_CREATION_NAME_BYTES)return 0;
 while(i<n){uint32_t cp,min;unsigned need,j;unsigned char b=(unsigned char)p[i++];
  if(b<0x80){cp=b;need=0;min=0;}
  else if(b>=0xc2&&b<=0xdf){cp=b&31u;need=1;min=0x80;}
  else if(b>=0xe0&&b<=0xef){cp=b&15u;need=2;min=0x800;}
  else if(b>=0xf0&&b<=0xf4){cp=b&7u;need=3;min=0x10000;}
  else return 0;
  if(need>n-i)return 0;
  for(j=0;j<need;j++){unsigned char x=(unsigned char)p[i++];if((x&0xc0)!=0x80)return 0;cp=(cp<<6)|(x&63u);}
  if(cp<min||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff)||cp<32||cp==127)return 0;
  if(++count>OA_CREATION_NAME_SCALARS)return 0;
 }
 return 1;
}
static int appearance_equal(const oa_creation_appearance *a,const oa_creation_appearance *b){
 unsigned i;for(i=0;i<OA_CREATION_ASSETS;i++)if(a->assets[i]!=b->assets[i])return 0;
 for(i=0;i<OA_CREATION_COLORS;i++)if(a->colors[i]!=b->colors[i])return 0;
 for(i=0;i<OA_CREATION_ALPHAS;i++)if(a->alphas[i]!=b->alphas[i])return 0;return 1;
}
const char *oa_creation_result_string(oa_creation_result r){
 static const char *const text[]={"ok","invalid argument","invalid state","invalid source selection","invalid name","profile locked","source preset has unresolved selection","transaction mismatch","already committed","insufficient capacity","corrupt envelope","unsupported envelope version","source catalogue mismatch"};
 return (unsigned)r<sizeof(text)/sizeof(text[0])?text[r]:"unknown result";
}
const oa_creation_source_type *oa_creation_source(unsigned race,unsigned sex){
 return race<4&&sex<2?oa_creation_types_data+type_index(race,sex):0;
}
const oa_creation_patron *oa_creation_source_patron(unsigned race,unsigned patron){
 return race<4&&patron<6?oa_creation_patrons_data[race]+patron:0;
}
const oa_creation_appearance *oa_creation_source_preset(unsigned race,unsigned sex,unsigned preset){
 return race<4&&sex<2&&preset>=1&&preset<=5?oa_creation_presets_data[type_index(race,sex)]+preset-1:0;
}
size_t oa_creation_color_count(unsigned race,unsigned sex,unsigned channel){
 return race<4&&sex<2&&channel<8?oa_creation_colors_data[type_index(race,sex)][channel].count:0;
}
const oa_creation_color_record *oa_creation_source_color(unsigned race,unsigned sex,unsigned channel,unsigned index){
 const oa_creation_color_view *v;if(race>=4||sex>=2||channel>=8||!index)return 0;
 v=&oa_creation_colors_data[type_index(race,sex)][channel];return index<=v->count?v->records+index-1:0;
}
int oa_creation_asset_supported(unsigned race,unsigned sex,unsigned cat,uint32_t id){
 const oa_creation_source_type *t=oa_creation_source(race,sex);size_t i;
 if(!t||cat>=6)return 0;
 /* Zero ears is explicitly UNSPECIFIED, not a claim that a native "none" item exists. */
 if(!id)return cat==OA_CREATION_EARS||(cat==OA_CREATION_BEARD&&sex==OA_CREATION_FEMALE);
 for(i=0;i<oa_creation_assets_count;i++){const oa_creation_asset_row *a=oa_creation_assets_data+i;
  if(a->id==id&&a->category==oa_creation_category_hashes[cat]&&(a->race_mask&t->race_mask)&&(a->sex_mask&t->sex_mask))return 1;
 }return 0;
}
uint32_t oa_creation_catalogue_crc(void){return OA_CREATION_SOURCE_CRC;}
const int16_t *oa_creation_source_skills(unsigned race){return race<4?oa_creation_skills_data[race]:0;}
int oa_creation_asset_option(unsigned race,unsigned sex,unsigned cat,size_t index,uint32_t *id){
 const oa_creation_source_type *t=oa_creation_source(race,sex);size_t i,count=0;
 if(!t||cat>=6||!id)return 0;
 if(cat==OA_CREATION_EARS||(cat==OA_CREATION_BEARD&&sex==OA_CREATION_FEMALE)){if(index==0){*id=0;return 1;}count++;}
 for(i=0;i<oa_creation_assets_count;i++){const oa_creation_asset_row *a=oa_creation_assets_data+i;
  if(a->category==oa_creation_category_hashes[cat]&&(a->race_mask&t->race_mask)&&(a->sex_mask&t->sex_mask)){if(count++==index){*id=a->id;return 1;}}
 }return 0;
}
size_t oa_creation_asset_option_count(unsigned race,unsigned sex,unsigned cat){
 const oa_creation_source_type *t=oa_creation_source(race,sex);size_t i,count=0;if(!t||cat>=6)return 0;
 if(cat==OA_CREATION_EARS||(cat==OA_CREATION_BEARD&&sex==OA_CREATION_FEMALE))count++;
 for(i=0;i<oa_creation_assets_count;i++){const oa_creation_asset_row *a=oa_creation_assets_data+i;
  if(a->category==oa_creation_category_hashes[cat]&&(a->race_mask&t->race_mask)&&(a->sex_mask&t->sex_mask))count++;
 }return count;
}
/* Original character_gen_manager0/15 changes only admitted option entries.
   Invalid authored indices retain the current selection; alpha list is0,5,...255.
   Ears is do_not_display and EyebrowAlpha has no m_gen_options row. Raw tables
   remain immutable; effective preset state can depend on the previous selection. */
static void preset_effective(const oa_creation_state *s,const oa_creation_appearance *p,oa_creation_appearance *out){
 unsigned i;*out=s->appearance;
 for(i=0;i<6;i++)if(i!=OA_CREATION_EARS&&p->assets[i]&&oa_creation_asset_supported(s->race,s->sex,i,p->assets[i]))out->assets[i]=p->assets[i];
 for(i=0;i<8;i++){size_t n=oa_creation_color_count(s->race,s->sex,i);if(p->colors[i]&&p->colors[i]<=n)out->colors[i]=p->colors[i];}
 for(i=0;i<4;i++)if(i!=1&&p->alphas[i]%5u==0)out->alphas[i]=p->alphas[i];
}
static int preset_matches(const oa_creation_state *s,const oa_creation_appearance *p){
 oa_creation_appearance effective;preset_effective(s,p,&effective);return appearance_equal(&effective,&s->appearance);
}
static oa_creation_result appearance_valid(const oa_creation_state *s){
 unsigned i;
 for(i=0;i<6;i++)if(!oa_creation_asset_supported(s->race,s->sex,i,s->appearance.assets[i]))return OA_CREATION_SELECTION;
 for(i=0;i<8;i++){size_t n=oa_creation_color_count(s->race,s->sex,i);unsigned v=s->appearance.colors[i];
  if((n&&(!v||v>n))||(!n&&v))return OA_CREATION_SELECTION;
 }return OA_CREATION_OK;
}
oa_creation_result oa_creation_validate(const oa_creation_state *s){
 const oa_creation_source_type *t;const oa_creation_appearance *p;size_t n;oa_creation_result r;
 if(!s)return OA_CREATION_ARGUMENT;
 if(s->guard!=GUARD||!s->revision||s->race>=4||s->sex>=2||s->preset>5||s->patron>=6||s->phase>2||s->customized>1||s->name_is_default>1)return OA_CREATION_INVALID_STATE;
 if((s->phase==OA_CREATION_DRAFT&&s->transaction)||(s->phase!=OA_CREATION_DRAFT&&!s->transaction))return OA_CREATION_INVALID_STATE;
 n=bounded_name(s->name);if(!utf8_name(s->name,n))return OA_CREATION_NAME;
 t=oa_creation_source(s->race,s->sex);
 if(s->name_is_default&&strcmp(s->name,t->default_name))return OA_CREATION_INVALID_STATE;
 r=appearance_valid(s);if(r)return r;
 if(!s->customized){p=s->preset?oa_creation_source_preset(s->race,s->sex,s->preset):&t->defaults;
  if(s->preset?!preset_matches(s,p):!appearance_equal(&s->appearance,p))return OA_CREATION_INVALID_STATE;
 }return OA_CREATION_OK;
}
static oa_creation_result mutable_state(const oa_creation_state *s){
 oa_creation_result r=oa_creation_validate(s);if(r)return r;
 if(s->phase!=OA_CREATION_DRAFT)return OA_CREATION_LOCKED;
 return s->revision==UINT32_MAX?OA_CREATION_INVALID_STATE:OA_CREATION_OK;
}
oa_creation_result oa_creation_begin(oa_creation_state *s,unsigned race,unsigned sex){
 const oa_creation_source_type *t=oa_creation_source(race,sex);oa_creation_state n;
 if(!s||!t)return OA_CREATION_ARGUMENT;
 memset(&n,0,sizeof n);n.guard=GUARD;n.revision=1;n.race=(uint8_t)race;n.sex=(uint8_t)sex;n.appearance=t->defaults;
 n.name_is_default=1;memcpy(n.name,t->default_name,strlen(t->default_name)+1);
 if(oa_creation_validate(&n))return OA_CREATION_INVALID_STATE;*s=n;return OA_CREATION_OK;
}
oa_creation_result oa_creation_select_type(oa_creation_state *s,unsigned race,unsigned sex){
 oa_creation_result r=mutable_state(s);oa_creation_state n;if(r)return r;
 r=oa_creation_begin(&n,race,sex);if(r)return r;n.revision=s->revision+1;
 if(!s->name_is_default){memcpy(n.name,s->name,sizeof n.name);n.name_is_default=0;}
 /* Patron index resets to the new race's first valid patron; no illegal carry-over. */
 *s=n;return OA_CREATION_OK;
}
oa_creation_result oa_creation_select_patron(oa_creation_state *s,unsigned patron){
 oa_creation_result r=mutable_state(s);if(r)return r;if(patron>=6)return OA_CREATION_SELECTION;
 s->patron=(uint8_t)patron;s->revision++;return OA_CREATION_OK;
}
oa_creation_result oa_creation_select_patron_id(oa_creation_state *s,uint32_t buff){
 unsigned i;oa_creation_result r=mutable_state(s);if(r)return r;
 for(i=0;i<6;i++)if(oa_creation_patrons_data[s->race][i].buff_id==buff)return oa_creation_select_patron(s,i);
 return OA_CREATION_SELECTION;
}
oa_creation_result oa_creation_apply_preset(oa_creation_state *s,unsigned preset){
 const oa_creation_appearance *p;oa_creation_state n;oa_creation_result r=mutable_state(s);if(r)return r;
 p=oa_creation_source_preset(s->race,s->sex,preset);if(!p)return OA_CREATION_SELECTION;
 n=*s;preset_effective(s,p,&n.appearance);n.preset=(uint8_t)preset;n.customized=0;n.revision++;
 if(appearance_valid(&n))return OA_CREATION_INVALID_STATE;
 *s=n;return OA_CREATION_OK;
}
oa_creation_result oa_creation_select_asset(oa_creation_state *s,unsigned cat,uint32_t id){
 oa_creation_result r=mutable_state(s);if(r)return r;
 if(!oa_creation_asset_supported(s->race,s->sex,cat,id))return OA_CREATION_SELECTION;
 s->appearance.assets[cat]=id;s->customized=1;s->revision++;return OA_CREATION_OK;
}
oa_creation_result oa_creation_select_color(oa_creation_state *s,unsigned channel,unsigned index){
 oa_creation_result r=mutable_state(s);size_t n;if(r)return r;if(channel>=8)return OA_CREATION_SELECTION;
 n=oa_creation_color_count(s->race,s->sex,channel);if((n&&(!index||index>n))||(!n&&index))return OA_CREATION_SELECTION;
 s->appearance.colors[channel]=(uint16_t)index;s->customized=1;s->revision++;return OA_CREATION_OK;
}
oa_creation_result oa_creation_select_alpha(oa_creation_state *s,unsigned channel,unsigned value){
 oa_creation_result r=mutable_state(s);if(r)return r;if(channel>=4||value>255)return OA_CREATION_SELECTION;
 s->appearance.alphas[channel]=(uint8_t)value;s->customized=1;s->revision++;return OA_CREATION_OK;
}
oa_creation_result oa_creation_set_name(oa_creation_state *s,const char *p,size_t n){
 oa_creation_result r=mutable_state(s);if(r)return r;if(!utf8_name(p,n))return OA_CREATION_NAME;
 memmove(s->name,p,n);s->name[n]=0;s->name_is_default=0;s->revision++;return OA_CREATION_OK;
}
oa_creation_result oa_creation_render(const oa_creation_state *s,oa_creation_render_selection *out){
 const oa_creation_source_type *t;unsigned i;oa_creation_result r=oa_creation_validate(s);if(r)return r;if(!out)return OA_CREATION_ARGUMENT;
 memset(out,0,sizeof(*out));t=oa_creation_source(s->race,s->sex);out->player_simtype=t->player_simtype;out->creator_simtype=t->creator_simtype;out->rig_fab=t->rig_fab;
 out->head_simtype=s->appearance.assets[0];out->hair_simtype=s->appearance.assets[1];out->beard_simtype=s->appearance.assets[2];out->ears_simtype=s->appearance.assets[3];out->tattoo_simtype=s->appearance.assets[4];out->accessory_simtype=s->appearance.assets[5];
 for(i=0;i<8;i++){const oa_creation_color_record *c=oa_creation_source_color(s->race,s->sex,i,s->appearance.colors[i]);if(c){out->colors[i]=*c;out->present_color_mask|=1u<<i;}}
 out->head_diffuse_id=out->colors[OA_CREATION_SKIN].words[3];out->body_diffuse_id=out->colors[OA_CREATION_SKIN].words[4];memcpy(out->alphas,s->appearance.alphas,4);
 out->warnings=OA_CREATION_VISUALS_NOT_IMPLEMENTED|OA_CREATION_ASSET_AVAILABILITY_UNVERIFIED|OA_CREATION_NATIVE_NAME_FILTER_UNVERIFIED;
 if(s->sex==OA_CREATION_FEMALE)out->warnings|=OA_CREATION_FEMALE_ANIMATION_UNVERIFIED;
 if(s->race>=OA_CREATION_LJOSALFAR&&!out->ears_simtype)out->warnings|=OA_CREATION_EARS_UNSPECIFIED;
 return OA_CREATION_OK;
}
oa_creation_result oa_creation_finalize(oa_creation_state *s,uint64_t token,oa_creation_commit *out){
 oa_creation_result r;if(out)memset(out,0,sizeof(*out));r=oa_creation_validate(s);if(r)return r;if(!out||!token)return OA_CREATION_ARGUMENT;
 if(s->phase==OA_CREATION_COMMITTED)return OA_CREATION_ALREADY_COMMITTED;
 if(s->phase==OA_CREATION_PENDING&&s->transaction!=token)return OA_CREATION_TRANSACTION;
 s->phase=OA_CREATION_PENDING;s->transaction=token;memset(out,0,sizeof(*out));out->transaction=token;out->revision=s->revision;out->profile=*s;
 memcpy(out->skill_delta_raw,oa_creation_skills_data[s->race],sizeof out->skill_delta_raw);
 out->patron_buff_id=oa_creation_patrons_data[s->race][s->patron].buff_id;out->patron_caster_tag=1731073u;out->patron_duration=-1;out->restore_health_to_max=1;return OA_CREATION_OK;
}
oa_creation_result oa_creation_acknowledge(oa_creation_state *s,uint64_t token){
 oa_creation_result r=oa_creation_validate(s);if(r)return r;if(!token||s->transaction!=token)return OA_CREATION_TRANSACTION;
 if(s->phase==OA_CREATION_COMMITTED)return OA_CREATION_ALREADY_COMMITTED;
 if(s->phase!=OA_CREATION_PENDING)return OA_CREATION_TRANSACTION;
 s->phase=OA_CREATION_COMMITTED;return OA_CREATION_OK;
}
oa_creation_result oa_creation_cancel_pending(oa_creation_state *s,uint64_t token){
 oa_creation_result r=oa_creation_validate(s);if(r)return r;
 if(s->phase!=OA_CREATION_PENDING||!token||s->transaction!=token)return OA_CREATION_TRANSACTION;
 if(s->revision==UINT32_MAX)return OA_CREATION_INVALID_STATE;
 s->phase=OA_CREATION_DRAFT;s->transaction=0;s->revision++;return OA_CREATION_OK;
}
static uint32_t crc32_bytes(const uint8_t *p,size_t n){
 uint32_t c=UINT32_MAX;size_t i;unsigned b;for(i=0;i<n;i++){c^=p[i];for(b=0;b<8;b++)c=(c>>1)^(UINT32_C(0xedb88320)&(0u-(c&1u)));}return ~c;
}
static void w16(uint8_t *p,uint16_t x){p[0]=(uint8_t)x;p[1]=(uint8_t)(x>>8);}
static void w32(uint8_t *p,uint32_t x){unsigned i;for(i=0;i<4;i++)p[i]=(uint8_t)(x>>(i*8));}
static void w64(uint8_t *p,uint64_t x){unsigned i;for(i=0;i<8;i++)p[i]=(uint8_t)(x>>(i*8));}
static uint16_t r16(const uint8_t *p){return(uint16_t)((uint16_t)p[0]|((uint16_t)p[1]<<8));}
static uint32_t r32(const uint8_t *p){return(uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static uint64_t r64(const uint8_t *p){return(uint64_t)r32(p)|((uint64_t)r32(p+4)<<32);}
size_t oa_creation_serialized_size(const oa_creation_state *s){return oa_creation_validate(s)?0:HEADER_SIZE+PAYLOAD_FIXED+bounded_name(s->name);}
oa_creation_result oa_creation_serialize(const oa_creation_state *s,void *buffer,size_t cap,size_t *written){
 uint8_t bytes[OA_CREATION_ENVELOPE_MAX];size_t n,name,at=HEADER_SIZE;unsigned i;oa_creation_result r=oa_creation_validate(s);
 if(written)*written=0;if(r)return r;n=oa_creation_serialized_size(s);if(written)*written=n;if(cap<n)return OA_CREATION_CAPACITY;if(!buffer)return OA_CREATION_ARGUMENT;
 memset(bytes,0,sizeof bytes);name=bounded_name(s->name);
 bytes[at++]=s->race;bytes[at++]=s->sex;bytes[at++]=s->preset;bytes[at++]=s->patron;bytes[at++]=s->phase;bytes[at++]=s->customized;bytes[at++]=s->name_is_default;
 for(i=0;i<4;i++)bytes[at++]=s->appearance.alphas[i];
 w16(bytes+at,(uint16_t)name);at+=2;
 for(i=0;i<6;i++){w32(bytes+at,s->appearance.assets[i]);at+=4;}
 for(i=0;i<8;i++){w16(bytes+at,s->appearance.colors[i]);at+=2;}
 w64(bytes+at,s->transaction);at+=8;w32(bytes+at,s->revision);at+=4;memcpy(bytes+at,s->name,name);at+=name;
 if(at!=n)return OA_CREATION_INVALID_STATE;
 memcpy(bytes,"OACREA1",8);w32(bytes+8,ENVELOPE_VERSION);w32(bytes+12,(uint32_t)(n-HEADER_SIZE));w32(bytes+16,crc32_bytes(bytes+HEADER_SIZE,n-HEADER_SIZE));w32(bytes+20,OA_CREATION_SOURCE_CRC);
 memcpy(buffer,bytes,n);return OA_CREATION_OK;
}
oa_creation_result oa_creation_deserialize(oa_creation_state *out,const void *buffer,size_t n){
 const uint8_t *p=(const uint8_t*)buffer;oa_creation_state s;uint32_t payload;size_t at=HEADER_SIZE,name;unsigned i;oa_creation_result r;
 if(!out||!p)return OA_CREATION_ARGUMENT;if(n<HEADER_SIZE||memcmp(p,"OACREA1",8))return OA_CREATION_CORRUPT;
 if(r32(p+8)!=ENVELOPE_VERSION)return OA_CREATION_VERSION;
 if(r32(p+20)!=OA_CREATION_SOURCE_CRC)return OA_CREATION_CATALOGUE;
 if(r32(p+24)||r32(p+28))return OA_CREATION_CORRUPT;
 payload=r32(p+12);if(payload<PAYLOAD_FIXED+1||payload>PAYLOAD_FIXED+OA_CREATION_NAME_BYTES||n!=HEADER_SIZE+(size_t)payload)return OA_CREATION_CORRUPT;
 if(r32(p+16)!=crc32_bytes(p+HEADER_SIZE,payload))return OA_CREATION_CORRUPT;
 memset(&s,0,sizeof s);s.guard=GUARD;s.race=p[at++];s.sex=p[at++];s.preset=p[at++];s.patron=p[at++];s.phase=p[at++];s.customized=p[at++];s.name_is_default=p[at++];
 for(i=0;i<4;i++)s.appearance.alphas[i]=p[at++];
 name=r16(p+at);at+=2;if(!name||name>OA_CREATION_NAME_BYTES||payload!=PAYLOAD_FIXED+name)return OA_CREATION_CORRUPT;
 for(i=0;i<6;i++){s.appearance.assets[i]=r32(p+at);at+=4;}
 for(i=0;i<8;i++){s.appearance.colors[i]=r16(p+at);at+=2;}
 s.transaction=r64(p+at);at+=8;s.revision=r32(p+at);at+=4;memcpy(s.name,p+at,name);s.name[name]=0;at+=name;
 /* Reject embedded NUL/trailing bytes even if an attacker recomputes the CRC. */
 if(at!=n||bounded_name(s.name)!=name)return OA_CREATION_CORRUPT;
 r=oa_creation_validate(&s);if(r)return r;*out=s;return OA_CREATION_OK;
}
