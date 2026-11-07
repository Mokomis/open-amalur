/* oa_engine.c: engine functions rewritten in C, patched over the originals in the running koa.exe.
   Each entry names its address in cs:15032 and the exact bytes expected there. A mismatch skips that entry, so a different build stays untouched.
   Set OA_NO_REPLACE=1 to run the original code. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define IMAGE_BASE 0x400000u
#define COM __stdcall

/* Engine texture record, only the fields seen so far. */
typedef struct {
    uint8_t pad0[0x0f];
    uint8_t mip_count;
    uint8_t pad1[0x04];
    void *resource; /* ID3D11Resource* */
} oa_texture;

typedef struct {
    void **context; /* ID3D11DeviceContext* */
} oa_render_context;

static volatile LONG g_calls_unmap;

/* 010596c0: unmap one subresource of an engine texture. D3D11CalcSubresource(mip, slice, mip_count) inlined. */
static void __cdecl oa_texture_unmap(oa_render_context *rc, const oa_texture *tex, UINT mip, UINT slice) {
    void *ctx = rc->context;
    void(COM * unmap)(void *, void *, UINT) = (void(COM *)(void *, void *, UINT))(*(void ***)ctx)[15];
    InterlockedIncrement(&g_calls_unmap);
    unmap(ctx, tex->resource, tex->mip_count * slice + mip);
}

/* Field names below are what the code does with them, not original names. */
typedef struct {
    uint8_t pad0[2];
    uint16_t slot;
    uint8_t pad1[4];
    uint8_t *sampler; /* holds the ID3D11SamplerState* at +8 */
} oa_slot_binding;

typedef struct {
    uint8_t pad0[8];
    oa_slot_binding *bindings;
} oa_material_bindings;

typedef struct {
    uint8_t pad0[2];
    uint16_t count;
    uint8_t pad1[8];
    const uint8_t *texture_index;
} oa_binding_layout;

typedef struct {
    void ***context_holder;
    uint8_t pad0[0x18];
    void *samplers[0x10]; /* +0x1c */
    void *textures[0x20]; /* +0x5c */
} oa_state_cache;

static volatile LONG g_calls_bind;

/* 00c5b2a0: bind a material's textures and samplers to the pixel stage, updating the state cache. */
static void __cdecl oa_bind_material_textures(oa_state_cache *cache, const uint8_t *scene, const uint32_t *texture_ids, const oa_material_bindings *mat, const oa_binding_layout *layout) {
    uint8_t **table = *(uint8_t ***)(scene + 0x254);
    UINT i;
    InterlockedIncrement(&g_calls_bind);
    for (i = 0; i < layout->count; i++) {
        const oa_slot_binding *b = &mat->bindings[i];
        uint32_t id = texture_ids[layout->texture_index[i]];
        uint8_t *tex = id ? table[id & 0xffff] : NULL;
        UINT slot = b->slot;
        uint8_t *sampler = b->sampler;
        void *null_view = NULL;
        void *ctx = *cache->context_holder;
        cache->samplers[slot] = sampler;
        ((void(COM *)(void *, UINT, UINT, void *))(*(void ***)ctx)[10])(ctx, slot, 1, sampler ? (void *)(sampler + 8) : (void *)&null_view);
        cache->textures[slot] = tex;
        ctx = *cache->context_holder;
        ((void(COM *)(void *, UINT, UINT, void *))(*(void ***)ctx)[8])(ctx, slot, 1, tex ? (void *)(tex + 0x18) : (void *)&null_view);
    }
}

typedef struct {
    uint16_t texture_slot;
    uint16_t slot;
    uint8_t pad[4];
    uint8_t *sampler;
} oa_direct_binding;

typedef struct {
    UINT count;
    uint8_t pad[4];
    oa_direct_binding *bindings;
} oa_direct_layout;

static volatile LONG g_calls_bind_ids, g_calls_bind_table;

