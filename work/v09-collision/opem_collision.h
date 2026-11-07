#ifndef OPEM_COLLISION_H
#define OPEM_COLLISION_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct opem_collision_world opem_collision_world;
typedef struct opem_controller_config {
    float radius,height,skin,step_height,ground_snap;
    float max_slope_cos,gravity,max_speed,max_fall_distance;
    float max_ceiling_height;
    int require_ceiling; /* Indoor spawn policy; not an original game rule. */
} opem_controller_config;
typedef struct opem_controller {
    float feet[3],last_safe_feet[3],velocity_z;
    int grounded,valid,recovered_last_step;
    uint32_t contacts_last_step,queries_last_step,edge_blocks_last_step;
} opem_controller;
typedef struct opem_collision_stats {
    uint32_t triangles,nodes,degenerate_triangles;
    size_t allocated_bytes;
    float bounds_min[3],bounds_max[3];
} opem_collision_stats;

/* Z is up. Defaults assume 100 geometry units per metre, pending native proof.
 * radius32,height170,speed240,step25,gravity980,max slope45 degrees.
 * Motion is authored approximate collision, not recovered native physics. */
void opem_controller_config_default(opem_controller_config *config);

/* Copies only xyz from triangle soup; stride is floats per vertex (scene=9).
 * Output must be NULL. At most300000 triangles; all positions finite and within
 * +/-1e6 units. No host mesh ownership transfer. Build failure leaves NULL. */
int opem_collision_create(opem_collision_world **output,const float *vertices,
    uint32_t vertex_count,uint32_t stride_floats,char *error,size_t capacity);
void opem_collision_destroy(opem_collision_world *world);
void opem_collision_get_stats(const opem_collision_world *world,opem_collision_stats *stats);

/* Deterministic floor candidate search. Optional hint is feet xyz. Require
 * complete capsule clearance, walkable floor, and optionally overhead geometry.
 * Failure leaves controller unchanged. No free-fly spawn fallback. */
int opem_controller_spawn(const opem_collision_world *world,const opem_controller_config *config,
    const float hint_xyz[3],opem_controller *controller,char *error,size_t capacity);

/* desired_vx/vy are WORLD XY units/second, bounded by max_speed. dt must be
 * finite in[0,0.1]. Internally substeps at<=1/120s; continuous sweeps protect
 * against thin triangles. Invalid inputs/query exhaustion freeze atomically.
 * Grounded walking rejects edges without a walkable landing within step height.
 * Airborne falls beyond max_fall_distance restore last validated grounded pose.
 * No jump/animation/engine callback is implied. Call spawn again for reset. */
int opem_controller_step(const opem_collision_world *world,const opem_controller_config *config,
    opem_controller *controller,float desired_vx,float desired_vy,float dt,
    char *error,size_t capacity);

/* Diagnostic validation of the current capsule; no mutation. */
int opem_controller_clear(const opem_collision_world *world,const opem_controller_config *config,
    const float feet[3],char *error,size_t capacity);
#ifdef __cplusplus
}
#endif
#endif
