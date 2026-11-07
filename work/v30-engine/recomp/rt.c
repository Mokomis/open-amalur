/* rt.c: runtime for translated code. Lookup of guest code addresses, traps and 80-bit floats. */
#include "rt.h"
#include <stdio.h>
#include <stdlib.h>

__thread cpu_t C;
__thread double ST_[8];
__thread int STP;
__thread u32 FSW, FCW = 0x27f, MXCSR = 0x1f80, DF, FS;

typedef struct { u32 addr; fn f; } func_entry;
extern const func_entry g_funcs[];
extern const u32 g_nfuncs;

long g_dispatch_misses;

fn dispatch(u32 addr) {
    u32 lo = 0, hi = g_nfuncs;
    while (lo < hi) {
        u32 m = (lo + hi) / 2;
        if (g_funcs[m].addr < addr) lo = m + 1;
        else hi = m;
    }
    if (lo < g_nfuncs && g_funcs[lo].addr == addr) return g_funcs[lo].f;
    fprintf(stderr, "dispatch: no translated code for %08x (esp %08x)\n", addr, C.esp);
    fflush(stderr);
    exit(98);
}

void trap_(u32 addr, const char *what) {
    fprintf(stderr, "trap at %08x: %s\n", addr, what);
    fflush(stderr);
    exit(99);
}

double rd80(u32 a) {
    u64 m = R64(a);
    u16 se = R16(a + 8);
    int e = se & 0x7fff;
    double v;
    if (!e && !m) v = 0.0;
    else if (e == 0x7fff) v = (m << 1) ? NAN : INFINITY;
    else v = ldexp((double)m, e - 16383 - 63);
    return (se & 0x8000) ? -v : v;
}

void wr80(u32 a, double v) {
    u64 m = 0;
    int e = 0;
    u16 se = signbit(v) ? 0x8000 : 0;
    if (v != v) { m = 0xc000000000000000ull; e = 0x7fff; }
    else if (isinf(v)) { m = 0x8000000000000000ull; e = 0x7fff; }
    else if (v != 0.0) {
        int x;
        double f = frexp(fabs(v), &x);
        m = (u64)ldexp(f, 64);
        e = x - 1 + 16383;
    }
    W64(a, m);
    W16(a + 8, (u16)(se | e));
}
