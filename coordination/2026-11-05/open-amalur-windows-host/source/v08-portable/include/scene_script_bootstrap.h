#ifndef OPEM_SCENE_SCRIPT_BOOTSTRAP_H
#define OPEM_SCENE_SCRIPT_BOOTSTRAP_H
#include "amalur_runtime.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Trusted host I/O. Paths are fixed runtime/<basename>, modules/modules.tsv,
 * or manifest-listed modules/<basename>; never paths read from game resources.
 * size/read return zero on success, nonzero with a diagnostic on failure.
 * read must fill exactly length bytes and reject a changed resource size.
 * Neither callback transfers ownership or retains the destination pointer. */
typedef struct scene_script_resources {
    void *context;
    int (*size)(void *,const char *,size_t *,char *,size_t);
    int (*read)(void *,const char *,char *,size_t,char *,size_t);
} scene_script_resources;
typedef struct scene_script_options {
    const char *root_module;      /* NULL selects SpaceCommon. */
    const char *event;            /* NULL only loads root; otherwise zero arguments. */
    size_t maximum_total_bytes;   /* 0 selects64MiB, includes manifest/core/modules. */
    size_t maximum_source_bytes;  /* 0 selects16MiB per source. */
    size_t lua_memory_limit;      /* 0 retains runtime default64MiB. */
    uint64_t instruction_budget;  /* 0 retains runtime default. */
    /* Optional trusted host setup after core initialization, before recovered
     * source registration/execution. Nonzero return reports failure via error.
     * Lua errors are caught by bootstrap; callback must clean its own C resources
     * before any operation that can raise a Lua error. No instruction hook bounds
     * arbitrary host callback work; use the runtime's protected provider API. */
    int (*setup)(amalur_runtime *,void *,char *,size_t);
    void *setup_context;
    /* Optional exact registered bootstrap name, required after all lazy source
     * registration and before root. NULL preserves the preceding behavior.
     * Bootstrap gets its own bounded runtime evaluation budget, as root/event
     * already do. No path aliases or implicit source searches are performed. */
    const char *bootstrap_module;
} scene_script_options;
typedef struct scene_script_result {
    int ok, root_loaded, event_invoked, event_argument_count;
    unsigned registered_modules;
    size_t resource_bytes, lua_memory_bytes;
    char phase[32], error[2048];
    int bootstrap_loaded;       /* Only set after optional bootstrap succeeds. */
} scene_script_result;
/* Returns a live realm on success, owned by caller; caller must destroy it.
 * On failure destroys any realm and frees every owned C buffer. No providers
 * are fabricated. This proves portable module/event loading, not native game
 * behavior. All roots are explicitly registered before require runs. */
amalur_runtime *scene_script_bootstrap(const scene_script_resources *,
                                     const scene_script_options *,scene_script_result *);
#ifdef __cplusplus
}
#endif
#endif
