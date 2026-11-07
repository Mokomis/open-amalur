/* oa_dxbc.c: Shader Model 4 bytecode to SPIR-V 1.0. Covers the instructions koa.exe's shaders use; anything else fails with a named error. */
#include "oa_dxbc.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* SPIR-V opcodes */
enum {
    OpExtInstImport = 11, OpExtInst = 12, OpMemoryModel = 14, OpEntryPoint = 15, OpExecutionMode = 16, OpCapability = 17,
    OpTypeVoid = 19, OpTypeBool = 20, OpTypeInt = 21, OpTypeFloat = 22, OpTypeVector = 23, OpTypeImage = 25, OpTypeSampler = 26,
    OpTypeSampledImage = 27, OpTypeArray = 28, OpTypeStruct = 30, OpTypePointer = 32, OpTypeFunction = 33, OpConstant = 43,
    OpConstantComposite = 44, OpFunction = 54, OpFunctionEnd = 56, OpVariable = 59, OpLoad = 61, OpStore = 62, OpAccessChain = 65,
    OpDecorate = 71, OpMemberDecorate = 72, OpVectorShuffle = 79, OpCompositeConstruct = 80, OpCompositeExtract = 81,
    OpCompositeInsert = 82, OpSampledImage = 86, OpImageSampleImplicitLod = 87, OpImageSampleExplicitLod = 88,
    OpImageSampleDrefImplicitLod = 89, OpImageFetch = 95, OpConvertFToU = 109, OpConvertFToS = 110, OpConvertSToF = 111,
    OpConvertUToF = 112, OpBitcast = 124, OpSNegate = 126, OpFNegate = 127, OpIAdd = 128, OpFAdd = 129, OpFMul = 133, OpIMul = 132,
    OpFDiv = 136, OpDot = 148, OpAny = 154, OpSelect = 169, OpIEqual = 170, OpINotEqual = 171, OpSGreaterThanEqual = 175,
    OpSLessThan = 177, OpUGreaterThanEqual = 174, OpULessThan = 176, OpFOrdEqual = 180, OpFUnordNotEqual = 183, OpFOrdLessThan = 184,
    OpFOrdGreaterThanEqual = 190, OpShiftRightLogical = 194, OpShiftRightArithmetic = 195, OpShiftLeftLogical = 196, OpBitwiseOr = 197,
    OpBitwiseXor = 198, OpBitwiseAnd = 199, OpNot = 200, OpDPdx = 207, OpDPdy = 208, OpLoopMerge = 246, OpSelectionMerge = 247,
    OpLabel = 248, OpBranch = 249, OpBranchConditional = 250, OpKill = 252, OpReturn = 253
};
/* GLSL.std.450 */
enum { G_RoundEven = 2, G_Trunc = 3, G_FAbs = 4, G_SAbs = 5, G_Floor = 8, G_Ceil = 9, G_Fract = 10, G_Sin = 13, G_Cos = 14, G_Exp2 = 29, G_Log2 = 30, G_Sqrt = 31, G_InverseSqrt = 32, G_FMin = 37, G_UMin = 38, G_SMin = 39, G_FMax = 40, G_UMax = 41, G_SMax = 42, G_FClamp = 43 };
/* Storage classes, decorations, builtins */
enum { SC_UniformConstant = 0, SC_Input = 1, SC_Uniform = 2, SC_Output = 3, SC_Function = 7 };
enum { D_Block = 2, D_ArrayStride = 6, D_BuiltIn = 11, D_NoPerspective = 13, D_Flat = 14, D_Centroid = 16, D_Location = 30, D_Binding = 33, D_DescriptorSet = 34, D_Offset = 35 };
enum { B_Position = 0, B_FragCoord = 15, B_FragDepth = 22 };

/* SM4 opcodes */
enum {
    S_ADD = 0, S_AND = 1, S_BREAK = 2, S_BREAKC = 3, S_CUT = 9, S_DERIV_RTX = 11, S_DERIV_RTY = 12, S_DISCARD = 13, S_DIV = 14, S_DP2 = 15, S_DP3 = 16, S_DP4 = 17,
    S_ELSE = 18, S_ENDIF = 21, S_ENDLOOP = 22, S_EQ = 24, S_EXP = 25, S_FRC = 26, S_FTOI = 27, S_FTOU = 28, S_GE = 29, S_IADD = 30, S_IF = 31, S_IEQ = 32, S_IGE = 33,
    S_ILT = 34, S_IMAD = 35, S_IMAX = 36, S_IMIN = 37, S_IMUL = 38, S_INE = 39, S_INEG = 40, S_ISHL = 41, S_ISHR = 42, S_ITOF = 43, S_LD = 45, S_LOG = 47, S_LOOP = 48,
    S_LT = 49, S_MAD = 50, S_MIN = 51, S_MAX = 52, S_CUSTOMDATA = 53, S_MOV = 54, S_MOVC = 55, S_MUL = 56, S_NE = 57, S_NOP = 58, S_NOT = 59, S_OR = 60, S_RET = 62,
    S_ROUND_NE = 64, S_ROUND_NI = 65, S_ROUND_PI = 66, S_ROUND_Z = 67, S_RSQ = 68, S_SAMPLE = 69, S_SAMPLE_C = 70, S_SAMPLE_L = 72, S_SQRT = 75, S_SINCOS = 77, S_ULT = 79,
    S_UGE = 80, S_UMAX = 83, S_UMIN = 84, S_USHR = 85, S_UTOF = 86, S_XOR = 87, S_DCL_RESOURCE = 88, S_DCL_CB = 89, S_DCL_SAMPLER = 90, S_DCL_INPUT = 95,
    S_DCL_INPUT_SGV = 96, S_DCL_INPUT_SIV = 97, S_DCL_INPUT_PS = 98, S_DCL_INPUT_PS_SGV = 99, S_DCL_INPUT_PS_SIV = 100, S_DCL_OUTPUT = 101, S_DCL_OUTPUT_SGV = 102,
    S_DCL_OUTPUT_SIV = 103, S_DCL_TEMPS = 104, S_DCL_GLOBAL_FLAGS = 106
};
/* SM4 operand types */
enum { R_TEMP = 0, R_INPUT = 1, R_OUTPUT = 2, R_IMM32 = 4, R_SAMPLER = 6, R_RESOURCE = 7, R_CB = 8, R_DEPTH = 12, R_NULL = 13 };

enum { K_FLOAT, K_INT, K_UINT };

typedef struct { uint32_t *w; size_t n, cap; } section;

typedef struct {
    uint32_t type, ncomp, mode, mask, swz[4], modifier;
    uint32_t imm[4];
    uint32_t index[3], has_rel[3], rel_id[3];
} operand;

#define MAX_CACHE 512
typedef struct {
    section head, entry, exec, annot, types, vars, code;
    uint32_t next_id, glsl, void_t, func_t;
    uint32_t scalar[3], vec2[3], vec3[3], vec4[3], bool_t, bvec4, bvec2, bvec3;
    struct { uint32_t sc, t, id; } ptrs[64];
    int nptrs;
    struct { uint32_t t, v, id; } consts[MAX_CACHE];
    int nconsts;
    struct { uint32_t t, a, b, c, d, id; } comps[MAX_CACHE];
    int ncomps;
    uint32_t temps[256], ntemps;
    uint32_t in_vars[32], in_kind[32], in_is_pos[32], out_vars[32], depth_var;
    uint32_t cb_vars[16], tex_vars[32], tex_types[32], si_types[32], tex_kind[32], sampler_vars[16], sampler_t;
    uint32_t iface[64], niface;
    uint32_t depth_tex; /* t# used with sample_c */
    struct { uint32_t kind, sd, depth, img, si; } images[16];
    int nimages, has_1d;
    uint32_t icb_var;
    oa_shader_info *info;
    const uint32_t *t; size_t tn, pc;
    uint32_t loop_merge[32], loop_cont[32], loop_head[32]; int loop_depth;
    uint32_t if_end[32], if_else[32]; int if_depth;
    int block_open, failed;
    char *err; size_t err_size;
} ctx;

