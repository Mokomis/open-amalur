#ifndef OA_ITEMS_H
#define OA_ITEMS_H
/* Inventory rules. Names and icons come from the game; power, value and effects are authored
 * host values, because the game derives real stats from level curves not yet decoded. */
#include <stdint.h>
enum{OA_SLOT_WEAPON,OA_SLOT_HEAD,OA_SLOT_TORSO,OA_SLOT_HANDS,OA_SLOT_LEGS,OA_SLOT_FEET,OA_SLOT_COUNT,OA_SLOT_NONE=-1};
enum{OA_TAB_ALL,OA_TAB_WEAPONS,OA_TAB_ARMOR,OA_TAB_CONSUMABLES,OA_TAB_REAGENTS,OA_TAB_COUNT};
enum{OA_RARITY_COMMON,OA_RARITY_UNCOMMON,OA_RARITY_RARE,OA_RARITY_EPIC};
enum{OA_ITEM_IRON,OA_ITEM_STEEL,OA_ITEM_AZURITE,OA_ITEM_SYLVANITE,OA_ITEM_PRISMERE,
 OA_ITEM_VIGILANT_HELM,OA_ITEM_TUATHA_HELM,OA_ITEM_VIGILANT_CUIRASS,OA_ITEM_TUATHA_CUIRASS,OA_ITEM_VIGILANT_GAUNTLETS,OA_ITEM_BATTLE_GAUNTLETS,OA_ITEM_VIGILANT_GREAVES,OA_ITEM_DAUNTLESS_GREAVES,OA_ITEM_SILENTSTEP_BOOTS,OA_ITEM_ZODIAC_BOOTS,
 OA_ITEM_MINOR_POTION,OA_ITEM_GREATER_POTION,OA_ITEM_MASTER_POTION,OA_ITEM_COUNT};
#define OA_WEAPON_MODELS 5
typedef struct oa_item_def{const char *name,*kind;int slot,sprite,power,value,rarity,heal,model;}oa_item_def;
typedef struct oa_bag{uint16_t count[OA_ITEM_COUNT];int16_t equipped[OA_SLOT_COUNT];uint32_t gold;}oa_bag;
const oa_item_def *oa_item_get(int item);
void oa_bag_new(oa_bag *b);
void oa_bag_sanitize(oa_bag *b);
void oa_bag_add(oa_bag *b,int item,int count);
int oa_bag_is_equipped(const oa_bag *b,int item);
/* Weapons swap but cannot be emptied, since there is no unarmed moveset. */
int oa_bag_equip(oa_bag *b,int item);
int oa_bag_unequip(oa_bag *b,int item);
/* Returns health restored, or 0 when the item cannot be used now. */
float oa_bag_use(oa_bag *b,int item,float health,float max_health);
float oa_bag_damage(const oa_bag *b);
int oa_bag_armor(const oa_bag *b);
/* Damage after armor: raw*100/(100+armor). */
float oa_armor_scale(int armor);
int oa_bag_weapon_model(const oa_bag *b);
#endif