static __inline void bind_one(oa_state_cache *cache, UINT slot, uint8_t *sampler, uint8_t *tex) {
    void *null_view = NULL;
    void *ctx = *cache->context_holder;
    cache->samplers[slot] = sampler;
    ((void(COM *)(void *, UINT, UINT, void *))(*(void ***)ctx)[10])(ctx, slot, 1, sampler ? (void *)(sampler + 8) : (void *)&null_view);
    cache->textures[slot] = tex;
    ctx = *cache->context_holder;
    ((void(COM *)(void *, UINT, UINT, void *))(*(void ***)ctx)[8])(ctx, slot, 1, tex ? (void *)(tex + 0x18) : (void *)&null_view);
}

/* 00c5b390: same binding with texture ids listed in slot order. */
static void __cdecl oa_bind_texture_ids(oa_state_cache *cache, const uint8_t *scene, const uint32_t *texture_ids, const oa_direct_layout *layout) {
    uint8_t **table = *(uint8_t ***)(scene + 0x254);
    UINT i;
    InterlockedIncrement(&g_calls_bind_ids);
    for (i = 0; i < layout->count; i++) {
        const oa_direct_binding *b = &layout->bindings[i];
        uint32_t id = texture_ids[i];
        bind_one(cache, b->slot, b->sampler, id ? table[id & 0xffff] : NULL);
    }
}

/* 00c726d0: __thiscall, ecx points 0x58 past a table of texture pointers. __fastcall with an unused edx has the same ABI. */
static void __fastcall oa_bind_texture_table(uint8_t *table_end, void *unused_edx, oa_state_cache *cache, const oa_direct_layout *layout) {
    UINT i;
    (void)unused_edx;
    InterlockedIncrement(&g_calls_bind_table);
    for (i = 0; i < layout->count; i++) {
        const oa_direct_binding *b = &layout->bindings[i];
        uint8_t *tex = *(uint8_t **)(table_end - 0x58 + (UINT)b->texture_slot * 4);
        bind_one(cache, b->slot, b->sampler, tex);
    }
}

/* ---- 00c961e0: draw a list of packets, all three kinds. ---- */
#define AT(p, off, T) (*(T *)((uint8_t *)(p) + (off)))
#define VT(ctx, i, T) ((T)(*(void ***)(ctx))[i])
#define ABS(a) ((uintptr_t)(a) - IMAGE_BASE + g_base)

typedef struct {
    void *pData;
    UINT row, depth;
} oa_mapped;
typedef HRESULT(COM *map_fn)(void *, void *, UINT, UINT, UINT, oa_mapped *);
typedef void(COM *unmap_fn)(void *, void *, UINT);
typedef void(COM *setcb_fn)(void *, UINT, UINT, void *);
typedef void(COM *setsh_fn)(void *, void *, void *, UINT);
typedef void(COM *set1_fn)(void *, void *);
typedef void(COM *set2_fn)(void *, void *, UINT);
typedef void(COM *setblend_fn)(void *, void *, const float *, UINT);
typedef void(COM *setvb_fn)(void *, UINT, UINT, void *, void *, void *);
typedef void(COM *setib_fn)(void *, void *, UINT, UINT);
typedef void(COM *drawi_fn)(void *, UINT, UINT, int);
typedef void(COM *draw_fn)(void *, UINT, UINT);
typedef void(COM *settopo_fn)(void *, UINT);

static uintptr_t g_base;
static volatile LONG g_calls_draw, g_draw_kind[3], g_imm_quads, g_imm_split, g_imm_discard, g_imm_skipped;

/* Immediate vertex ring in the render holder. Offsets from the disassembly; names describe their use. */
#define HOLDER_IMM_VB 0x10
#define HOLDER_IMM_CURSOR 0x14
#define HOLDER_IMM_SIZE 0x18
#define HOLDER_IMM_STRIDE 0x1c
#define HOLDER_IMM_COUNT 0x20
#define HOLDER_IMM_TOPOLOGY 0x24
#define HOLDER_IMM_QUADS 0x34
#define HOLDER_IMM_DEST 0x38
#define HOLDER_IMM_QUAD_TEMP 0x3c

