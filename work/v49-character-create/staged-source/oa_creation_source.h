#ifndef OA_CREATION_SOURCE_H
#define OA_CREATION_SOURCE_H
#include <stdint.h>
/* Source-backed choices. Geometry candidates remain diffuse-only and unreviewed on GPU. */
#define OA_CREATION_SOURCE_TYPES 8
#define OA_CREATION_SOURCE_SKILLS 9
#define OA_CREATION_NAME_UI_LIMIT 16
typedef struct oa_creation_source_type {const char *type,*race,*gender,*default_name;uint32_t race_hash,gender_hash,simtype,lite,rig;uint32_t head,hair,beard,tattoo,accessory;const char *geometry_candidate;} oa_creation_source_type;
static const oa_creation_source_type oa_creation_source_types[8]={
{"Almain_Male","Almain","Male","Elrid",1812351u,673049u,669805u,1536820u,456813u,1304307u,1388827u,1371890u,1431913u,1498507u,"packs/Almain_Male/character.bin"},
{"Almain_Female","Almain","Female","Aidith",1812351u,1641879u,669806u,1536818u,611642u,1384512u,1384365u,0u,1431913u,1498507u,0},
{"Varani_Male","Varani","Male","Stigandr",1889828u,673049u,669805u,1536821u,456813u,1304403u,1304591u,1389483u,1431913u,1498507u,"packs/Varani_Male/character.bin"},
{"Varani_Female","Varani","Female","Isolda",1889828u,1641879u,669806u,1536819u,611642u,1385080u,1384498u,0u,1431913u,1498507u,0},
{"Ljosalfar_Male","Ljosalfar","Male","Lorcan",4668301u,673049u,669807u,1536816u,456813u,1304443u,1304600u,1390251u,1431913u,1498507u,0},
{"Ljosalfar_Female","Ljosalfar","Female","Siobhan",4668301u,1641879u,669808u,1536839u,611642u,1385165u,1384650u,0u,1431913u,1498507u,0},
{"Dokkalfar_Male","Dokkalfar","Male","Caerwyn",4602950u,673049u,669807u,1536813u,456813u,1304512u,1304602u,1390268u,1431913u,1498507u,0},
{"Dokkalfar_Female","Dokkalfar","Female","Niah",4602950u,1641879u,669808u,1536800u,611642u,1389535u,1384370u,0u,1431913u,1498507u,0},
};
/* Order: Alchemy,Blacksmithing,DetectHidden,Dispelling,Lockpicking,Mercantile,Persuasion,Sagecraft,Stealth; values are native raw skill units (10/rank). */
static const uint16_t oa_creation_racial_bonus[4][9]={
{10,20,0,0,0,0,10,0,0},
{0,0,10,0,20,10,0,0,0},
{10,0,0,20,0,0,0,10,0},
{0,0,0,0,0,0,10,10,20},
};
typedef struct oa_creation_source_patron {const char *name;uint32_t buff_id;} oa_creation_source_patron;
/* Per race: Almain, Varani, Ljosalfar, Dokkalfar; original order. None has a real buff. */
static const oa_creation_source_patron oa_creation_patrons[4][6]={
{{"Fire",1254092u},{"Wisdom",1254094u},{"War",1254095u},{"Order",1254099u},{"Justice",1254101u},{"None",1697849u}},
{{"Fire",1254092u},{"Water",1254093u},{"War",1254095u},{"Death",1254097u},{"Mischief",1254102u},{"None",1697849u}},
{{"Earth",1254079u},{"Air",1254091u},{"Wisdom",1254094u},{"Order",1254099u},{"Justice",1254101u},{"None",1697849u}},
{{"Wisdom",1254094u},{"Love",1254096u},{"Death",1254097u},{"Fate",1254098u},{"Mischief",1254102u},{"None",1697849u}},
};
#endif
