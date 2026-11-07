#ifndef OA_CHARACTER_MATERIAL_H
#define OA_CHARACTER_MATERIAL_H
#include <GLES3/gl3.h>
/* Source CB exact order: ConstantColor, SpecularValues,
 * CharacterExtraTerms2, FresnelValues2; opaque HardLight only. */
typedef struct oa_character_hardlight {float constant[4],specular[4],extra[4],fresnel[4];} oa_character_hardlight;
/* Standalone nativeVS351 convention: inputs already in world coordinates,
 * independently normalize N/T/B BEFORE interpolation. Skinning must provide its
 * own verified vertex stage through oa_world_program_with_vertex. */
GLuint oa_character_rigid_material_program(unsigned lights);
int oa_character_hardlight_upload(GLuint program,const oa_character_hardlight *);
#endif