static void engine_log(uint32_t format, int value) {
    ((void(__cdecl *)(const char *, int))ABS(0x01050e90))((const char *)ABS(format), value);
}

/* Engine primitive type to its internal topology code. */
static int primitive_code(UINT prim) {
    switch (prim) {
    case 1: return 2;
    case 2: return 0;
    case 3: return 1;
    case 5: return 4;
    case 6: return 3;
    default: engine_log(0x0173ba38, (int)prim); return -1;
    }
}

/* Write vertices into the ring buffer and draw. Code 4 is quads, expanded to two triangles each. */
static void immediate_draw(uint8_t *holder, int code, UINT stride, UINT count_in, const void *src) {
    void *ctx = AT(holder, 0, void *);
    UINT count = count_in;
    uint8_t *dest;
    UINT bytes;
    oa_mapped m;
    HRESULT hr;
    if (code == 4) {
        if (count_in * stride > 0x18000) { InterlockedIncrement(&g_imm_skipped); return; }
        InterlockedIncrement(&g_imm_quads);
        count = (count_in >> 2) * 6;
        code = 0;
        AT(holder, HOLDER_IMM_QUADS, uint8_t) = 1;
    } else {
        AT(holder, HOLDER_IMM_QUADS, uint8_t) = 0;
    }
    bytes = count * stride;
    if (bytes > AT(holder, HOLDER_IMM_SIZE, UINT)) { InterlockedIncrement(&g_imm_skipped); return; }
    if (AT(holder, HOLDER_IMM_CURSOR, UINT) + bytes < AT(holder, HOLDER_IMM_SIZE, UINT)) {
        hr = VT(ctx, 14, map_fn)(ctx, AT(holder, HOLDER_IMM_VB, void *), 0, 5, 0, &m);
        if (hr < 0) { engine_log(0x0173b764, hr); return; }
    } else {
        hr = VT(ctx, 14, map_fn)(ctx, AT(holder, HOLDER_IMM_VB, void *), 0, 4, 0, &m);
        if (hr < 0) { engine_log(0x0173b764, hr); return; }
        AT(holder, HOLDER_IMM_CURSOR, UINT) = 0;
        InterlockedIncrement(&g_imm_discard);
    }
    AT(holder, HOLDER_IMM_COUNT, UINT) = count;
    AT(holder, HOLDER_IMM_STRIDE, UINT) = stride;
    AT(holder, HOLDER_IMM_TOPOLOGY, int) = code;
    dest = (uint8_t *)m.pData + AT(holder, HOLDER_IMM_CURSOR, UINT);
    AT(holder, HOLDER_IMM_DEST, uint8_t *) = dest;
    if (AT(holder, HOLDER_IMM_QUADS, uint8_t)) dest = holder + HOLDER_IMM_QUAD_TEMP;
    if (!dest) return;
    memcpy(dest, src, stride * count_in);
    if (AT(holder, HOLDER_IMM_QUADS, uint8_t)) {
        int quad_vertices = ((int)count / 6) * 4;
        int d = (int)count - 6, s = quad_vertices - 4;
        for (; quad_vertices > 0 && d >= 0; d -= 6, s -= 4) {
            uint8_t *out = AT(holder, HOLDER_IMM_DEST, uint8_t *) + (UINT)d * stride;
            const uint8_t *in = holder + HOLDER_IMM_QUAD_TEMP + (UINT)s * stride;
            memcpy(out + stride * 5, in + stride * 3, stride);
            memcpy(out + stride * 4, in + stride * 2, stride);
            memcpy(out + stride * 3, in, stride);
            memcpy(out + stride * 2, in + stride * 2, stride);
            memcpy(out + stride, in + stride, stride);
            memcpy(out, in, stride);
        }
    }
    ctx = AT(holder, 0, void *);
    VT(ctx, 15, unmap_fn)(ctx, AT(holder, HOLDER_IMM_VB, void *), 0);
    ctx = AT(holder, 0, void *);
    VT(ctx, 18, setvb_fn)(ctx, 0, 1, holder + HOLDER_IMM_VB, &stride, holder + HOLDER_IMM_CURSOR);
    ctx = AT(holder, 0, void *);
    VT(ctx, 19, setib_fn)(ctx, NULL, 0x39, 0);
    ctx = AT(holder, 0, void *);
    VT(ctx, 24, settopo_fn)(ctx, *(UINT *)(ABS(0x0175c6d8) + AT(holder, HOLDER_IMM_TOPOLOGY, int) * 4));
    ctx = AT(holder, 0, void *);
    VT(ctx, 13, draw_fn)(ctx, AT(holder, HOLDER_IMM_COUNT, UINT), 0);
    AT(holder, HOLDER_IMM_CURSOR, UINT) += AT(holder, HOLDER_IMM_COUNT, UINT) * stride;
    AT(holder, HOLDER_IMM_STRIDE, UINT) = 0;
}

