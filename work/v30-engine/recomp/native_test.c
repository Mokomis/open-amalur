/* native_test.c: runs the translated animation decoder 0x111bf10 natively on ARM64.
   Same inputs and output format as work/v20-char/clip_bake.cpp, so the two outputs can be compared byte for byte.
   Usage: native_test koa.exe skeleton.fab_bxml clip.anm_bxml out.bin */
#define _GNU_SOURCE
#include "rt.h"
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <time.h>

void f_0111bf10(void);

#define IMAGE_BASE 0x400000u
#define ARENA_BASE 0x10000000u
#define ARENA_SIZE (64u << 20)
#define STACK_SIZE (8u << 20)

static u32 g_bump = ARENA_BASE + STACK_SIZE;

static void *map_at(u32 addr, u32 size, int prot) {
    void *p = mmap(P(addr), size, prot, MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED_NOREPLACE, -1, 0);
    if (p == MAP_FAILED || p != P(addr)) {
        fprintf(stderr, "cannot map %08x size %x: %p\n", addr, size, p);
        exit(4);
    }
    return p;
}

static u32 lalloc(u32 size) {
    u32 a = (g_bump + 127) & ~127u;
    g_bump = a + size;
    if (g_bump > ARENA_BASE + ARENA_SIZE) { fprintf(stderr, "arena full\n"); exit(4); }
    return a;
}

static u32 load_low(const char *path, u32 *size) {
    FILE *f = fopen(path, "rb");
    long n;
    u32 a;
    if (!f) { fprintf(stderr, "open %s\n", path); exit(2); }
    fseek(f, 0, SEEK_END);
    n = ftell(f);
    rewind(f);
    a = lalloc((u32)n + 16);
    if (fread(P(a), 1, (size_t)n, f) != (size_t)n) exit(2);
    fclose(f);
    *size = (u32)n;
    return a;
}

static void load_image(const char *path) {
    FILE *f = fopen(path, "rb");
    long n;
    u8 *b;
    u32 pe, image_size;
    u16 ns, oh;
    if (!f) { fprintf(stderr, "open %s\n", path); exit(2); }
    fseek(f, 0, SEEK_END);
    n = ftell(f);
    rewind(f);
    b = malloc((size_t)n);
    if (fread(b, 1, (size_t)n, f) != (size_t)n) exit(2);
    fclose(f);
    memcpy(&pe, b + 0x3c, 4);
    memcpy(&ns, b + pe + 6, 2);
    memcpy(&oh, b + pe + 20, 2);
    memcpy(&image_size, b + pe + 24 + 56, 4);
    map_at(IMAGE_BASE, (image_size + 0xfff) & ~0xfffu, PROT_READ | PROT_WRITE);
    for (u32 i = 0; i < ns; i++) {
        u8 *s = b + pe + 24 + oh + 40 * i;
        u32 va, raw, rp;
        memcpy(&va, s + 12, 4);
        memcpy(&raw, s + 16, 4);
        memcpy(&rp, s + 20, 4);
        if (raw) memcpy(P(IMAGE_BASE + va), b + rp, raw);
    }
    free(b);
}

#define RD16(a) R16(a)
static u32 rel(u32 a, u32 o) {
    s32 v = (s32)R32(a + o);
    return v ? a + o + (u32)v : 0;
}

int main(int argc, char **argv) {
    u32 sf_size, cf_size, stack_top;
    struct timespec t0, t1;
    double total = 0;
    if (argc != 5) { fprintf(stderr, "usage\n"); return 2; }
    load_image(argv[1]);
    map_at(ARENA_BASE, ARENA_SIZE, PROT_READ | PROT_WRITE);
    stack_top = ARENA_BASE + STACK_SIZE - 64;

    u32 sf = load_low(argv[2], &sf_size);
    if (memcmp(P(sf + 4), "30SE", 4)) { fprintf(stderr, "bad skeleton tag\n"); return 5; }
    u32 skel = sf + 4;
    u32 joints = R16(skel + 0x10);
    u32 bind = rel(skel, 0x18);

    u32 cf = load_low(argv[3], &cf_size);
    u32 size = R32(cf + 4);
    u32 anim = lalloc(size);
    memcpy(P(anim), P(cf + 8), size);
    if (memcmp(P(anim), "50AE", 4)) { fprintf(stderr, "bad clip tag\n"); return 5; }
    float fps = RF(anim + 8);
    u32 clip_joints = R16(anim + 0xe), frames = R16(anim + 0x10), sets = R16(anim + 0x12);
    if (clip_joints > joints) { fprintf(stderr, "joint mismatch\n"); return 6; }
    u32 frame_tab = rel(anim, 0x3c), data_tab = rel(anim, 0x38);
    u32 out = lalloc(joints * 48 + 64), user = lalloc(4096), work = lalloc(1u << 20);

    FILE *f = fopen(argv[4], "wb");
    if (!f) return 2;
    fwrite(&joints, 4, 1, f);
    fwrite(&frames, 4, 1, f);
    fwrite(&fps, 4, 1, f);
    for (u32 fr = 0; fr < frames; fr++) {
        memcpy(P(out), P(bind), joints * 48);
        memset(P(user), 0, 4096);
        u32 lo = 0, hi = sets - 1;
        while (lo + 1 < hi) {
            u32 mid = (lo + hi) / 2;
            if (fr < R16(frame_tab + mid * 4)) hi = mid;
            else lo = mid;
        }
        u32 base = R16(frame_tab + lo * 4), count = R16(frame_tab + lo * 4 + 2);
        u32 off = R32(data_tab + 4 + lo * 8), sz = R16(data_tab + 2 + lo * 8);
        u32 set = work + ((anim + off) & 0x7f);
        if (sz) memcpy(P(set), P(anim + off), sz);
        s32 idx = (s32)(fr - base);
        float alpha = 0.f;
        if (count < (u32)idx) { alpha = 1.f; idx = (s32)count; }

        /* cdecl call on the guest stack, like the x86 harness. */
        u32 esp = stack_top;
        esp -= 4; WF(esp, alpha);
        esp -= 4; W32(esp, (u32)idx);
        esp -= 4; W32(esp, count);
        esp -= 4; W32(esp, set);
        esp -= 4; W32(esp, anim);
        esp -= 4; W32(esp, user);
        esp -= 4; W32(esp, out);
        esp -= 4; W32(esp, 0xdead0000u);
        C.esp = esp;
        clock_gettime(CLOCK_MONOTONIC, &t0);
        f_0111bf10();
        clock_gettime(CLOCK_MONOTONIC, &t1);
        total += (double)(t1.tv_sec - t0.tv_sec) + (double)(t1.tv_nsec - t0.tv_nsec) * 1e-9;
        if (C.esp != esp + 4) { fprintf(stderr, "stack mismatch frame %u: %08x vs %08x\n", fr, C.esp, esp + 4); return 7; }
        if (fwrite(P(out), 48, joints, f) != joints) return 3;
    }
    fclose(f);
    printf("joints %u frames %u sets %u fps %.3f\n", joints, frames, sets, fps);
    printf("decode time total %.3f ms, %.2f us per frame\n", total * 1e3, frames ? total * 1e6 / frames : 0.0);
    return 0;
}
