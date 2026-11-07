#ifndef OA_MATERIAL_PROBES_H
#define OA_MATERIAL_PROBES_H
#include <GLES3/gl3.h>
struct AAssetManager;
typedef struct oa_material_probes oa_material_probes;
/* Renderer-owned independent cube registry. Never inherits another material's probe. */
oa_material_probes *oa_material_probes_open(struct AAssetManager*,unsigned material_count);
GLuint oa_material_probes_get(oa_material_probes*,unsigned material);
void oa_material_probes_gpu_close(oa_material_probes*);
void oa_material_probes_close(oa_material_probes*);
#endif
