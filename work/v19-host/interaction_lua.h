#ifndef OPEM_INTERACTION_LUA_H
#define OPEM_INTERACTION_LUA_H
#include "interaction_state.h"
#include "amalur_runtime.h"
/* One worker owns runtime and interaction for their entire shared lifetime. */
int oa_lua_install(amalur_runtime *,oa_interaction *,const char *source,size_t length,char *error,size_t cap);
int oa_lua_interact(amalur_runtime *,oa_interaction *,char *error,size_t cap);
#endif
