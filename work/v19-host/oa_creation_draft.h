#ifndef OA_CREATION_DRAFT_H
#define OA_CREATION_DRAFT_H
#include "oa_creation.h"
/* Drafts are distinct from completed profiles and never issue gameplay effects.
 * Return 0 on success (load returns 2 for missing file, 1 for invalid/unreadable);
 * failed loads leave the destination unchanged. */
int oa_creation_draft_load(oa_creation_state *state,const char *path);
int oa_creation_draft_save(const oa_creation_state *state,const char *path);
#endif