static void *cb_map(uint8_t *holder, uint8_t *cb_owner);

/* Kind 1: per-instance constants in vertex slot 5, then a draw from a sub-range of the geometry. */
static void draw_kind1(uint8_t *p, uint8_t *tables, uint8_t *state, uint8_t *holder) {
    uint8_t *g = AT(p, 0x2c, uint8_t *);
    uint8_t *range = AT(g, 0x34, uint8_t *);
    uint8_t *format = AT(g, 8, uint8_t *);
    uint8_t *strides = NULL;
    void *data, *ctx;
    void *ib = AT(g, 0x14, void *);
    void *vb[2];
    UINT stride[2], offset[2];
    UINT count = AT(range, 0xc, UINT);
    UINT ib_offset = AT(range, 8, UINT) * 2;
    void **pending = &AT(holder, 4, void *);
    UINT slot;
    AT(state, 0x184, UINT) = 5;
    data = cb_map(holder, AT(tables, 0x18, uint8_t *));
    memcpy(data, AT(p, 0x30, void *), AT(p, 0x34, UINT) * 0x30);
    slot = AT(state, 0x184, UINT);
    AT(state, 0x13c + slot * 4, void *) = NULL;
    ctx = AT(holder, 0, void *);
    VT(ctx, 15, unmap_fn)(ctx, *pending, 0);
    ctx = AT(holder, 0, void *);
    VT(ctx, 7, setcb_fn)(ctx, slot, 1, pending);
    *pending = NULL;
    if (!count) count = ib ? AT(g, 0x18, UINT) : AT(g, 0x10, UINT);
    strides = AT(holder, 0x2c, uint8_t *);
    vb[0] = AT(g, 0xc, void *);
    vb[1] = AT(AT(tables, 0x20, uint8_t *), 4, void *);
    stride[0] = AT(strides, 0xd8, UINT);
    stride[1] = AT(strides, 0xdc, UINT);
    offset[0] = AT(range, 0x14, UINT) * AT(format, 0xd8, UINT);
    offset[1] = 0;
    ctx = AT(holder, 0, void *);
    VT(ctx, 18, setvb_fn)(ctx, 0, 2, vb, stride, offset);
    ctx = AT(holder, 0, void *);
    VT(ctx, 24, settopo_fn)(ctx, AT(g, 0x2c, UINT));
    ctx = AT(holder, 0, void *);
    if (ib) {
        VT(ctx, 19, setib_fn)(ctx, ib, AT(g, 0x28, UINT), ib_offset);
        ctx = AT(holder, 0, void *);
        VT(ctx, 12, drawi_fn)(ctx, count, 0, 0);
    } else {
        VT(ctx, 13, draw_fn)(ctx, count, 0);
    }
}

