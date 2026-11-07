#ifndef OA_STREAM_H
#define OA_STREAM_H
/* Streams the outdoor world in cells on a background thread: geometry at three levels of detail,
 * textures on demand, and the collision around the player. GL work stays on the render thread. */
#include <stddef.h>
#include <stdint.h>
#include "opem_collision.h"
#define OA_STREAM_NEAR 12800.0f
#define OA_STREAM_MID 25600.0f
#define OA_STREAM_FAR 64000.0f
#define OA_STREAM_GRASS 7000.0f
/* Level of detail wanted at a distance: 0 finest, -1 unloaded. */
static inline int oa_stream_want(float distance,float far_range){return distance<OA_STREAM_NEAR?0:distance<OA_STREAM_MID?1:distance<far_range?2:-1;}
typedef struct oa_stream oa_stream;
typedef struct oa_stream_stats{unsigned cells,cells_drawn,draws,triangles,queued,textures,native_material_draws,native_terrain_draws,forced_leaf_cells,native_leaf_cells,region_cells,region_draws,region_lod_culled;float gpu_mb,cpu_mb,upload_ms,upload_worst_ms;}oa_stream_stats;
struct AAssetManager;
oa_stream *oa_stream_open(struct AAssetManager *assets);
void oa_stream_close(oa_stream *s);
void oa_stream_set_far(oa_stream *s,float range);
void oa_stream_bounds(const oa_stream *s,float center[3],float *radius);
/* Blocks until the collision around feet is built. The caller owns the result. */
opem_collision_world *oa_stream_collision_now(oa_stream *s,const float feet[3],char *error,size_t capacity);
/* Starts a rebuild when feet enter a new cell; returns a finished world once, else NULL. */
opem_collision_world *oa_stream_collision_poll(oa_stream *s,const float feet[3]);
/* Render thread. Requests what the eye needs and uploads within a per-frame budget. */
void oa_stream_update(oa_stream *s,const float eye[3]);
/* Draws what is ready. radius limits drawing around center when above zero, for the shadow pass. */
void oa_stream_draw(oa_stream *s,const float mvp[16],int has_texture,int terrain,const float center[3],float radius);
/* Test aid: bit n hides material kind n. */
extern int oa_stream_hide;
/* Diagnostic only: -1 keeps normal selection; 0 requests finest cutout geometry. */
extern int oa_stream_leaf_lod_override;
extern int oa_stream_leaf_native;
extern int oa_stream_region;
/* Draws with one program per material kind: opaque, terrain, cutout, foliage, river, waterfall, veil. */
void oa_stream_draw_world(oa_stream *s,const float mvp[16],const unsigned program[7],unsigned features);
void oa_stream_gpu_close(oa_stream *s);
void oa_stream_get_stats(oa_stream *s,oa_stream_stats *out);
int oa_stream_native_post(const oa_stream *s,float out[4]);
void oa_stream_draw_world_range(oa_stream *s,const float m[16],const GLuint programs[7],unsigned features,int first,int last,int reset_stats);
#endif