static void fail(ctx *c, const char *fmt, ...) {
    va_list a;
    if (c->failed) return;
    c->failed = 1;
    va_start(a, fmt);
    vsnprintf(c->err, c->err_size, fmt, a);
    va_end(a);
}

static void put(section *s, uint32_t v) {
    if (s->n == s->cap) {
        s->cap = s->cap ? s->cap * 2 : 256;
        s->w = realloc(s->w, s->cap * 4);
    }
    s->w[s->n++] = v;
}
static void ins(section *s, uint32_t op, int count, ...) {
    va_list a;
    int i;
    put(s, op | ((uint32_t)(count + 1) << 16));
    va_start(a, count);
    for (i = 0; i < count; i++) put(s, va_arg(a, uint32_t));
    va_end(a);
}
#define U(x) ((uint32_t)(x))
static uint32_t id(ctx *c) { return c->next_id++; }

static uint32_t str_words(section *s, const char *x) {
    size_t n = strlen(x) + 1, i;
    uint32_t words = (uint32_t)((n + 3) / 4);
    for (i = 0; i < words; i++) {
        uint32_t w = 0;
        size_t j;
        for (j = 0; j < 4 && i * 4 + j < n; j++) w |= (uint32_t)(uint8_t)x[i * 4 + j] << (j * 8);
        put(s, w);
    }
    return words;
}

static uint32_t vec_t(ctx *c, int kind, int n) { return n == 1 ? c->scalar[kind] : n == 2 ? c->vec2[kind] : n == 3 ? c->vec3[kind] : c->vec4[kind]; }

static uint32_t ptr_t(ctx *c, uint32_t sc, uint32_t t) {
    int i;
    uint32_t r;
    for (i = 0; i < c->nptrs; i++)
        if (c->ptrs[i].sc == sc && c->ptrs[i].t == t) return c->ptrs[i].id;
    r = id(c);
    ins(&c->types, OpTypePointer, 3, r, sc, t);
    c->ptrs[c->nptrs].sc = sc;
    c->ptrs[c->nptrs].t = t;
    c->ptrs[c->nptrs++].id = r;
    return r;
}

static uint32_t const_t(ctx *c, uint32_t t, uint32_t v) {
    int i;
    uint32_t r;
    for (i = 0; i < c->nconsts; i++)
        if (c->consts[i].t == t && c->consts[i].v == v) return c->consts[i].id;
    r = id(c);
    ins(&c->types, OpConstant, 3, t, r, v);
    if (c->nconsts < MAX_CACHE) {
        c->consts[c->nconsts].t = t;
        c->consts[c->nconsts].v = v;
        c->consts[c->nconsts++].id = r;
    }
    return r;
}
static uint32_t cuint(ctx *c, uint32_t v) { return const_t(c, c->scalar[K_UINT], v); }
static uint32_t cfloat(ctx *c, float f) {
    uint32_t v;
    memcpy(&v, &f, 4);
    return const_t(c, c->scalar[K_FLOAT], v);
}

static uint32_t const_vec4(ctx *c, int kind, const uint32_t *v) {
    int i;
    uint32_t t = c->vec4[kind], a = const_t(c, c->scalar[kind], v[0]), b = const_t(c, c->scalar[kind], v[1]), d = const_t(c, c->scalar[kind], v[2]), e = const_t(c, c->scalar[kind], v[3]), r;
    for (i = 0; i < c->ncomps; i++)
        if (c->comps[i].t == t && c->comps[i].a == a && c->comps[i].b == b && c->comps[i].c == d && c->comps[i].d == e) return c->comps[i].id;
    r = id(c);
    ins(&c->types, OpConstantComposite, 6, t, r, a, b, d, e);
    if (c->ncomps < MAX_CACHE) {
        c->comps[c->ncomps].t = t;
        c->comps[c->ncomps].a = a;
        c->comps[c->ncomps].b = b;
        c->comps[c->ncomps].c = d;
        c->comps[c->ncomps].d = e;
        c->comps[c->ncomps++].id = r;
    }
    return r;
}

static uint32_t splat(ctx *c, int kind, uint32_t v) {
    uint32_t x[4];
    x[0] = x[1] = x[2] = x[3] = v;
    return const_vec4(c, kind, x);
}

static uint32_t bitcast(ctx *c, uint32_t v, int from, int to, int n) {
    uint32_t r;
    if (from == to) return v;
    r = id(c);
    ins(&c->code, OpBitcast, 3, vec_t(c, to, n), r, v);
    return r;
}

static uint32_t ext1(ctx *c, uint32_t t, uint32_t fn, uint32_t a) {
    uint32_t r = id(c);
    ins(&c->code, OpExtInst, 5, t, r, c->glsl, fn, a);
    return r;
}
static uint32_t ext2(ctx *c, uint32_t t, uint32_t fn, uint32_t a, uint32_t b) {
    uint32_t r = id(c);
    ins(&c->code, OpExtInst, 6, t, r, c->glsl, fn, a, b);
    return r;
}
static uint32_t bin(ctx *c, uint32_t op, uint32_t t, uint32_t a, uint32_t b) {
    uint32_t r = id(c);
    ins(&c->code, op, 4, t, r, a, b);
    return r;
}
static uint32_t un(ctx *c, uint32_t op, uint32_t t, uint32_t a) {
    uint32_t r = id(c);
    ins(&c->code, op, 3, t, r, a);
    return r;
}

static uint32_t next_word(ctx *c) {
    if (c->pc >= c->tn) {
        fail(c, "ran off the end of the shader");
        return 0;
    }
    return c->t[c->pc++];
}

static uint32_t load_raw(ctx *c, operand *o);

static void parse_operand(ctx *c, operand *o) {
    uint32_t w = next_word(c), dim, i, rep[3];
    memset(o, 0, sizeof(*o));
    o->ncomp = w & 3;
    o->mode = (w >> 2) & 3;
    o->mask = 0xf;
    o->swz[0] = 0; o->swz[1] = 1; o->swz[2] = 2; o->swz[3] = 3;
    if (o->ncomp == 2) {
        if (o->mode == 0) o->mask = (w >> 4) & 0xf;
        else if (o->mode == 1) { for (i = 0; i < 4; i++) o->swz[i] = (w >> (4 + 2 * i)) & 3; }
        else if (o->mode == 2) { uint32_t s = (w >> 4) & 3; o->swz[0] = o->swz[1] = o->swz[2] = o->swz[3] = s; }
    }
    o->type = (w >> 12) & 0xff;
    dim = (w >> 20) & 3;
    rep[0] = (w >> 22) & 7; rep[1] = (w >> 25) & 7; rep[2] = (w >> 28) & 7;
    if (w >> 31) {
        uint32_t e = next_word(c);
        if ((e & 0x3f) == 1) o->modifier = (e >> 6) & 0xff;
    }
    if (o->type == R_IMM32) {
        if (o->ncomp == 1) o->imm[0] = o->imm[1] = o->imm[2] = o->imm[3] = next_word(c);
        else for (i = 0; i < 4; i++) o->imm[i] = next_word(c);
        return;
    }
    for (i = 0; i < dim; i++) {
        if (rep[i] == 0) o->index[i] = next_word(c);
        else if (rep[i] == 2 || rep[i] == 3) {
            operand r;
            if (rep[i] == 3) o->index[i] = next_word(c);
            parse_operand(c, &r);
            o->has_rel[i] = 1;
            {
                uint32_t raw = load_raw(c, &r), u = bitcast(c, raw, K_FLOAT, K_UINT, 4), e = id(c);
                ins(&c->code, OpCompositeExtract, 4, c->scalar[K_UINT], e, u, r.swz[0]);
                o->rel_id[i] = e;
            }
        } else fail(c, "unsupported index representation %u", rep[i]);
    }
}

