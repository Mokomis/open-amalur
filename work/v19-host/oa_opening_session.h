#ifndef OA_OPENING_SESSION_H
#define OA_OPENING_SESSION_H
#include "oa_opening_movement.h"
#include "opem_collision.h"
struct AAssetManager;
struct oa_stream;
typedef struct oa_opening_session oa_opening_session;
/* This isolated source-room prototype owns one movement-only checkpoint.
 * Cinematic skip is explicit; no native quest, inventory or door is synthesized. */
oa_opening_session *oa_opening_session_open(struct AAssetManager *,const char *,
    unsigned space,unsigned region,const oa_movement_pose *,int explicit_skip,char *,size_t);
void oa_opening_session_close(oa_opening_session *);
int oa_opening_session_update(oa_opening_session *,const oa_movement_pose *,char *,size_t);
int oa_opening_session_save(oa_opening_session *,char *,size_t);
int oa_opening_session_has_checkpoint(const oa_opening_session *);
/* Stages current collision + controller before any Lua restore. On failure the
 * caller's world/controller/pose remain unchanged. Caller owns returned world. */
int oa_opening_session_load(oa_opening_session *,struct oa_stream *,
    const opem_controller_config *,opem_collision_world **,opem_controller *,
    oa_movement_pose *,char *,size_t);
#endif