/* Kind 2: immediate vertices from the packet. Batches over 64 KB are split on primitive boundaries. */
static void draw_kind2(uint8_t *p, uint8_t *holder) {
    UINT stride = AT(p, 0x30, uint16_t);
    UINT verts = AT(p, 0x2e, uint16_t);
    const uint8_t *src = AT(p, 0x34, const uint8_t *);
    int code = primitive_code(AT(p, 0x2c, uint16_t));
    if (verts * stride <= 0x10000) {
        immediate_draw(holder, code, stride, verts, src);
    } else {
        int unit = code == 0 ? 3 : code == 2 ? 2 : code == 4 ? 4 : 1;
        UINT done = 0;
        InterlockedIncrement(&g_imm_split);
        while ((uint16_t)done < verts) {
            uint16_t limit = (uint16_t)(0x10000 / (int)stride);
            uint16_t chunk = (uint16_t)(verts - done);
            UINT n;
            if (chunk > limit) chunk = limit;
            n = (UINT)chunk - (UINT)((int)chunk % unit);
            immediate_draw(holder, code, stride, (uint16_t)n, src + (uint16_t)done * stride);
            done += n;
        }
    }
}

static void *cb_map(uint8_t *holder, uint8_t *cb_owner) {
    void *ctx = AT(holder, 0, void *);
    void *cb = *(void **)cb_owner;
    oa_mapped m;
    if (VT(ctx, 14, map_fn)(ctx, cb, 0, 4, 0, &m) < 0) return NULL;
    AT(holder, 4, void *) = cb;
    return m.pData;
}

/* Unmap the buffer mapped above and bind it to one constant buffer slot of both stages. */
static void cb_commit(uint8_t *holder, UINT slot) {
    void *ctx = AT(holder, 0, void *);
    void **pending = &AT(holder, 4, void *);
    VT(ctx, 15, unmap_fn)(ctx, *pending, 0);
    ctx = AT(holder, 0, void *);
    VT(ctx, 7, setcb_fn)(ctx, slot, 1, pending);
    ctx = AT(holder, 0, void *);
    VT(ctx, 16, setcb_fn)(ctx, slot, 1, pending);
    *pending = NULL;
}

