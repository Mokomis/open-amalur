#include "oa_patron_presentation.h"
#include <stddef.h>
static const oa_patron_presentation rows[]={
{1254079u,"Earth","Gaea - Goddess of Earth, the Harvest, and Fertility","Gaea's Blessing","The earth goddess Gaea's star shone brightly on the day you were reborn. It would seem you have her blessing.","+5% Elemental Resistance"},
{1254091u,"Air","Ohnshan - God of Air, Sky, Stars, and the Winds","Ohnshan's Blessing","The wind goddess Ohnshan's star shone brightly on the day you were reborn. It would seem you have her blessing.","+6% Lightning Damage; +6% Lightning Resistance"},
{1254092u,"Fire","Vraekor - God of Fire, and Patron of the Forge","Vraekor's Blessing","The fire god Vraekor's crimson star shone brightly on the day you were reborn. It would seem you have his blessing.","+6% Fire Damage; +6% Fire Resistance"},
{1254093u,"Water","Njordir - God of Water, Patron of Fishing and Sailing","Njordir's Blessing","The water god Njordir's azure star shone brightly on the day you were reborn. Somehow it would seem you have his favor.","+6% Ice Damage; +6% Ice Resistance"},
{1254094u,"Wisdom","Ethene - Goddess of Wisdom and Art","Ethene's Blessing","The star of Ethene, goddess of wisdom, shone brightly on the day you were reborn. It would seem that somehow you have acquired her favor.","+10% Mana"},
{1254095u,"War","Thyrdon - God of War, Battle, and Tactics","Thyrdon's Blessing","The war god Thyrdon's star shone brightly on the day you were reborn. It would seem you have his blessing.","+5% Physical Damage; +5% Armor"},
{1254096u,"Love","Aryllia - Goddess of Love and Beauty","Aryllia's Blessing","The star of Aryllia, goddess of love, shone brightly on the day you were reborn. Blessed by this soothing light, it would seem you have her blessing.","+5% Health; +1% Critical Hit Chance"},
{1254097u,"Death","Belen - God of Death","Belen's Blessing","The death god Belen's star shone brightly on the day you were reborn. It would seem you have his blessing.","+1% Critical Hit Chance; +8% Critical Hit Damage"},
{1254098u,"Fate","Lyria - Goddess of Fate, Magic, and Luck","Lyria's Blessing","The star of Lyria, goddess of magic and fate, shone brightly on the day you were reborn. It would seem you have her blessing.","+5% Mana; +5% Mana Regeneration"},
{1254099u,"Order","Mitharu - God of Order","Mitharu's Blessing","The holy light of Mitharu, god of order, shone brightly on the day you were reborn. It would seem you have his blessing.","+5% Health; +5% Mana"},
{1254101u,"Justice","Ynadon - God of Justice","Ynadon's Blessing","The star of Ynadon, god of justice, shone brightly on the day you were reborn. It would seem you have his blessing.","+10% Health"},
{1254102u,"Mischief","Lupoku - God of Mischief, Patron of Brewing","Lupoku's Blessing","The mischievious god Lupoku's glittering star shone brightly on the day you were reborn. It would seem you have his blessing.","+6% Poison Damage; +6% Poison Resistance"},
{1697849u,"None","Beholden to no god, your self-sufficiency yields its own rewards.","Self-Sufficient","A boon granted by your own strength of will. You are beholden to no god.","+1% Experience"},
};
const oa_patron_presentation *oa_patron_presentation_find(uint32_t id){size_t i;for(i=0;i<sizeof(rows)/sizeof(rows[0]);i++)if(rows[i].buff_id==id)return rows+i;return NULL;}
