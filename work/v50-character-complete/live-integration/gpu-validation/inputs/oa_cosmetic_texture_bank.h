#ifndef OA_COSMETIC_TEXTURE_BANK_H
#define OA_COSMETIC_TEXTURE_BANK_H
#include <stddef.h>
#include <stdint.h>
#include <GLES3/gl3.h>
typedef int (*oa_cm_read_file)(void *user,const char *name,uint8_t **malloc_bytes,size_t *size);
typedef struct oa_cm_texture_entry {uint32_t asset;GLenum target;GLuint texture;} oa_cm_texture_entry;
typedef struct oa_cm_texture_bank {oa_cm_read_file read;void *user;char prefix[512];unsigned count;oa_cm_texture_entry entries[512];} oa_cm_texture_bank;
int oa_cm_bank_open(oa_cm_texture_bank *,oa_cm_read_file,void *,const char *prefix);
void oa_cm_bank_close(oa_cm_texture_bank *);
/* Suitable as oa_cm_texture_lookup. Resource0/1 unsupported, never fabricated.
 * Reads <prefix><nativeID>.oatx or .oacube, validates complete authored chains
 * before GL allocation, no gamma/row/RB edits, no generated mipmaps. */
GLuint oa_cm_bank_texture(void *,uint32_t asset,GLenum target);
#endif