static void __cdecl oa_draw_packets(const uint8_t *cur, const uint8_t *end, uint8_t *tables, uint8_t *state, char use_queries) {
    uint8_t *scene = *(uint8_t **)ABS(0x019fdfb4);
    uint8_t *last_material = NULL;
    uint32_t last_key = 0xffffffffu;
    const char copy_cb5 = *(const char *)ABS(0x01966179);
    const char predication = *(const char *)ABS(0x0196617a);
    void(__cdecl *fill_constants)(void *, void *, void *, void *) = (void(__cdecl *)(void *, void *, void *, void *))ABS(0x00c34c90);
    InterlockedIncrement(&g_calls_draw);
    for (; cur != end; cur += 8) {
        uint8_t *p = AT(cur, 4, uint8_t *);
        uint8_t *material = AT(p, 8, uint8_t *);
        uint8_t *holder = AT(state, 0, uint8_t *);
        void *ctx = AT(holder, 0, void *);
        uint8_t *x, *pred;
        uint32_t key;
        if (!material || !(x = AT(material, 0x10, uint8_t *))) continue;
        if (material != last_material) {
            uint8_t *vs = AT(material, 8, uint8_t *);
            void **ps = AT(material, 0xc, void **);
            uint8_t *bindings;
            if (vs) {
                VT(ctx, 11, setsh_fn)(ctx, AT(vs, 8, void *), NULL, 0);
                ctx = AT(holder, 0, void *);
                VT(ctx, 17, set1_fn)(ctx, AT(x, 0xc, void *));
                AT(holder, 0x2c, void *) = AT(x, 8, void *);
            } else {
                VT(ctx, 11, setsh_fn)(ctx, NULL, NULL, 0);
            }
            ctx = AT(holder, 0, void *);
            VT(ctx, 9, setsh_fn)(ctx, ps ? *ps : NULL, NULL, 0);
            AT(state, 0x9c, void *) = material + 8;
            AT(state, 0xc, void *) = x;
            last_material = material;
            bindings = AT(material, 0x14, uint8_t *);
            if (bindings) oa_bind_texture_table(AT(tables, 8, uint8_t *), NULL, (oa_state_cache *)state, (const oa_direct_layout *)(bindings + 0xc));
        }
        key = AT(p, 4, uint32_t);
        if (key != last_key) {
            uint8_t *t = AT(tables, 0, uint8_t *);
            void *rs = AT(t, 0x34 + (key >> 30) * 4, void *);
            void *bs = AT(t, ((key >> 24) & 0x3f) * 4, void *);
            void *ds = AT(tables, 4, void *);
            UINT stencil = key & 0xff;
            if (AT(state, 0x14, void *) != rs) {
                ctx = AT(holder, 0, void *);
                VT(ctx, 43, set1_fn)(ctx, AT(rs, 8, void *));
                AT(state, 0x14, void *) = rs;
            }
            if (AT(state, 0x10, void *) != bs) {
                float f = *(const float *)ABS(0x013be4a0);
                float factor[4];
                factor[0] = factor[1] = factor[2] = factor[3] = f;
                ctx = AT(holder, 0, void *);
                VT(ctx, 35, setblend_fn)(ctx, AT(bs, 8, void *), factor, 0xffffffffu);
                AT(state, 0x10, void *) = bs;
            }
            if (AT(state, 0x18, void *) != ds || AT(state, 0x180, UINT) != stencil) {
                ctx = AT(holder, 0, void *);
                VT(ctx, 36, set2_fn)(ctx, AT(ds, 8, void *), stencil);
                AT(state, 0x18, void *) = ds;
                AT(state, 0x180, UINT) = stencil;
            }
            last_key = key;
        }
        if (AT(p, 0x10, uint8_t *)) {
            uint8_t *obj = AT(p, 0x10, uint8_t *);
            void *layout = AT(p, 0xc, void *);
            uint8_t *mat_b = AT(material, 0x14, uint8_t *) + 0x30;
            void *data = cb_map(holder, AT(tables, 0x14, uint8_t *));
            fill_constants(data, AT(obj, 4, void *), mat_b, layout);
            AT(state, 0x15c, void *) = NULL;
            AT(state, 0x13c, void *) = NULL;
            cb_commit(holder, 0);
            oa_bind_material_textures((oa_state_cache *)state, scene, AT(obj, 8, const uint32_t *), (const oa_material_bindings *)(mat_b + 0xc), (const oa_binding_layout *)layout);
        }
        if (AT(p, 0x18, uint8_t *)) {
            uint8_t *obj = AT(p, 0x18, uint8_t *);
            void *data = cb_map(holder, AT(tables, 0xc, uint8_t *));
            memcpy(data, AT(obj, 4, void *), (size_t)AT(obj, 0, uint16_t) << 4);
            AT(state, 0x168, void *) = NULL;
            AT(state, 0x148, void *) = NULL;
            cb_commit(holder, 3);
            oa_bind_material_textures((oa_state_cache *)state, scene, AT(obj, 8, const uint32_t *), (const oa_material_bindings *)(AT(material, 0x14, uint8_t *) + 0x24), AT(p, 0x14, const oa_binding_layout *));
        } else {
            uint8_t *mb = AT(material, 0x14, uint8_t *);
            if (!mb || (AT(mb, 0x48, uint8_t) & 4)) {
                void *data = cb_map(holder, AT(tables, 0xc, uint8_t *));
                memset(data, 0, 0x90);
                AT(state, 0x168, void *) = NULL;
                AT(state, 0x148, void *) = NULL;
                cb_commit(holder, 3);
            }
        }
        if (AT(p, 0x20, uint8_t *)) {
            uint8_t *obj = AT(p, 0x20, uint8_t *);
            void *data = cb_map(holder, AT(tables, 0x10, uint8_t *));
            memcpy(data, AT(obj, 4, void *), (size_t)AT(obj, 0, uint16_t) << 4);
            AT(state, 0x16c, void *) = NULL;
            AT(state, 0x14c, void *) = NULL;
            cb_commit(holder, 4);
            if (AT(p, 0x1c, void *)) oa_bind_texture_ids((oa_state_cache *)state, scene, AT(obj, 8, const uint32_t *), AT(p, 0x1c, const oa_direct_layout *));
        }
        if (AT(p, 0x24, uint8_t *)) {
            uint8_t *obj = AT(p, 0x24, uint8_t *);
            size_t size = (size_t)AT(obj, 0, uint16_t) << 4;
            void *data = cb_map(holder, AT(tables, 0x1c, uint8_t *));
            if (copy_cb5) memcpy(data, AT(obj, 4, void *), size);
            else memset(data, 0, size);
            AT(state, 0x170, void *) = NULL;
            AT(state, 0x150, void *) = NULL;
            cb_commit(holder, 5);
        }
        pred = AT(p, 0x28, uint8_t *);
        ctx = AT(holder, 0, void *);
        if (pred && predication) {
            if (use_queries) VT(ctx, 27, set1_fn)(ctx, *(void **)pred);
            else VT(ctx, 30, set2_fn)(ctx, *(void **)pred, 0);
        }
        if (AT(p, 0, int) == 1) {
            InterlockedIncrement(&g_draw_kind[1]);
            draw_kind1(p, tables, state, holder);
        } else if (AT(p, 0, int) == 2) {
            InterlockedIncrement(&g_draw_kind[2]);
            draw_kind2(p, holder);
        } else if (AT(p, 0, int) == 0) {
            uint8_t *g = AT(p, 0x2c, uint8_t *);
            uint8_t *strides = AT(holder, 0x2c, uint8_t *);
            void *vb[2];
            UINT stride[2], offset[2];
            void *ib = AT(g, 0x14, void *);
            InterlockedIncrement(&g_draw_kind[0]);
            vb[0] = AT(g, 0xc, void *);
            vb[1] = AT(AT(tables, 0x20, uint8_t *), 4, void *);
            stride[0] = AT(strides, 0xd8, UINT);
            stride[1] = AT(strides, 0xdc, UINT);
            offset[0] = offset[1] = 0;
            VT(ctx, 18, setvb_fn)(ctx, 0, 2, vb, stride, offset);
            ctx = AT(holder, 0, void *);
            VT(ctx, 24, settopo_fn)(ctx, AT(g, 0x2c, UINT));
            ctx = AT(holder, 0, void *);
            if (ib) {
                VT(ctx, 19, setib_fn)(ctx, ib, AT(g, 0x28, UINT), 0);
                ctx = AT(holder, 0, void *);
                VT(ctx, 12, drawi_fn)(ctx, AT(g, 0x18, UINT), 0, 0);
            } else {
                VT(ctx, 13, draw_fn)(ctx, AT(g, 0x10, UINT), 0);
            }
        }
        if (pred && predication) {
            ctx = AT(holder, 0, void *);
            if (use_queries) VT(ctx, 28, set1_fn)(ctx, *(void **)pred);
            else VT(ctx, 30, set2_fn)(ctx, NULL, 0);
        }
    }
}

