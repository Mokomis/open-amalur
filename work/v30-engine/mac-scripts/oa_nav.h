#ifndef OA_NAV_H
#define OA_NAV_H
/* Where a person fits, on a 2 m grid built offline from terrain slope and collision, and paths across it.
 * This is authored navigation: the game's own path data is not decoded. */
#include <stdint.h>
typedef struct oa_nav{uint32_t width,height;float x0,y0,step;const uint8_t *bits;}oa_nav;
int oa_nav_blocked(const oa_nav *n,float x,float y);
/* Fills up to max waypoints from just after start to the goal. Returns the count, or 0 when no route lies within reach of the search. */
int oa_nav_path(const oa_nav *n,const float from[2],const float to[2],float (*out)[2],int max);
#endif
