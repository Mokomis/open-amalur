#ifndef OPEM_INTERACTION_STATE_H
#define OPEM_INTERACTION_STATE_H
#include <stdint.h>
#include <stddef.h>
/* Authored engine ownership. These are not Amalur native type11 handles. */
typedef struct oa_handle {uint32_t slot,generation;} oa_handle;
typedef struct oa_object {uint32_t generation,source_id,type_id,script_id;float position[3],interaction_point[3];int alive;} oa_object;
typedef struct oa_registry {oa_object objects[32];} oa_registry;
typedef struct oa_reagent {uint32_t id;const char *symbol,*essence;} oa_reagent;
typedef struct oa_need {const char *essence;unsigned quantity;} oa_need;
typedef struct oa_formula {uint32_t id,product;const char *symbol;unsigned difficulty,need_count;oa_need needs[8];} oa_formula;
typedef struct oa_catalog {const oa_reagent *reagents;size_t reagent_count;const oa_formula *formulas;size_t formula_count;} oa_catalog;
typedef struct oa_item {uint32_t id,count;} oa_item;
typedef struct oa_inventory {oa_item items[1024];unsigned count,alchemy_skill;} oa_inventory;
typedef struct oa_interaction {
 oa_registry registry;oa_handle workbench,player,selected;
 oa_catalog catalog;oa_inventory inventory;
 int ready,window_open,page,tab,recipe_selected,inventory_writable;char status[128];
} oa_interaction;
void oa_registry_init(oa_registry *);
oa_handle oa_object_create(oa_registry *,uint32_t source,uint32_t type,uint32_t script,const float position[3]);
const oa_object *oa_object_resolve(const oa_registry *,oa_handle);
int oa_object_target(oa_registry *,oa_handle,const float point[3]);
int oa_object_remove(oa_registry *,oa_handle);
/* Authored reach/facing policy, no unverified native property interpretation. */
int oa_workbench_in_reach(const oa_registry *,oa_handle,const float feet[3],float yaw);
uint32_t oa_inventory_count(const oa_inventory *,uint32_t id);
int oa_inventory_set(oa_inventory *,uint32_t id,uint32_t count);
uint32_t oa_essence_count(const oa_catalog *,const oa_inventory *,const char *essence);
int oa_can_craft(const oa_catalog *,const oa_inventory *,const oa_formula *,char *reason,size_t cap);
int oa_craft(const oa_catalog *,oa_inventory *,const oa_formula *,char *reason,size_t cap);
int oa_inventory_load(oa_inventory *,const char *path,char *error,size_t cap);
int oa_inventory_save(const oa_inventory *,const char *path,char *error,size_t cap);
#endif
