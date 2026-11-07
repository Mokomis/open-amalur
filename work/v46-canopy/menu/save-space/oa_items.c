#include "oa_items.h"
#include "oa_ui.h"
#include <string.h>
static const oa_item_def ITEMS[OA_ITEM_COUNT]={
 {"Iron Longsword","Longsword",OA_SLOT_WEAPON,OA_SPR_I_IRON,14,120,OA_RARITY_COMMON,0,1},
 {"Steel Longsword","Longsword",OA_SLOT_WEAPON,OA_SPR_I_STEEL,22,320,OA_RARITY_COMMON,0,0},
 {"Azurite Longsword","Longsword",OA_SLOT_WEAPON,OA_SPR_I_AZURITE,30,780,OA_RARITY_UNCOMMON,0,2},
 {"Sylvanite Longsword","Longsword",OA_SLOT_WEAPON,OA_SPR_I_SYLVANITE,38,1650,OA_RARITY_RARE,0,3},
 {"Prismere Longsword","Longsword",OA_SLOT_WEAPON,OA_SPR_I_PRISMERE,48,3100,OA_RARITY_EPIC,0,4},
 {"Vigilant Helm","Helm",OA_SLOT_HEAD,OA_SPR_I_HELM,12,260,OA_RARITY_COMMON,0,-1},
 {"Tuatha Helm","Helm",OA_SLOT_HEAD,OA_SPR_I_HELM2,20,720,OA_RARITY_UNCOMMON,0,-1},
 {"Vigilant Cuirass","Cuirass",OA_SLOT_TORSO,OA_SPR_I_CUIRASS,30,540,OA_RARITY_COMMON,0,-1},
 {"Elite Tuatha Cuirass","Cuirass",OA_SLOT_TORSO,OA_SPR_I_CUIRASS2,46,1900,OA_RARITY_RARE,0,-1},
 {"Vigilant Gauntlets","Gauntlets",OA_SLOT_HANDS,OA_SPR_I_GAUNT,9,210,OA_RARITY_COMMON,0,-1},
 {"Battle Gauntlets","Gauntlets",OA_SLOT_HANDS,OA_SPR_I_GAUNT2,15,600,OA_RARITY_UNCOMMON,0,-1},
 {"Vigilant Greaves","Greaves",OA_SLOT_LEGS,OA_SPR_I_LEGS,14,300,OA_RARITY_COMMON,0,-1},
 {"Dauntless Greaves","Greaves",OA_SLOT_LEGS,OA_SPR_I_LEGS2,24,980,OA_RARITY_RARE,0,-1},
 {"Silentstep Boots","Boots",OA_SLOT_FEET,OA_SPR_I_BOOTS,8,240,OA_RARITY_COMMON,0,-1},
 {"Boots of the Zodiac","Boots",OA_SLOT_FEET,OA_SPR_I_BOOTS2,16,1200,OA_RARITY_EPIC,0,-1},
 {"Minor Healing Potion","Potion",OA_SLOT_NONE,OA_SPR_I_POTION,0,25,OA_RARITY_COMMON,25,-1},
 {"Greater Healing Potion","Potion",OA_SLOT_NONE,OA_SPR_I_POTION2,0,60,OA_RARITY_UNCOMMON,50,-1},
 {"Master Healing Potion","Potion",OA_SLOT_NONE,OA_SPR_I_POTION3,0,140,OA_RARITY_RARE,100,-1}};
const oa_item_def *oa_item_get(int i){return i>=0&&i<OA_ITEM_COUNT?ITEMS+i:NULL;}
void oa_bag_new(oa_bag *b){int i;memset(b,0,sizeof(*b));for(i=0;i<OA_SLOT_COUNT;i++)b->equipped[i]=-1;
 b->count[OA_ITEM_STEEL]=1;b->count[OA_ITEM_IRON]=1;b->count[OA_ITEM_VIGILANT_CUIRASS]=1;b->count[OA_ITEM_VIGILANT_GAUNTLETS]=1;b->count[OA_ITEM_VIGILANT_GREAVES]=1;b->count[OA_ITEM_SILENTSTEP_BOOTS]=1;b->count[OA_ITEM_MINOR_POTION]=3;b->gold=50;
 b->equipped[OA_SLOT_WEAPON]=OA_ITEM_STEEL;b->equipped[OA_SLOT_TORSO]=OA_ITEM_VIGILANT_CUIRASS;b->equipped[OA_SLOT_HANDS]=OA_ITEM_VIGILANT_GAUNTLETS;b->equipped[OA_SLOT_LEGS]=OA_ITEM_VIGILANT_GREAVES;b->equipped[OA_SLOT_FEET]=OA_ITEM_SILENTSTEP_BOOTS;}
void oa_bag_sanitize(oa_bag *b){int i;for(i=0;i<OA_SLOT_COUNT;i++){int e=b->equipped[i];if(e<0||e>=OA_ITEM_COUNT||ITEMS[e].slot!=i||!b->count[e])b->equipped[i]=-1;}
 if(b->equipped[OA_SLOT_WEAPON]<0){if(!b->count[OA_ITEM_STEEL])b->count[OA_ITEM_STEEL]=1;b->equipped[OA_SLOT_WEAPON]=OA_ITEM_STEEL;}}
void oa_bag_add(oa_bag *b,int i,int n){if(!oa_item_get(i)||n<=0)return;b->count[i]=(uint16_t)(b->count[i]+n>9999?9999:b->count[i]+n);}
int oa_bag_is_equipped(const oa_bag *b,int i){int s;if(!oa_item_get(i))return 0;s=ITEMS[i].slot;return s!=OA_SLOT_NONE&&b->equipped[s]==i;}
int oa_bag_equip(oa_bag *b,int i){const oa_item_def *d=oa_item_get(i);if(!d||d->slot==OA_SLOT_NONE||!b->count[i])return 0;b->equipped[d->slot]=(int16_t)i;return 1;}
int oa_bag_unequip(oa_bag *b,int i){const oa_item_def *d=oa_item_get(i);if(!d||d->slot==OA_SLOT_NONE||d->slot==OA_SLOT_WEAPON||b->equipped[d->slot]!=i)return 0;b->equipped[d->slot]=-1;return 1;}
float oa_bag_use(oa_bag *b,int i,float health,float max){const oa_item_def *d=oa_item_get(i);float gained;if(!d||!d->heal||!b->count[i]||health>=max||health<=0)return 0;gained=(float)d->heal;if(gained>max-health)gained=max-health;b->count[i]--;return gained;}
float oa_bag_damage(const oa_bag *b){const oa_item_def *d=oa_item_get(b->equipped[OA_SLOT_WEAPON]);return d?(float)d->power:22.f;}
int oa_bag_armor(const oa_bag *b){int s,t=0;for(s=OA_SLOT_HEAD;s<OA_SLOT_COUNT;s++){const oa_item_def *d=oa_item_get(b->equipped[s]);if(d)t+=d->power;}return t;}
float oa_armor_scale(int a){return 100.f/(100.f+(float)(a<0?0:a));}
int oa_bag_weapon_model(const oa_bag *b){const oa_item_def *d=oa_item_get(b->equipped[OA_SLOT_WEAPON]);return d&&d->model>=0?d->model:0;}
