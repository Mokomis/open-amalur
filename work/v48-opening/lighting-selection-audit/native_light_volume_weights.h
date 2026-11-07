#ifndef NATIVE_LIGHT_VOLUME_WEIGHTS_H
#define NATIVE_LIGHT_VOLUME_WEIGHTS_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Source SPACE root+c8,60B: settingsIndex,T4,Q4,S3,opaque,fade,id.
 * Only the needed T/Q/S/fade fields are represented here.
 * Source world rotation is conjugated Hamilton; query inverse uses R(sourceQ).
 * Admitted input: finite coordinates, approximately-unit source Q, S>=0. */
typedef struct oa_light_volume {
    float translation[3];
    float quaternion[4]; /* source XYZW, never silently normalized */
    float scale[3];
    float fade;
} oa_light_volume;
typedef enum oa_light_volume_mode {
    OA_LIGHT_NORMAL = 0,
    OA_LIGHT_ADDITIONAL_OVERRIDE = 1,
    OA_LIGHT_HARD_OVERRIDE = 2
} oa_light_volume_mode;
typedef enum oa_light_volume_status {
    OA_LIGHT_INVALID = -1,
    OA_LIGHT_NORMAL_READY = 0,
    OA_LIGHT_ADDITIONAL_INPUT_REQUIRED = 1,
    OA_LIGHT_HARD_INPUT_REQUIRED = 2
} oa_light_volume_status;
typedef struct oa_light_volume_result {
    float raw_local_total;
    float base_residual;
    float normalization_total;
    float normalized_base;
} oa_light_volume_result;
/* Return1 on admitted input,0 otherwise. No game state or allocation. */
int oa_light_volume_distance(const oa_light_volume *volume,
                             const float point[3], float *distance);
float oa_light_volume_fade_weight(float distance, float fade, float space_weight);
/* Native ordinary local/base weights only. Caller supplies Space weight and mode.
 * NORMAL: returns0, complete ordinary result.
 * ADDITIONAL: returns1 and ordinary result ONLY; subsequent override is unknown.
 * HARD: returns2 without touching output buffers; normal volumes are bypassed.
 * INVALID: returns-1; no valid result promised.
 * Does not select a profile, interpolate colors, or discover override inputs. */
oa_light_volume_status oa_light_volume_weights(
    const oa_light_volume *volumes, size_t count, const float point[3],
    float space_weight, oa_light_volume_mode mode,
    float *normalized_weights, oa_light_volume_result *result);
#ifdef __cplusplus
}
#endif
#endif