typedef struct {
    uint32_t address;
    const char *name;
    void *replacement;
    uint8_t expect[16];
    volatile LONG *calls;
    int applied;
    uint8_t reloc_from, reloc_to; /* bytes holding an absolute address, rewritten at load under ASLR: not compared */
} oa_patch;

static int bytes_match(const oa_patch *p, const uint8_t *at) {
    int i;
    for (i = 0; i < (int)sizeof(p->expect); i++)
        if ((i < p->reloc_from || i >= p->reloc_to) && at[i] != p->expect[i]) return 0;
    return 1;
}

static oa_patch g_patches[] = {
    {0x010596c0, "texture_unmap", (void *)oa_texture_unmap, {0x8b, 0x4c, 0x24, 0x08, 0x8b, 0x44, 0x24, 0x04, 0x8b, 0x00, 0x8b, 0x10, 0x8b, 0x52, 0x3c, 0x56}, &g_calls_unmap, 0},
    {0x00c5b2a0, "bind_material_textures", (void *)oa_bind_material_textures, {0x8b, 0x4c, 0x24, 0x14, 0x83, 0xec, 0x08, 0x55, 0x33, 0xc0, 0x33, 0xed, 0x66, 0x3b, 0x41, 0x02}, &g_calls_bind, 0},
    {0x00c5b390, "bind_texture_ids", (void *)oa_bind_texture_ids, {0x8b, 0x44, 0x24, 0x10, 0x83, 0xec, 0x08, 0x55, 0x33, 0xed, 0x39, 0x28, 0x0f, 0x86, 0xbf, 0x00}, &g_calls_bind_ids, 0},
    {0x00c726d0, "bind_texture_table", (void *)oa_bind_texture_table, {0x83, 0xec, 0x08, 0x55, 0x8b, 0x6c, 0x24, 0x14, 0x33, 0xd2, 0x89, 0x4c, 0x24, 0x08, 0x89, 0x54}, &g_calls_bind_table, 0},
    {0x00c961e0, "draw_packets", (void *)oa_draw_packets, {0x81, 0xec, 0x50, 0x01, 0x00, 0x00, 0xa1, 0x3c, 0x71, 0x97, 0x01, 0x33, 0xc4, 0x89, 0x84, 0x24}, &g_calls_draw, 0, 7, 11},
};

