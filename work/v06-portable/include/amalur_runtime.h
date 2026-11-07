#ifndef AMALUR_RUNTIME_H
#define AMALUR_RUNTIME_H

#include <stddef.h>
#include <stdint.h>
#include "lua.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct amalur_runtime amalur_runtime;
typedef struct amalur_runtime_config {
    const char *runtime_dir;       /* Required: explicit directory of five modules. */
    uint64_t instruction_budget;  /* Per eval; 0 selects 1,000,000. */
    size_t memory_limit_bytes;    /* Lua allocator cap; 0 selects 64 MiB. */
} amalur_runtime_config;

/* Each runtime is one independent Lua 5.1 realm. No game services are invented.
 * error is optional and receives a bounded diagnostic. NULL means failure. */
amalur_runtime *amalur_runtime_create(const amalur_runtime_config *config,
                                     char *error, size_t error_capacity);
void amalur_runtime_destroy(amalur_runtime *runtime);

/* Trusted embedding access. Do not run concurrently on the same runtime.
 * Native providers must bound their own work; the hook bounds Lua instructions.
 * Calling arbitrary Lua APIs may throw; use normal protected Lua API discipline. */
lua_State *amalur_runtime_state(amalur_runtime *runtime);

/* Input table is at provider_index on this realm's Lua stack. Registry bridge
 * snapshots its known methods. Missing methods fail explicitly when invoked.
 * Uses a separate bounded 1M-instruction setup budget, not the eval budget.
 * Leaves the input stack unchanged, appending an error object only on failure. */
int amalur_runtime_set_provider(amalur_runtime *runtime, int provider_index,
                               char *error, size_t error_capacity);

/* Eval clears earlier stack values, then retains ALL results on success,
 * including trailing nil and exact type11 userdata. result_count is exact.
 * Failure leaves one original Lua error object on the stack and returns nonzero.
 * source/file is trusted recovered code or test input, not a security boundary. */
int amalur_runtime_eval_file(amalur_runtime *runtime, const char *path,
                            int *result_count, char *error, size_t error_capacity);
int amalur_runtime_eval_source(amalur_runtime *runtime, const char *source,
                              size_t length, const char *name, int *result_count,
                              char *error, size_t error_capacity);
size_t amalur_runtime_memory_used(const amalur_runtime *runtime);

#ifdef __cplusplus
}
#endif
#endif