/* Load a whole register as a float vec4, without swizzle or modifiers. */
static uint32_t load_raw(ctx *c, operand *o) {
    uint32_t r = id(c);
    switch (o->type) {
    case R_TEMP:
        if (o->index[0] >= c->ntemps) { fail(c, "temp r%u not declared", o->index[0]); return r; }
        ins(&c->code, OpLoad, 3, c->vec4[K_FLOAT], r, c->temps[o->index[0]]);
        return r;
    case R_INPUT: {
        uint32_t i = o->index[0];
        if (i >= 32 || !c->in_vars[i]) { fail(c, "input v%u not declared", i); return r; }
        ins(&c->code, OpLoad, 3, c->vec4[c->in_kind[i]], r, c->in_vars[i]);
        if (c->in_is_pos[i]) {
            /* D3D gives w, Vulkan gives 1/w. */
            uint32_t w = id(c), rw;
            ins(&c->code, OpCompositeExtract, 4, c->scalar[K_FLOAT], w, r, 3);
            rw = bin(c, OpFDiv, c->scalar[K_FLOAT], cfloat(c, 1.0f), w);
            {
                uint32_t out = id(c);
                ins(&c->code, OpCompositeInsert, 5, c->vec4[K_FLOAT], out, rw, r, 3);
                return out;
            }
        }
        return bitcast(c, r, c->in_kind[i], K_FLOAT, 4);
    }
    case R_OUTPUT:
        if (o->index[0] >= 32 || !c->out_vars[o->index[0]]) { fail(c, "output o%u not declared", o->index[0]); return r; }
        ins(&c->code, OpLoad, 3, c->vec4[K_FLOAT], r, c->out_vars[o->index[0]]);
        return r;
    case 9: { /* immediate constant buffer */
        uint32_t idx = cuint(c, o->index[0]), p;
        if (!c->icb_var) { fail(c, "immediate constants not declared"); return r; }
        if (o->has_rel[0]) idx = o->index[0] ? bin(c, OpIAdd, c->scalar[K_UINT], o->rel_id[0], idx) : o->rel_id[0];
        p = id(c);
        ins(&c->code, OpAccessChain, 4, ptr_t(c, 6, c->vec4[K_FLOAT]), p, c->icb_var, idx);
        ins(&c->code, OpLoad, 3, c->vec4[K_FLOAT], r, p);
        return r;
    }
    case R_CB: {
        uint32_t slot = o->index[0], idx, p;
        if (slot >= 16 || !c->cb_vars[slot]) { fail(c, "cb%u not declared", slot); return r; }
        idx = cuint(c, o->index[1]);
        if (o->has_rel[1]) idx = o->index[1] ? bin(c, OpIAdd, c->scalar[K_UINT], o->rel_id[1], idx) : o->rel_id[1];
        p = id(c);
        ins(&c->code, OpAccessChain, 5, ptr_t(c, SC_Uniform, c->vec4[K_FLOAT]), p, c->cb_vars[slot], cuint(c, 0), idx);
        ins(&c->code, OpLoad, 3, c->vec4[K_FLOAT], r, p);
        return r;
    }
    default:
        fail(c, "cannot read operand type %u", o->type);
        return r;
    }
}

static int is_identity(const uint32_t *s) { return s[0] == 0 && s[1] == 1 && s[2] == 2 && s[3] == 3; }

static uint32_t swizzled(ctx *c, uint32_t t, uint32_t v, const uint32_t *s) {
    uint32_t r;
    if (is_identity(s)) return v;
    r = id(c);
    ins(&c->code, OpVectorShuffle, 8, t, r, v, v, s[0], s[1], s[2], s[3]);
    return r;
}

/* Read a source operand as a 4-component value of the given kind, with swizzle and modifiers. */
static uint32_t load_src(ctx *c, operand *o, int kind) {
    uint32_t t = c->vec4[kind], v;
    if (o->type == R_IMM32) {
        uint32_t s[4], i;
        for (i = 0; i < 4; i++) s[i] = o->imm[o->swz[i]];
        v = const_vec4(c, kind, s);
    } else {
        v = bitcast(c, load_raw(c, o), K_FLOAT, kind, 4);
        v = swizzled(c, t, v, o->swz);
    }
    if (o->modifier == 2 || o->modifier == 3) v = ext1(c, t, kind == K_FLOAT ? G_FAbs : G_SAbs, kind == K_UINT ? bitcast(c, v, K_UINT, K_INT, 4) : v);
    if (o->modifier == 1 || o->modifier == 3) v = un(c, kind == K_FLOAT ? OpFNegate : OpSNegate, t, v);
    return v;
}

static void store_dst(ctx *c, operand *o, uint32_t v, int kind, int saturate) {
    uint32_t var, f, t = c->vec4[K_FLOAT];
    if (o->type == R_NULL) return;
    f = bitcast(c, v, kind, K_FLOAT, 4);
    if (saturate) {
        uint32_t r = id(c), lo = splat(c, K_FLOAT, 0), hi = splat(c, K_FLOAT, 0x3f800000);
        ins(&c->code, OpExtInst, 7, t, r, c->glsl, U(G_FClamp), f, lo, hi);
        f = r;
    }
    if (o->type == R_DEPTH) {
        uint32_t e = id(c);
        ins(&c->code, OpCompositeExtract, 4, c->scalar[K_FLOAT], e, f, 0);
        ins(&c->code, OpStore, 2, c->depth_var, e);
        return;
    }
    if (o->type == R_TEMP) {
        if (o->index[0] >= c->ntemps) { fail(c, "temp r%u not declared", o->index[0]); return; }
        var = c->temps[o->index[0]];
    } else if (o->type == R_OUTPUT) {
        if (o->index[0] >= 32 || !c->out_vars[o->index[0]]) { fail(c, "output o%u not declared", o->index[0]); return; }
        var = c->out_vars[o->index[0]];
    } else {
        fail(c, "cannot write operand type %u", o->type);
        return;
    }
    if (o->mask != 0xf) {
        uint32_t old = id(c), r = id(c), i, s[4];
        ins(&c->code, OpLoad, 3, t, old, var);
        for (i = 0; i < 4; i++) s[i] = (o->mask >> i & 1) ? 4 + i : i;
        ins(&c->code, OpVectorShuffle, 8, t, r, old, f, s[0], s[1], s[2], s[3]);
        f = r;
    }
    ins(&c->code, OpStore, 2, var, f);
}

/* First component of a source operand as a bool, for test_nz or test_z. */
static uint32_t cond_of(ctx *c, operand *o, int nonzero) {
    uint32_t v = load_src(c, o, K_UINT), e = id(c);
    ins(&c->code, OpCompositeExtract, 4, c->scalar[K_UINT], e, v, 0);
    return bin(c, nonzero ? OpINotEqual : OpIEqual, c->bool_t, e, cuint(c, 0));
}

static uint32_t compare(ctx *c, uint32_t op, uint32_t a, uint32_t b) {
    uint32_t bv = bin(c, op, c->bvec4, a, b), r = id(c);
    ins(&c->code, OpSelect, 5, c->vec4[K_UINT], r, bv, splat(c, K_UINT, 0xffffffffu), splat(c, K_UINT, 0));
    return r;
}

