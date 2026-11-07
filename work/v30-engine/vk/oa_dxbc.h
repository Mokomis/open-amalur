/* oa_dxbc.h: Shader Model 4 bytecode to SPIR-V. */
#ifndef OA_DXBC_H
#define OA_DXBC_H
#include <stddef.h>
#include <stdint.h>

#define OA_MAX_SIG 32

typedef struct {
    char name[32];
    uint32_t semantic_index, sysval, comp_type, reg, mask;
} oa_sig_element;

typedef struct {
    int is_pixel;
    uint32_t binding_base;
    uint16_t cb_mask;        /* constant buffer slots used */
    uint32_t cb_sizes[16];   /* declared size in bytes */
    uint16_t sampler_mask;
    uint32_t texture_mask;   /* t0..t31 */
    uint8_t texture_dim[32]; /* 2=1D 3=2D 5=3D 6=cube */
    int input_count, output_count;
    oa_sig_element inputs[OA_MAX_SIG], outputs[OA_MAX_SIG];
    int writes_depth, uses_discard;
} oa_shader_info;

/* Binding layout inside the one push descriptor set: base+slot constant buffers, base+16+slot samplers, base+32+slot textures.
   Pixel shaders use base 0 and vertex shaders base 64. */
#define OA_BIND_CB 0
#define OA_BIND_SAMPLER 16
#define OA_BIND_TEXTURE 32
#define OA_BIND_VS_BASE 64

/* Returns 1 and a malloc'd word array on success. On failure returns 0 and describes it in err. */
int oa_dxbc_translate(const void *dxbc, size_t size, oa_shader_info *info, uint32_t **spirv, size_t *words, char *err, size_t err_size);

#endif