void oa_engine_install(void (*log)(const char *, ...)) {
    uintptr_t base = (uintptr_t)GetModuleHandleA(NULL);
    char off[8];
    size_t i;
    g_base = base;
    if (GetEnvironmentVariableA("OA_NO_REPLACE", off, sizeof(off)) && off[0] == '1') {
        log("engine replacements disabled");
        return;
    }
    for (i = 0; i < sizeof(g_patches) / sizeof(g_patches[0]); i++) {
        oa_patch *p = &g_patches[i];
        uint8_t *at = (uint8_t *)(base + p->address - IMAGE_BASE);
        DWORD old;
        if (!bytes_match(p, at)) {
            log("replace %s skipped: bytes differ", p->name);
            continue;
        }
        if (!VirtualProtect(at, 5, PAGE_EXECUTE_READWRITE, &old)) {
            log("replace %s skipped: protect failed", p->name);
            continue;
        }
        at[0] = 0xE9;
        *(int32_t *)(at + 1) = (int32_t)((uint8_t *)p->replacement - (at + 5));
        VirtualProtect(at, 5, old, &old);
        FlushInstructionCache(GetCurrentProcess(), at, 5);
        p->applied = 1;
        log("replace %s applied at %08x", p->name, p->address);
    }
}

void oa_engine_report(const char *path) {
    FILE *f = fopen(path, "w");
    size_t i;
    if (!f) return;
    for (i = 0; i < sizeof(g_patches) / sizeof(g_patches[0]); i++)
        fprintf(f, "%08x %s applied=%d calls=%ld\n", g_patches[i].address, g_patches[i].name, g_patches[i].applied, *g_patches[i].calls);
    fprintf(f, "draw packets kind0=%ld kind1=%ld kind2=%ld\n", g_draw_kind[0], g_draw_kind[1], g_draw_kind[2]);
    fprintf(f, "immediate quads=%ld split=%ld ring_wraps=%ld skipped=%ld\n", g_imm_quads, g_imm_split, g_imm_discard, g_imm_skipped);
    fclose(f);
}