static uint32_t shuffle_to(ctx *c, uint32_t v, int n) {
    uint32_t r = id(c);
    if (n == 2) ins(&c->code, OpVectorShuffle, 6, c->vec2[K_FLOAT], r, v, v, 0, 1);
    else ins(&c->code, OpVectorShuffle, 7, c->vec3[K_FLOAT], r, v, v, 0, 1, 2);
    return r;
}

static uint32_t vec4_of(ctx *c, uint32_t s) {
    uint32_t r = id(c);
    ins(&c->code, OpCompositeConstruct, 6, c->vec4[K_FLOAT], r, s, s, s, s);
    return r;
}

static const char *sig_chunk(const uint8_t *d, size_t size, const char *tag, uint32_t *len) {
    uint32_t n, i;
    if (size < 32) return NULL;
    memcpy(&n, d + 28, 4);
    for (i = 0; i < n; i++) {
        uint32_t off;
        if (32 + 4 * (size_t)i + 4 > size) return NULL;
        memcpy(&off, d + 32 + 4 * i, 4);
        if ((size_t)off + 8 > size) return NULL;
        if (!memcmp(d + off, tag, 4)) {
            memcpy(len, d + off + 4, 4);
            return (const char *)d + off + 8;
        }
    }
    return NULL;
}

static int read_sig(const char *p, uint32_t len, oa_sig_element *out) {
    uint32_t n, i;
    if (!p || len < 8) return 0;
    memcpy(&n, p, 4);
    if (n > OA_MAX_SIG) n = OA_MAX_SIG;
    for (i = 0; i < n; i++) {
        uint32_t f[6];
        memcpy(f, p + 8 + 24 * i, 24);
        snprintf(out[i].name, sizeof(out[i].name), "%s", p + f[0]);
        out[i].semantic_index = f[1];
        out[i].sysval = f[2];
        out[i].comp_type = f[3];
        out[i].reg = f[4];
        out[i].mask = f[5] & 0xff;
    }
    return (int)n;
}

static uint32_t declare_var(ctx *c, uint32_t type, uint32_t sc) {
    uint32_t r = id(c);
    ins(&c->types, OpVariable, 3, ptr_t(c, sc, type), r, sc);
    if ((sc == SC_Input || sc == SC_Output) && c->niface < 64) c->iface[c->niface++] = r;
    return r;
}

static void dcl_input(ctx *c, uint32_t w, uint32_t op) {
    operand o;
    uint32_t reg, interp = (w >> 11) & 0xf, kind = K_FLOAT, sys = 0, i;
    parse_operand(c, &o);
    reg = o.index[0];
    if (op == S_DCL_INPUT_SIV || op == S_DCL_INPUT_SGV || op == S_DCL_INPUT_PS_SIV || op == S_DCL_INPUT_PS_SGV) sys = next_word(c);
    if (o.type != R_INPUT || reg >= 32) { if (o.type != R_INPUT) fail(c, "unsupported input operand type %u", o.type); return; }
    if (c->in_vars[reg]) return;
    if (!c->info->is_pixel) {
        for (i = 0; i < (uint32_t)c->info->input_count; i++)
            if (c->info->inputs[i].reg == reg) kind = c->info->inputs[i].comp_type == 1 ? K_UINT : c->info->inputs[i].comp_type == 2 ? K_INT : K_FLOAT;
    }
    c->in_kind[reg] = kind;
    c->in_vars[reg] = declare_var(c, c->vec4[kind], SC_Input);
    if (op == S_DCL_INPUT_PS_SIV && sys == 1) {
        c->in_is_pos[reg] = 1;
        ins(&c->annot, OpDecorate, 3, c->in_vars[reg], U(D_BuiltIn), U(B_FragCoord));
        return;
    }
    if (sys) { fail(c, "unsupported input system value %u", sys); return; }
    ins(&c->annot, OpDecorate, 3, c->in_vars[reg], U(D_Location), reg);
    if (op == S_DCL_INPUT_PS) {
        if (interp == 1) ins(&c->annot, OpDecorate, 2, c->in_vars[reg], U(D_Flat));
        else if (interp == 3 || interp == 5) ins(&c->annot, OpDecorate, 2, c->in_vars[reg], U(D_Centroid));
        if (interp == 4 || interp == 5) ins(&c->annot, OpDecorate, 2, c->in_vars[reg], U(D_NoPerspective));
    }
}

static void dcl_output(ctx *c, uint32_t op) {
    operand o;
    uint32_t reg, sys = 0;
    parse_operand(c, &o);
    if (op == S_DCL_OUTPUT_SIV || op == S_DCL_OUTPUT_SGV) sys = next_word(c);
    if (o.type == R_DEPTH) {
        c->depth_var = declare_var(c, c->scalar[K_FLOAT], SC_Output);
        ins(&c->annot, OpDecorate, 3, c->depth_var, U(D_BuiltIn), U(B_FragDepth));
        c->info->writes_depth = 1;
        return;
    }
    if (o.type != R_OUTPUT) { fail(c, "unsupported output operand type %u", o.type); return; }
    reg = o.index[0];
    if (reg >= 32 || c->out_vars[reg]) return;
    c->out_vars[reg] = declare_var(c, c->vec4[K_FLOAT], SC_Output);
    if (sys == 1) ins(&c->annot, OpDecorate, 3, c->out_vars[reg], U(D_BuiltIn), U(B_Position));
    else if (sys) fail(c, "unsupported output system value %u", sys);
    else ins(&c->annot, OpDecorate, 3, c->out_vars[reg], U(D_Location), reg);
}

static void dcl_cb(ctx *c) {
    operand o;
    uint32_t slot, n, arr, st, var, base = c->info->binding_base;
    parse_operand(c, &o);
    slot = o.index[0];
    n = o.index[1];
    if (slot >= 16) { fail(c, "cb%u out of range", slot); return; }
    if (n == 0) n = 1;
    arr = id(c);
    ins(&c->types, OpTypeArray, 3, arr, c->vec4[K_FLOAT], cuint(c, n));
    ins(&c->annot, OpDecorate, 3, arr, U(D_ArrayStride), U(16));
    st = id(c);
    ins(&c->types, OpTypeStruct, 2, st, arr);
    ins(&c->annot, OpDecorate, 2, st, U(D_Block));
    ins(&c->annot, OpMemberDecorate, 4, st, U(0), U(D_Offset), U(0));
    var = declare_var(c, st, SC_Uniform);
    ins(&c->annot, OpDecorate, 3, var, U(D_DescriptorSet), U(0));
    ins(&c->annot, OpDecorate, 3, var, U(D_Binding), base + OA_BIND_CB + slot);
    c->cb_vars[slot] = var;
    c->info->cb_mask |= (uint16_t)(1u << slot);
    c->info->cb_sizes[slot] = n * 16;
}

