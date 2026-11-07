#ifndef OA_FX_H
#define OA_FX_H
#include <android/asset_manager.h>
/* The zone's placed particle effects, from assets/fx/fx.bin. NULL when the asset is absent. */
typedef struct oa_fx oa_fx;
/* Debug0 retains prior square/view-facing shapes;1uses source/observed shape policy. */
extern int oa_fx_native_shape;
oa_fx *oa_fx_open(AAssetManager *manager);
void oa_fx_update(oa_fx *f,const float eye[3],float dt);
void oa_fx_draw(oa_fx *f,const float mvp[16],const float fog_color[3],float fog_a,float fog_b,unsigned scene_depth,const float inverse_depth[2],int width,int height);
void oa_fx_close(oa_fx *f);
/* Particles alive in the last update. */
int oa_fx_live(const oa_fx *f);
#endif
