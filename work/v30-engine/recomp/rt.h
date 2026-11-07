/* rt.h: runtime for code translated from 32-bit x86. Guest addresses are host addresses in the low 4 GB. */
#ifndef OA_RT_H
#define OA_RT_H
#include <stdint.h>
#include <string.h>
#include <math.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32; typedef uint64_t u64;
typedef int8_t s8; typedef int16_t s16; typedef int32_t s32; typedef int64_t s64;
typedef union { u64 q[2]; u32 d[4]; u16 w[8]; u8 b[16]; float f[4]; double g[2]; s32 i[4]; s16 h[8]; } X;
typedef void (*fn)(void);
typedef struct { u32 eax, ecx, edx, ebx, esp, ebp, esi, edi; X xmm0, xmm1, xmm2, xmm3, xmm4, xmm5, xmm6, xmm7; } cpu_t;
extern __thread cpu_t C;
extern __thread double ST_[8];
extern __thread int STP;
extern __thread u32 FSW, FCW, MXCSR, DF, FS;
fn dispatch(u32 addr);
void trap_(u32 addr, const char *what);
#define INL static inline __attribute__((always_inline))
#define P(a) ((void *)(uintptr_t)(u32)(a))
INL u8 R8(u32 a) { return *(volatile u8 *)P(a); }
INL u16 R16(u32 a) { u16 v; __builtin_memcpy(&v, P(a), 2); return v; }
INL u32 R32(u32 a) { u32 v; __builtin_memcpy(&v, P(a), 4); return v; }
INL u64 R64(u32 a) { u64 v; __builtin_memcpy(&v, P(a), 8); return v; }
INL float RF(u32 a) { float v; __builtin_memcpy(&v, P(a), 4); return v; }
INL double RD(u32 a) { double v; __builtin_memcpy(&v, P(a), 8); return v; }
INL X RX(u32 a) { X v; __builtin_memcpy(&v, P(a), 16); return v; }
INL void W8(u32 a, u8 v) { *(volatile u8 *)P(a) = v; }
INL void W16(u32 a, u16 v) { __builtin_memcpy(P(a), &v, 2); }
INL void W32(u32 a, u32 v) { __builtin_memcpy(P(a), &v, 4); }
INL void W64(u32 a, u64 v) { __builtin_memcpy(P(a), &v, 8); }
INL void WF(u32 a, float v) { __builtin_memcpy(P(a), &v, 4); }
INL void WD(u32 a, double v) { __builtin_memcpy(P(a), &v, 8); }
INL void WX(u32 a, X v) { __builtin_memcpy(P(a), &v, 16); }
INL u8 par(u32 r) { return !__builtin_parity(r & 0xff); }
#define SZP(r, bits) do { zf = ((r) & (u32)(0xffffffffu >> (32 - (bits)))) == 0; sf = ((r) >> ((bits) - 1)) & 1; pf = par(r); } while (0)
#define FADD(r, a, b, bits) do { SZP(r, bits); cf = (bits == 32) ? ((u32)(r) < (u32)(a)) : (((u64)(a) + (u64)(b)) >> (bits)) & 1; of = ((((a) ^ (r)) & ((b) ^ (r))) >> ((bits) - 1)) & 1; } while (0)
#define FSUB(r, a, b, bits) do { SZP(r, bits); cf = (u32)(a) < (u32)(b); of = ((((a) ^ (b)) & ((a) ^ (r))) >> ((bits) - 1)) & 1; } while (0)
#define FLOG(r, bits) do { SZP(r, bits); cf = 0; of = 0; } while (0)
INL u32 cvt_d2i(double d) { return (d > -2147483649.0 && d < 2147483648.0) ? (u32)(s32)d : 0x80000000u; }
INL u32 round_d2i(double d) { return cvt_d2i(rint(d)); }
#define COMI(a, b) do { of = 0; sf = 0; if ((a) != (a) || (b) != (b)) { zf = 1; pf = 1; cf = 1; } else { zf = (a) == (b); pf = 0; cf = (a) < (b); } } while (0)
/* Packed helpers */
#define LOOP(n) for (int i_ = 0; i_ < (n); i_++)
#define PACKED(name, T, field, n, expr) INL X name(X a, X b) { X r; LOOP(n) { T x = a.field[i_], y = b.field[i_]; (void)x; (void)y; r.field[i_] = (expr); } return r; }
PACKED(p_addps, float, f, 4, x + y) PACKED(p_subps, float, f, 4, x - y) PACKED(p_mulps, float, f, 4, x * y) PACKED(p_divps, float, f, 4, x / y)
PACKED(p_addpd, double, g, 2, x + y) PACKED(p_subpd, double, g, 2, x - y) PACKED(p_mulpd, double, g, 2, x * y)
PACKED(p_minps, float, f, 4, x < y ? x : y) PACKED(p_maxps, float, f, 4, x > y ? x : y)
PACKED(p_paddd, u32, d, 4, x + y) PACKED(p_psubd, u32, d, 4, x - y) PACKED(p_paddw, u16, w, 8, (u16)(x + y)) PACKED(p_paddq, u64, q, 2, x + y) PACKED(p_psubq, u64, q, 2, x - y)
PACKED(p_pcmpeqd, u32, d, 4, x == y ? 0xffffffffu : 0) PACKED(p_pcmpgtd, s32, i, 4, x > y ? -1 : 0)
PACKED(p_pminsw, s16, h, 8, x < y ? x : y) PACKED(p_pmaxsw, s16, h, 8, x > y ? x : y)
PACKED(p_cmpltps, float, f, 4, x < y ? (r.d[i_] = 0xffffffffu, r.f[i_]) : (r.d[i_] = 0, r.f[i_]))
INL X p_and(X a, X b) { X r; r.q[0] = a.q[0] & b.q[0]; r.q[1] = a.q[1] & b.q[1]; return r; }
INL X p_or(X a, X b) { X r; r.q[0] = a.q[0] | b.q[0]; r.q[1] = a.q[1] | b.q[1]; return r; }
INL X p_xor(X a, X b) { X r; r.q[0] = a.q[0] ^ b.q[0]; r.q[1] = a.q[1] ^ b.q[1]; return r; }
INL X p_andn(X a, X b) { X r; r.q[0] = ~a.q[0] & b.q[0]; r.q[1] = ~a.q[1] & b.q[1]; return r; }
INL X p_cmpltps_(X a, X b) { X r; LOOP(4) r.d[i_] = a.f[i_] < b.f[i_] ? 0xffffffffu : 0; return r; }
INL X p_rcpps(X a) { X r; LOOP(4) r.f[i_] = 1.0f / a.f[i_]; return r; }
INL X p_rsqrtps(X a) { X r; LOOP(4) r.f[i_] = 1.0f / sqrtf(a.f[i_]); return r; }
INL X p_sqrtps(X a) { X r; LOOP(4) r.f[i_] = sqrtf(a.f[i_]); return r; }
INL X p_shufps(X a, X b, u32 c) { X r; r.d[0] = a.d[c & 3]; r.d[1] = a.d[(c >> 2) & 3]; r.d[2] = b.d[(c >> 4) & 3]; r.d[3] = b.d[(c >> 6) & 3]; return r; }
INL X p_shufpd(X a, X b, u32 c) { X r; r.q[0] = a.q[c & 1]; r.q[1] = b.q[(c >> 1) & 1]; return r; }
INL X p_pshufd(X b, u32 c) { X r; LOOP(4) r.d[i_] = b.d[(c >> (i_ * 2)) & 3]; return r; }
INL X p_pshufb(X a, X b) { X r; LOOP(16) r.b[i_] = (b.b[i_] & 0x80) ? 0 : a.b[b.b[i_] & 15]; return r; }
INL X p_unpcklps(X a, X b) { X r; r.d[0] = a.d[0]; r.d[1] = b.d[0]; r.d[2] = a.d[1]; r.d[3] = b.d[1]; return r; }
INL X p_unpckhps(X a, X b) { X r; r.d[0] = a.d[2]; r.d[1] = b.d[2]; r.d[2] = a.d[3]; r.d[3] = b.d[3]; return r; }
INL X p_unpcklpd(X a, X b) { X r; r.q[0] = a.q[0]; r.q[1] = b.q[0]; return r; }
INL X p_unpckhpd(X a, X b) { X r; r.q[0] = a.q[1]; r.q[1] = b.q[1]; return r; }
INL X p_punpcklbw(X a, X b) { X r; LOOP(8) { r.b[i_ * 2] = a.b[i_]; r.b[i_ * 2 + 1] = b.b[i_]; } return r; }
INL X p_punpcklwd(X a, X b) { X r; LOOP(4) { r.w[i_ * 2] = a.w[i_]; r.w[i_ * 2 + 1] = b.w[i_]; } return r; }
INL X p_punpckhwd(X a, X b) { X r; LOOP(4) { r.w[i_ * 2] = a.w[i_ + 4]; r.w[i_ * 2 + 1] = b.w[i_ + 4]; } return r; }
INL X p_packuswb(X a, X b) { X r; LOOP(8) { s16 x = a.h[i_], y = b.h[i_]; r.b[i_] = x < 0 ? 0 : x > 255 ? 255 : x; r.b[i_ + 8] = y < 0 ? 0 : y > 255 ? 255 : y; } return r; }
INL X p_pmuludq(X a, X b) { X r; r.q[0] = (u64)a.d[0] * b.d[0]; r.q[1] = (u64)a.d[2] * b.d[2]; return r; }
#define SHIFT_FN(name, T, field, n, bits, expr, big) INL X name(X a, u32 c) { X r; LOOP(n) { T x = a.field[i_]; r.field[i_] = c >= bits ? (big) : (expr); } return r; }
SHIFT_FN(p_pslld, u32, d, 4, 32, x << c, 0) SHIFT_FN(p_psrld, u32, d, 4, 32, x >> c, 0) SHIFT_FN(p_psrad, s32, i, 4, 32, x >> c, x >> 31)
SHIFT_FN(p_psllq, u64, q, 2, 64, x << c, 0) SHIFT_FN(p_psrlq, u64, q, 2, 64, x >> c, 0) SHIFT_FN(p_psllw, u16, w, 8, 16, (u16)(x << c), 0) SHIFT_FN(p_psrlw, u16, w, 8, 16, x >> c, 0)
INL X p_pslldq(X a, u32 c) { X r; c = c > 16 ? 16 : c; memset(&r, 0, 16); memcpy(r.b + c, a.b, 16 - c); return r; }
INL X p_psrldq(X a, u32 c) { X r; c = c > 16 ? 16 : c; memset(&r, 0, 16); memcpy(r.b, a.b + c, 16 - c); return r; }
INL u32 p_pmovmskb(X a) { u32 r = 0; LOOP(16) r |= (u32)(a.b[i_] >> 7) << i_; return r; }
INL X p_cvtps2pd(X b) { X r; r.g[0] = b.f[0]; r.g[1] = b.f[1]; return r; }
INL X p_cvtpd2ps(X b) { X r; r.f[0] = (float)b.g[0]; r.f[1] = (float)b.g[1]; r.q[1] = 0; return r; }
INL X p_cvtdq2ps(X b) { X r; LOOP(4) r.f[i_] = (float)b.i[i_]; return r; }
INL X p_cvtdq2pd(X b) { X r; r.g[0] = b.i[0]; r.g[1] = b.i[1]; return r; }
INL X p_cvtps2dq(X b) { X r; LOOP(4) r.d[i_] = round_d2i(b.f[i_]); return r; }
INL X X_q(u64 v) { X r; r.q[0] = v; r.q[1] = 0; return r; }
INL X X_d(u32 v) { X r; r.q[0] = v; r.q[1] = 0; return r; }
/* x87, kept as doubles */
#define ST(i) ST_[(STP + (i)) & 7]
INL void FPUSH(double v) { STP = (STP - 1) & 7; ST_[STP] = v; }
INL double FPOP(void) { double v = ST_[STP]; STP = (STP + 1) & 7; return v; }
INL double frnd(double d) { switch ((FCW >> 10) & 3) { case 1: return floor(d); case 2: return ceil(d); case 3: return trunc(d); default: return rint(d); } }
INL void FCOMSW(double a, double b) { u32 c; if (a != a || b != b) c = 0x4500; else if (a > b) c = 0; else if (a < b) c = 0x100; else c = 0x4000; FSW = (FSW & ~0x4500u) | c; }
#define FCOMIF(a, b) COMI(a, b)
double rd80(u32 a);
void wr80(u32 a, double v);
/* String operations */
INL void rep_movs(u32 *esi, u32 *edi, u32 *ecx, u32 sz, int rep) { u32 n = rep ? *ecx : 1; s32 d = DF ? -(s32)sz : (s32)sz; if (!DF && (*edi - *esi >= n * sz)) { memmove(P(*edi), P(*esi), n * sz); *esi += n * sz; *edi += n * sz; } else { while (n--) { for (u32 k = 0; k < sz; k++) W8(*edi + k, R8(*esi + k)); *esi += d; *edi += d; } } if (rep) *ecx = 0; }
INL void rep_stos(u32 eax, u32 *edi, u32 *ecx, u32 sz, int rep) { u32 n = rep ? *ecx : 1; s32 d = DF ? -(s32)sz : (s32)sz; while (n--) { for (u32 k = 0; k < sz; k++) W8(*edi + k, (u8)(eax >> (k * 8))); *edi += d; } if (rep) *ecx = 0; }
#endif