static void dcl_resource(ctx *c, uint32_t w) {
    operand o;
    uint32_t slot, dim = (w >> 11) & 0x1f, ret, kind, sd, img, si, var, base = c->info->binding_base;
    parse_operand(c, &o);
    ret = next_word(c);
    slot = o.index[0];
    if (slot >= 32) { fail(c, "t%u out of range", slot); return; }
    switch (dim) {
    case 2: sd = 0; break;
    case 3: sd = 1; break;
    case 5: sd = 2; break;
    case 6: sd = 3; break;
    default: fail(c, "unsupported resource dimension %u", dim); return;
    }
    if (sd == 0 && !c->has_1d) { c->has_1d = 1; ins(&c->head, OpCapability, 1, U(43)); } /* Sampled1D */
    kind = (ret & 0xf) == 3 ? K_INT : (ret & 0xf) == 4 ? K_UINT : K_FLOAT;
    {
        uint32_t depth = c->depth_tex >> slot & 1;
        int i;
        img = 0;
        for (i = 0; i < c->nimages; i++)
            if (c->images[i].kind == kind && c->images[i].sd == sd && c->images[i].depth == depth) { img = c->images[i].img; si = c->images[i].si; }
        if (!img) {
            img = id(c);
            ins(&c->types, OpTypeImage, 8, img, c->scalar[kind], sd, depth, U(0), U(0), U(1), U(0));
            si = id(c);
            ins(&c->types, OpTypeSampledImage, 2, si, img);
            if (c->nimages < 16) {
                c->images[c->nimages].kind = kind; c->images[c->nimages].sd = sd; c->images[c->nimages].depth = depth;
                c->images[c->nimages].img = img; c->images[c->nimages++].si = si;
            }
        }
    }
    var = declare_var(c, img, SC_UniformConstant);
    ins(&c->annot, OpDecorate, 3, var, U(D_DescriptorSet), U(0));
    ins(&c->annot, OpDecorate, 3, var, U(D_Binding), base + OA_BIND_TEXTURE + slot);
    c->tex_vars[slot] = var;
    c->tex_types[slot] = img;
    c->si_types[slot] = si;
    c->tex_kind[slot] = kind;
    c->info->texture_mask |= 1u << slot;
    c->info->texture_dim[slot] = (uint8_t)dim;
}

static void dcl_sampler(ctx *c) {
    operand o;
    uint32_t slot, var, base = c->info->binding_base;
    parse_operand(c, &o);
    slot = o.index[0];
    if (slot >= 16) { fail(c, "s%u out of range", slot); return; }
    var = declare_var(c, c->sampler_t, SC_UniformConstant);
    ins(&c->annot, OpDecorate, 3, var, U(D_DescriptorSet), U(0));
    ins(&c->annot, OpDecorate, 3, var, U(D_Binding), base + OA_BIND_SAMPLER + slot);
    c->sampler_vars[slot] = var;
    c->info->sampler_mask |= (uint16_t)(1u << slot);
}

static int coord_size(uint32_t dim) { return dim == 2 ? 1 : dim == 3 ? 2 : 3; }

static uint32_t coord_of(ctx *c, uint32_t v, int kind, int n) {
    uint32_t r = id(c);
    if (n == 1) ins(&c->code, OpCompositeExtract, 4, c->scalar[kind], r, v, 0);
    else if (n == 2) ins(&c->code, OpVectorShuffle, 6, c->vec2[kind], r, v, v, 0, 1);
    else ins(&c->code, OpVectorShuffle, 7, c->vec3[kind], r, v, v, 0, 1, 2);
    return r;
}

static uint32_t combined(ctx *c, uint32_t t, uint32_t s) {
    uint32_t img = id(c), smp = id(c), r = id(c);
    if (t >= 32 || !c->tex_vars[t]) { fail(c, "t%u not declared", t); return r; }
    if (s >= 16 || !c->sampler_vars[s]) { fail(c, "s%u not declared", s); return r; }
    ins(&c->code, OpLoad, 3, c->tex_types[t], img, c->tex_vars[t]);
    ins(&c->code, OpLoad, 3, c->sampler_t, smp, c->sampler_vars[s]);
    ins(&c->code, OpSampledImage, 4, c->si_types[t], r, img, smp);
    return r;
}

static void start_block(ctx *c, uint32_t label) {
    ins(&c->code, OpLabel, 1, label);
    c->block_open = 1;
}

/* Find which textures are read with comparison, since their image type must say so. */
static void prepass(ctx *c) {
    size_t pc = 2;
    while (pc < c->tn) {
        uint32_t w = c->t[pc], op = w & 0x7ff, len = (w >> 24) & 0x7f;
        if (op == S_CUSTOMDATA) len = c->t[pc + 1];
        if (!len) return;
        if (op == S_SAMPLE_C) {
            size_t saved = c->pc;
            operand o;
            int i;
            section keep = c->code;
            c->pc = pc + 1;
            while (c->t[c->pc - 1] >> 31 && c->pc - 1 == pc) c->pc++;
            memset(&c->code, 0, sizeof(c->code));
            /* Skip dest and coord, read the resource. Relative indexes here load nothing useful, so the code goes to a scratch section. */
            for (i = 0; i < 3; i++) {
                int was_failed = c->failed;
                c->failed = 1; /* suppress declaration errors while nothing is declared yet */
                parse_operand(c, &o);
                c->failed = was_failed;
            }
            free(c->code.w);
            c->code = keep;
            if (o.type == R_RESOURCE && o.index[0] < 32) c->depth_tex |= 1u << o.index[0];
            c->pc = saved;
        }
        pc += len;
    }
}

