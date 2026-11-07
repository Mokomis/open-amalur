#ifndef AMALUR_BLOB_H
#define AMALUR_BLOB_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

/* Native-confirmed container storage, not a decoded game scene:
 * LE u32 payload_bytes, LE u32 fixup_bytes, payload, LE u32 fixup slots.
 * Each slot is payload-relative and holds a LE u32 FILE-relative target.
 * Native FUN_00a6e7c0 relocates it as base+stored_word-8. This loader retains
 * the stored integer and exposes a checked payload offset stored_word-8;
 * it never rewrites serialized fields into host pointers. */
typedef struct amalur_blob amalur_blob;
typedef struct amalur_blob_limits {
    size_t max_file_bytes;       /* 0 selects 64 MiB. */
    uint32_t max_fixup_slots;    /* 0 selects 1,048,576. */
} amalur_blob_limits;
typedef struct amalur_blob_fixup {
    uint32_t slot_offset;        /* Relative to payload start, file offset +8. */
    uint32_t stored_file_offset; /* Original unmodified LE u32 target word. */
    uint32_t target_offset;      /* Checked stored_file_offset-8 in payload. */
} amalur_blob_fixup;

/* On success the blob owns an immutable copy of all bytes. Caller may release
 * or mutate the input. On failure returns NULL with a bounded error string.
 * Source hashing/provenance belongs to the embedding importer. */
amalur_blob *amalur_blob_parse(const void *bytes, size_t length,
                              const amalur_blob_limits *limits,
                              char *error, size_t error_capacity);
amalur_blob *amalur_blob_load_file(const char *path,
                                  const amalur_blob_limits *limits,
                                  char *error, size_t error_capacity);
void amalur_blob_destroy(amalur_blob *blob);
const unsigned char *amalur_blob_file_bytes(const amalur_blob *blob, size_t *length);
const unsigned char *amalur_blob_payload(const amalur_blob *blob, uint32_t *length);
uint32_t amalur_blob_fixup_count(const amalur_blob *blob);
/* Entries preserve original table order, even if the input table is unsorted. */
int amalur_blob_fixup_at(const amalur_blob *blob, uint32_t index, amalur_blob_fixup *entry);
int amalur_blob_read_u32(const amalur_blob *blob, uint32_t offset, uint32_t *value);
/* Raw IEEE754 binary32 interpretation; NaN/Inf are not semantic scene values. */
int amalur_blob_read_f32(const amalur_blob *blob, uint32_t offset, float *value);
/* Resolves only a registered fixup slot and a caller-declared byte count.
 * One-past-end targets are accepted only for zero-byte spans. Stored words
 * below8 are rejected; no null-pointer exception is established. Stored8
 * resolves to payload offset0, not a null reference. */
int amalur_blob_resolve_span(const amalur_blob *blob, uint32_t slot_offset,
                             size_t byte_count, const unsigned char **bytes,
                             uint32_t *target_offset);

#ifdef __cplusplus
}
#endif
#endif