static void instruction(ctx *c) {
    uint32_t w = next_word(c), op = w & 0x7ff, len = (w >> 24) & 0x7f;
    size_t start = c->pc - 1;
    int sat = (w >> 13) & 1, nz = (w >> 18) & 1;
    int32_t off[3] = {0, 0, 0};
    int has_off = 0;
    operand d, a, b, e, f;
    uint32_t t4 = c->vec4[K_FLOAT], ti = c->vec4[K_INT], tu = c->vec4[K_UINT];

    if (op == S_CUSTOMDATA) {
        uint32_t words = next_word(c);
        if (((w >> 11) & 0x1f) == 3 && words >= 6) { /* immediate constant buffer: vec4s */
            uint32_t n = (words - 2) / 4, i, arr, comp, *members = malloc(n * 4);
            for (i = 0; i < n; i++) members[i] = const_vec4(c, K_FLOAT, c->t + start + 2 + i * 4);
            arr = id(c);
            ins(&c->types, OpTypeArray, 3, arr, c->vec4[K_FLOAT], cuint(c, n));
            comp = id(c);
            put(&c->types, OpConstantComposite | ((n + 3) << 16));
            put(&c->types, arr);
            put(&c->types, comp);
            for (i = 0; i < n; i++) put(&c->types, members[i]);
            free(members);
            c->icb_var = id(c);
            ins(&c->types, OpVariable, 4, ptr_t(c, 6, arr), c->icb_var, U(6), comp);
        }
        c->pc = start + words;
        return;
    }
    if (w >> 31) {
        uint32_t x;
        do {
            x = next_word(c);
            if ((x & 0x3f) == 1) {
                off[0] = (int32_t)(x << 19) >> 28;
                off[1] = (int32_t)(x << 15) >> 28;
                off[2] = (int32_t)(x << 11) >> 28;
                has_off = 1;
            }
        } while (x >> 31);
    }
    if (!c->block_open && op != S_ELSE && op != S_ENDIF && op != S_ENDLOOP && op < S_DCL_RESOURCE) start_block(c, id(c));

#define UNARY_EXT(FN) parse_operand(c, &d); parse_operand(c, &a); store_dst(c, &d, ext1(c, t4, FN, load_src(c, &a, K_FLOAT)), K_FLOAT, sat); break
#define BIN_F(OP) parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b); { uint32_t x = load_src(c, &a, K_FLOAT), y = load_src(c, &b, K_FLOAT); store_dst(c, &d, bin(c, OP, t4, x, y), K_FLOAT, sat); } break
#define BIN_EXT_F(FN) parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b); { uint32_t x = load_src(c, &a, K_FLOAT), y = load_src(c, &b, K_FLOAT); store_dst(c, &d, ext2(c, t4, FN, x, y), K_FLOAT, sat); } break
#define BIN_K(OP, K, T) parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b); { uint32_t x = load_src(c, &a, K), y = load_src(c, &b, K); store_dst(c, &d, bin(c, OP, T, x, y), K, 0); } break
#define BIN_EXT_K(FN, K, T) parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b); { uint32_t x = load_src(c, &a, K), y = load_src(c, &b, K); store_dst(c, &d, ext2(c, T, FN, x, y), K, 0); } break
#define CMP(OP, K) parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b); { uint32_t x = load_src(c, &a, K), y = load_src(c, &b, K); store_dst(c, &d, compare(c, OP, x, y), K_UINT, 0); } break
#define SHIFT(OP, K, T) parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b); { uint32_t x = load_src(c, &a, K), y = bin(c, OpBitwiseAnd, tu, load_src(c, &b, K_UINT), splat(c, K_UINT, 31)); store_dst(c, &d, bin(c, OP, T, x, y), K, 0); } break
#define DOT(N) parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b); { uint32_t x = load_src(c, &a, K_FLOAT), y = load_src(c, &b, K_FLOAT); if (N < 4) { x = shuffle_to(c, x, N); y = shuffle_to(c, y, N); } store_dst(c, &d, vec4_of(c, bin(c, OpDot, c->scalar[K_FLOAT], x, y)), K_FLOAT, sat); } break

    switch (op) {
    case S_NOP: case S_DCL_GLOBAL_FLAGS: break;
    case S_DCL_TEMPS: {
        uint32_t n = next_word(c), i;
        if (n > 256) { fail(c, "%u temps", n); break; }
        for (i = c->ntemps; i < n; i++) {
            c->temps[i] = id(c);
            ins(&c->vars, OpVariable, 3, ptr_t(c, SC_Function, t4), c->temps[i], U(SC_Function));
        }
        c->ntemps = n;
        break;
    }
    case S_DCL_INPUT: case S_DCL_INPUT_SGV: case S_DCL_INPUT_SIV: case S_DCL_INPUT_PS: case S_DCL_INPUT_PS_SGV: case S_DCL_INPUT_PS_SIV: dcl_input(c, w, op); break;
    case S_DCL_OUTPUT: case S_DCL_OUTPUT_SGV: case S_DCL_OUTPUT_SIV: dcl_output(c, op); break;
    case S_DCL_CB: dcl_cb(c); break;
    case S_DCL_RESOURCE: dcl_resource(c, w); break;
    case S_DCL_SAMPLER: dcl_sampler(c); break;

    case S_MOV: parse_operand(c, &d); parse_operand(c, &a); store_dst(c, &d, load_src(c, &a, K_FLOAT), K_FLOAT, sat); break;
    case S_ADD: BIN_F(OpFAdd);
    case S_MUL: BIN_F(OpFMul);
    case S_DIV: BIN_F(OpFDiv);
    case S_MIN: BIN_EXT_F(G_FMin);
    case S_MAX: BIN_EXT_F(G_FMax);
    case S_MAD:
        parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b); parse_operand(c, &e);
        { uint32_t x = load_src(c, &a, K_FLOAT), y = load_src(c, &b, K_FLOAT), z = load_src(c, &e, K_FLOAT); store_dst(c, &d, bin(c, OpFAdd, t4, bin(c, OpFMul, t4, x, y), z), K_FLOAT, sat); }
        break;
    case S_DP2: DOT(2);
    case S_DP3: DOT(3);
    case S_DP4: DOT(4);
    case S_SQRT: UNARY_EXT(G_Sqrt);
    case S_RSQ: UNARY_EXT(G_InverseSqrt);
    case S_EXP: UNARY_EXT(G_Exp2);
    case S_LOG: UNARY_EXT(G_Log2);
    case S_FRC: UNARY_EXT(G_Fract);
    case S_ROUND_NE: UNARY_EXT(G_RoundEven);
    case S_ROUND_NI: UNARY_EXT(G_Floor);
    case S_ROUND_PI: UNARY_EXT(G_Ceil);
    case S_ROUND_Z: UNARY_EXT(G_Trunc);
    case S_DERIV_RTX: parse_operand(c, &d); parse_operand(c, &a); store_dst(c, &d, un(c, OpDPdx, t4, load_src(c, &a, K_FLOAT)), K_FLOAT, sat); break;
    case S_DERIV_RTY: parse_operand(c, &d); parse_operand(c, &a); store_dst(c, &d, un(c, OpDPdy, t4, load_src(c, &a, K_FLOAT)), K_FLOAT, sat); break;
    case S_SINCOS: {
        operand d2;
        parse_operand(c, &d); parse_operand(c, &d2); parse_operand(c, &a);
        { uint32_t x = load_src(c, &a, K_FLOAT);
          if (d.type != R_NULL) store_dst(c, &d, ext1(c, t4, G_Sin, x), K_FLOAT, sat);
          if (d2.type != R_NULL) store_dst(c, &d2, ext1(c, t4, G_Cos, x), K_FLOAT, sat); }
        break;
    }
    case S_LT: CMP(OpFOrdLessThan, K_FLOAT);
    case S_GE: CMP(OpFOrdGreaterThanEqual, K_FLOAT);
    case S_EQ: CMP(OpFOrdEqual, K_FLOAT);
    case S_NE: CMP(OpFUnordNotEqual, K_FLOAT);
    case S_IEQ: CMP(OpIEqual, K_INT);
    case S_INE: CMP(OpINotEqual, K_INT);
    case S_IGE: CMP(OpSGreaterThanEqual, K_INT);
    case S_ILT: CMP(OpSLessThan, K_INT);
    case S_UGE: CMP(OpUGreaterThanEqual, K_UINT);
    case S_ULT: CMP(OpULessThan, K_UINT);
    case S_IADD: BIN_K(OpIAdd, K_INT, ti);
    case S_AND: BIN_K(OpBitwiseAnd, K_UINT, tu);
    case S_OR: BIN_K(OpBitwiseOr, K_UINT, tu);
    case S_XOR: BIN_K(OpBitwiseXor, K_UINT, tu);
    case S_IMAX: BIN_EXT_K(G_SMax, K_INT, ti);
    case S_IMIN: BIN_EXT_K(G_SMin, K_INT, ti);
    case S_UMAX: BIN_EXT_K(G_UMax, K_UINT, tu);
    case S_UMIN: BIN_EXT_K(G_UMin, K_UINT, tu);
    case S_ISHL: SHIFT(OpShiftLeftLogical, K_INT, ti);
    case S_ISHR: SHIFT(OpShiftRightArithmetic, K_INT, ti);
    case S_USHR: SHIFT(OpShiftRightLogical, K_UINT, tu);
    case S_IMUL:
        parse_operand(c, &d); parse_operand(c, &e); parse_operand(c, &a); parse_operand(c, &b);
        if (d.type != R_NULL) { fail(c, "imul with a high result"); break; }
        { uint32_t x = load_src(c, &a, K_INT), y = load_src(c, &b, K_INT); store_dst(c, &e, bin(c, OpIMul, ti, x, y), K_INT, 0); }
        break;
    case S_IMAD:
        parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b); parse_operand(c, &e);
        { uint32_t x = load_src(c, &a, K_INT), y = load_src(c, &b, K_INT), z = load_src(c, &e, K_INT); store_dst(c, &d, bin(c, OpIAdd, ti, bin(c, OpIMul, ti, x, y), z), K_INT, 0); }
        break;
    case S_INEG: parse_operand(c, &d); parse_operand(c, &a); store_dst(c, &d, un(c, OpSNegate, ti, load_src(c, &a, K_INT)), K_INT, 0); break;
    case S_NOT: parse_operand(c, &d); parse_operand(c, &a); store_dst(c, &d, un(c, OpNot, tu, load_src(c, &a, K_UINT)), K_UINT, 0); break;
    case S_ITOF: parse_operand(c, &d); parse_operand(c, &a); store_dst(c, &d, un(c, OpConvertSToF, t4, load_src(c, &a, K_INT)), K_FLOAT, sat); break;
    case S_UTOF: parse_operand(c, &d); parse_operand(c, &a); store_dst(c, &d, un(c, OpConvertUToF, t4, load_src(c, &a, K_UINT)), K_FLOAT, sat); break;
    case S_FTOI: parse_operand(c, &d); parse_operand(c, &a); store_dst(c, &d, un(c, OpConvertFToS, ti, load_src(c, &a, K_FLOAT)), K_INT, 0); break;
    case S_FTOU: parse_operand(c, &d); parse_operand(c, &a); store_dst(c, &d, un(c, OpConvertFToU, tu, load_src(c, &a, K_FLOAT)), K_UINT, 0); break;
    case S_MOVC:
        parse_operand(c, &d); parse_operand(c, &e); parse_operand(c, &a); parse_operand(c, &b);
        { uint32_t cnd = bin(c, OpINotEqual, c->bvec4, load_src(c, &e, K_UINT), splat(c, K_UINT, 0)), x = load_src(c, &a, K_FLOAT), y = load_src(c, &b, K_FLOAT), r = id(c);
          ins(&c->code, OpSelect, 5, t4, r, cnd, x, y);
          store_dst(c, &d, r, K_FLOAT, sat); }
        break;
    case S_DISCARD: {
        uint32_t cnd, kill = id(c), merge = id(c);
        parse_operand(c, &a);
        cnd = cond_of(c, &a, nz);
        ins(&c->code, OpSelectionMerge, 2, merge, U(0));
        ins(&c->code, OpBranchConditional, 3, cnd, kill, merge);
        ins(&c->code, OpLabel, 1, kill);
        ins(&c->code, OpKill, 0);
        ins(&c->code, OpLabel, 1, merge);
        c->info->uses_discard = 1;
        break;
    }
    case S_SAMPLE: case S_SAMPLE_L: case S_SAMPLE_C: {
        uint32_t coord, img, r, res, dim;
        int n;
        parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b); parse_operand(c, &e);
        if (op != S_SAMPLE) parse_operand(c, &f);
        dim = b.index[0] < 32 ? c->info->texture_dim[b.index[0]] : 0;
        n = coord_size(dim);
        coord = coord_of(c, load_src(c, &a, K_FLOAT), K_FLOAT, n);
        img = combined(c, b.index[0], e.index[0]);
        r = id(c);
        {
            uint32_t offc = 0, mask = has_off ? 8u : 0u; /* ConstOffset */
            if (has_off) {
                if (n == 2) {
                    offc = id(c);
                    ins(&c->types, OpConstantComposite, 4, c->vec2[K_INT], offc, const_t(c, c->scalar[K_INT], (uint32_t)off[0]), const_t(c, c->scalar[K_INT], (uint32_t)off[1]));
                } else { fail(c, "sample offset on a non-2D texture"); break; }
            }
            if (op == S_SAMPLE) {
                if (has_off) ins(&c->code, OpImageSampleImplicitLod, 6, t4, r, img, coord, mask, offc);
                else ins(&c->code, OpImageSampleImplicitLod, 4, t4, r, img, coord);
            } else if (op == S_SAMPLE_L) {
                uint32_t lod = id(c), lv = load_src(c, &f, K_FLOAT);
                ins(&c->code, OpCompositeExtract, 4, c->scalar[K_FLOAT], lod, lv, 0);
                if (has_off) ins(&c->code, OpImageSampleExplicitLod, 7, t4, r, img, coord, U(2u | 8u), lod, offc);
                else ins(&c->code, OpImageSampleExplicitLod, 6, t4, r, img, coord, U(2), lod);
            } else {
                uint32_t ref = id(c), rv = load_src(c, &f, K_FLOAT), s = id(c);
                ins(&c->code, OpCompositeExtract, 4, c->scalar[K_FLOAT], ref, rv, 0);
                if (has_off) ins(&c->code, OpImageSampleDrefImplicitLod, 7, c->scalar[K_FLOAT], s, img, coord, ref, mask, offc);
                else ins(&c->code, OpImageSampleDrefImplicitLod, 5, c->scalar[K_FLOAT], s, img, coord, ref);
                ins(&c->code, OpCompositeConstruct, 6, t4, r, s, s, s, s);
            }
        }
        res = bitcast(c, r, K_FLOAT, K_FLOAT, 4);
        store_dst(c, &d, swizzled(c, t4, res, b.swz), K_FLOAT, sat);
        break;
    }
    case S_LD: {
        uint32_t coord, cv, img, r, lod, dim, st, tv, full;
        int n;
        parse_operand(c, &d); parse_operand(c, &a); parse_operand(c, &b);
        dim = b.index[0] < 32 ? c->info->texture_dim[b.index[0]] : 0;
        if (b.index[0] >= 32 || !c->tex_vars[b.index[0]]) { fail(c, "t%u not declared", b.index[0]); break; }
        n = coord_size(dim);
        cv = load_src(c, &a, K_INT);
        coord = coord_of(c, cv, K_INT, n);
        lod = id(c);
        ins(&c->code, OpCompositeExtract, 4, c->scalar[K_INT], lod, cv, 3);
        tv = c->tex_vars[b.index[0]];
        img = id(c);
        ins(&c->code, OpLoad, 3, c->tex_types[b.index[0]], img, tv);
        r = id(c);
        st = c->vec4[c->tex_kind[b.index[0]]];
        ins(&c->code, OpImageFetch, 6, st, r, img, coord, U(2), lod);
        full = bitcast(c, r, (int)c->tex_kind[b.index[0]], K_FLOAT, 4);
        store_dst(c, &d, swizzled(c, t4, full, b.swz), K_FLOAT, sat);
        break;
    }
    case S_LOOP: {
        uint32_t head = id(c), body = id(c), cont = id(c), merge = id(c);
        if (c->loop_depth >= 32) { fail(c, "loops nested too deep"); break; }
        ins(&c->code, OpBranch, 1, head);
        ins(&c->code, OpLabel, 1, head);
        ins(&c->code, OpLoopMerge, 3, merge, cont, U(0));
        ins(&c->code, OpBranch, 1, body);
        ins(&c->code, OpLabel, 1, body);
        c->loop_head[c->loop_depth] = head;
        c->loop_cont[c->loop_depth] = cont;
        c->loop_merge[c->loop_depth++] = merge;
        break;
    }
    case S_ENDLOOP: {
        if (!c->loop_depth) { fail(c, "endloop without loop"); break; }
        c->loop_depth--;
        if (c->block_open) ins(&c->code, OpBranch, 1, c->loop_cont[c->loop_depth]);
        ins(&c->code, OpLabel, 1, c->loop_cont[c->loop_depth]);
        ins(&c->code, OpBranch, 1, c->loop_head[c->loop_depth]);
        start_block(c, c->loop_merge[c->loop_depth]);
        break;
    }
    case S_BREAK:
        if (!c->loop_depth) { fail(c, "break outside a loop"); break; }
        ins(&c->code, OpBranch, 1, c->loop_merge[c->loop_depth - 1]);
        c->block_open = 0;
        break;
    case S_BREAKC: {
        uint32_t cnd, next = id(c);
        parse_operand(c, &a);
        if (!c->loop_depth) { fail(c, "breakc outside a loop"); break; }
        cnd = cond_of(c, &a, nz);
        ins(&c->code, OpSelectionMerge, 2, next, U(0));
        ins(&c->code, OpBranchConditional, 3, cnd, c->loop_merge[c->loop_depth - 1], next);
        ins(&c->code, OpLabel, 1, next);
        break;
    }
    case S_IF: {
        uint32_t cnd, then = id(c), other = id(c), end = id(c);
        parse_operand(c, &a);
        if (c->if_depth >= 32) { fail(c, "ifs nested too deep"); break; }
        cnd = cond_of(c, &a, nz);
        ins(&c->code, OpSelectionMerge, 2, end, U(0));
        ins(&c->code, OpBranchConditional, 3, cnd, then, other);
        ins(&c->code, OpLabel, 1, then);
        c->if_end[c->if_depth] = end;
        c->if_else[c->if_depth++] = other;
        break;
    }
    case S_ELSE:
        if (!c->if_depth) { fail(c, "else without if"); break; }
        if (c->block_open) ins(&c->code, OpBranch, 1, c->if_end[c->if_depth - 1]);
        start_block(c, c->if_else[c->if_depth - 1]);
        c->if_else[c->if_depth - 1] = 0;
        break;
    case S_ENDIF:
        if (!c->if_depth) { fail(c, "endif without if"); break; }
        c->if_depth--;
        if (c->block_open) ins(&c->code, OpBranch, 1, c->if_end[c->if_depth]);
        if (c->if_else[c->if_depth]) {
            ins(&c->code, OpLabel, 1, c->if_else[c->if_depth]);
            ins(&c->code, OpBranch, 1, c->if_end[c->if_depth]);
        }
        start_block(c, c->if_end[c->if_depth]);
        break;
    case S_RET:
        ins(&c->code, OpReturn, 0);
        c->block_open = 0;
        break;
    default:
        fail(c, "unsupported SM4 opcode %u", op);
        break;
    }
    if (!c->failed && c->pc != start + len && op != S_CUSTOMDATA) fail(c, "opcode %u: parsed %u words, length says %u", op, (unsigned)(c->pc - start), len);
    if (op == S_DCL_GLOBAL_FLAGS || op == S_NOP) c->pc = start + len;
}

static void append(section *out, const section *s) {
    size_t i;
    for (i = 0; i < s->n; i++) put(out, s->w[i]);
}

int oa_dxbc_translate(const void *dxbc, size_t size, oa_shader_info *info, uint32_t **spirv, size_t *words, char *err, size_t err_size) {
    const uint8_t *d = dxbc;
    uint32_t len, shex_len, version, i;
    const char *p;
    ctx *c = calloc(1, sizeof(ctx));
    section out = {0};
    uint32_t main_id, label, ok;

    memset(info, 0, sizeof(*info));
    c->info = info;
    c->err = err;
    c->err_size = err_size;
    if (err_size) err[0] = 0;
    if (size < 32 || memcmp(d, "DXBC", 4)) { fail(c, "not DXBC"); goto done; }
    p = sig_chunk(d, size, "SHDR", &shex_len);
    if (!p) p = sig_chunk(d, size, "SHEX", &shex_len);
    if (!p) { fail(c, "no shader chunk"); goto done; }
    c->t = (const uint32_t *)p;
    c->tn = shex_len / 4;
    version = c->t[0];
    if ((version >> 16) > 1) { fail(c, "unsupported shader type %u", version >> 16); goto done; }
    info->is_pixel = (version >> 16) == 0;
    info->binding_base = info->is_pixel ? 0 : OA_BIND_VS_BASE;
    {
        const char *q = sig_chunk(d, size, "ISGN", &len);
        info->input_count = read_sig(q, q ? len : 0, info->inputs);
        q = sig_chunk(d, size, "OSGN", &len);
        info->output_count = read_sig(q, q ? len : 0, info->outputs);
    }
    c->next_id = 1;
    ins(&c->head, OpCapability, 1, U(1)); /* Shader */
    c->glsl = id(c);
    c->void_t = id(c);
    ins(&c->types, OpTypeVoid, 1, c->void_t);
    c->func_t = id(c);
    ins(&c->types, OpTypeFunction, 2, c->func_t, c->void_t);
    c->scalar[K_FLOAT] = id(c);
    ins(&c->types, OpTypeFloat, 2, c->scalar[K_FLOAT], U(32));
    c->scalar[K_INT] = id(c);
    ins(&c->types, OpTypeInt, 3, c->scalar[K_INT], U(32), U(1));
    c->scalar[K_UINT] = id(c);
    ins(&c->types, OpTypeInt, 3, c->scalar[K_UINT], U(32), U(0));
    for (i = 0; i < 3; i++) {
        c->vec2[i] = id(c);
        ins(&c->types, OpTypeVector, 3, c->vec2[i], c->scalar[i], U(2));
        c->vec3[i] = id(c);
        ins(&c->types, OpTypeVector, 3, c->vec3[i], c->scalar[i], U(3));
        c->vec4[i] = id(c);
        ins(&c->types, OpTypeVector, 3, c->vec4[i], c->scalar[i], U(4));
    }
    c->bool_t = id(c);
    ins(&c->types, OpTypeBool, 1, c->bool_t);
    c->bvec4 = id(c);
    ins(&c->types, OpTypeVector, 3, c->bvec4, c->bool_t, U(4));
    c->sampler_t = id(c);
    ins(&c->types, OpTypeSampler, 1, c->sampler_t);
    prepass(c);
    main_id = id(c);
    label = id(c);
    c->pc = 2;
    c->block_open = 1;
    while (c->pc < c->tn && !c->failed) instruction(c);
    if (c->failed) goto done;
    if (c->block_open) ins(&c->code, OpReturn, 0);

    /* Assemble. */
    put(&out, 0x07230203);
    put(&out, 0x00010000);
    put(&out, 0);
    put(&out, c->next_id);
    put(&out, 0);
    append(&out, &c->head);
    {
        section s = {0};
        uint32_t w = str_words(&s, "GLSL.std.450");
        put(&out, OpExtInstImport | ((w + 2) << 16));
        put(&out, c->glsl);
        append(&out, &s);
        free(s.w);
    }
    ins(&out, OpMemoryModel, 2, U(0), U(1));
    {
        section s = {0};
        uint32_t w = str_words(&s, "main");
        put(&out, OpEntryPoint | ((3 + w + c->niface) << 16));
        put(&out, info->is_pixel ? 4 : 0);
        put(&out, main_id);
        append(&out, &s);
        for (i = 0; i < c->niface; i++) put(&out, c->iface[i]);
        free(s.w);
    }
    if (info->is_pixel) {
        ins(&out, OpExecutionMode, 2, main_id, U(7)); /* OriginUpperLeft */
        if (info->writes_depth) ins(&out, OpExecutionMode, 2, main_id, U(12)); /* DepthReplacing */
    }
    append(&out, &c->annot);
    append(&out, &c->types);
    ins(&out, OpFunction, 4, c->void_t, main_id, U(0), c->func_t);
    ins(&out, OpLabel, 1, label);
    append(&out, &c->vars);
    append(&out, &c->code);
    ins(&out, OpFunctionEnd, 0);
done:
    ok = !c->failed;
    if (ok) {
        *spirv = out.w;
        *words = out.n;
    } else {
        free(out.w);
        *spirv = NULL;
        *words = 0;
    }
    free(c->head.w); free(c->entry.w); free(c->exec.w); free(c->annot.w); free(c->types.w); free(c->vars.w); free(c->code.w);
    free(c);
    return (int)ok;
}
