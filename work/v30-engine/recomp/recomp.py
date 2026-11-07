#!/usr/bin/env python3
"""recomp.py <koa.exe> <recomp dir> <out dir> [limit]: translate koa.exe's x86 code to C. Every instruction it cannot handle becomes a counted trap."""
import collections, json, os, re, struct, sys, time

import capstone
from capstone import x86_const as K

exe, rdir, outdir = sys.argv[1:4]
limit = int(sys.argv[4]) if len(sys.argv) > 4 else 0
d = open(exe, "rb").read()
pe = struct.unpack_from("<I", d, 0x3c)[0]
ns = struct.unpack_from("<H", d, pe + 6)[0]
oh = struct.unpack_from("<H", d, pe + 20)[0]
o = pe + 24
base = struct.unpack_from("<I", d, o + 28)[0]
secs = {}
for i in range(ns):
    s = o + oh + 40 * i
    n = d[s:s + 8].rstrip(b"\0").decode()
    vs, va, rs, rp = struct.unpack_from("<IIII", d, s + 8)
    secs[n] = (base + va, vs, rp, rs)
TLO, _, TRP, TRS = secs[".text"]
THI = TLO + TRS
text = d[TRP:TRP + TRS]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True


def u32_at(a):
    for lo, vs, rp, rs in secs.values():
        if lo <= a < lo + min(vs, rs) - 3:
            return struct.unpack_from("<I", d, a - lo + rp)[0]
    return None


GPR = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"]
SUB = {"ax": ("eax", 16), "cx": ("ecx", 16), "dx": ("edx", 16), "bx": ("ebx", 16), "sp": ("esp", 16), "bp": ("ebp", 16), "si": ("esi", 16), "di": ("edi", 16),
       "al": ("eax", 8), "cl": ("ecx", 8), "dl": ("edx", 8), "bl": ("ebx", 8), "ah": ("eax", 9), "ch": ("ecx", 9), "dh": ("edx", 9), "bh": ("ebx", 9)}
CC = {"e": "zf", "ne": "!zf", "l": "sf!=of", "ge": "sf==of", "le": "(zf||sf!=of)", "g": "(!zf&&sf==of)", "b": "cf", "ae": "!cf", "be": "(cf||zf)", "a": "(!cf&&!zf)",
      "s": "sf", "ns": "!sf", "p": "pf", "np": "!pf", "o": "of", "no": "!of"}


class Unsupported(Exception):
    pass


class G:
    def __init__(self, ins):
        self.i = ins
        self.ops = ins.operands
        self.used = set()

    def rname(self, r):
        return self.i.reg_name(r)

    def addr(self, op):
        m = op.mem
        parts = []
        if m.base:
            parts.append(self.reg_base(self.rname(m.base)))
        if m.index:
            parts.append(f"{self.reg_base(self.rname(m.index))}*{m.scale}" if m.scale != 1 else self.reg_base(self.rname(m.index)))
        if m.disp:
            parts.append(f"0x{m.disp & 0xffffffff:x}u")
        if m.segment and self.rname(m.segment) == "fs":
            parts.append("FS")
        return "(u32)(" + ("+".join(parts) if parts else "0u") + ")"

    def reg_base(self, n):
        if n not in GPR:
            raise Unsupported("address register " + n)
        self.used.add(n)
        return n

    def rd(self, op, signed=False):
        if op.type == K.X86_OP_IMM:
            mask = (1 << (op.size * 8)) - 1 if op.size < 8 else 0xffffffff
            return f"0x{op.imm & mask & 0xffffffff:x}u"
        if op.type == K.X86_OP_REG:
            n = self.rname(op.reg)
            if n in GPR:
                self.used.add(n)
                return n
            if n in SUB:
                b, k = SUB[n]
                self.used.add(b)
                return {16: f"(u16){b}", 8: f"(u8){b}", 9: f"(u8)({b}>>8)"}[k]
            raise Unsupported("register " + n)
        if op.type == K.X86_OP_MEM:
            return {1: "R8", 2: "R16", 4: "R32", 8: "R64"}[op.size] + "(" + self.addr(op) + ")"
        raise Unsupported("operand")

    def wr(self, op, v):
        if op.type == K.X86_OP_REG:
            n = self.rname(op.reg)
            if n in GPR:
                self.used.add(n)
                return f"{n}=(u32)({v});"
            if n in SUB:
                b, k = SUB[n]
                self.used.add(b)
                return {16: f"{b}=({b}&0xffff0000u)|(u16)({v});", 8: f"{b}=({b}&0xffffff00u)|(u8)({v});", 9: f"{b}=({b}&0xffff00ffu)|((u32)(u8)({v})<<8);"}[k]
            raise Unsupported("register " + n)
        if op.type == K.X86_OP_MEM:
            return {1: "W8", 2: "W16", 4: "W32", 8: "W64"}[op.size] + f"({self.addr(op)},{v});"
        raise Unsupported("write operand")

    def x(self, op):
        """Whole xmm value from a register or 16-byte memory."""
        if op.type == K.X86_OP_REG:
            n = self.rname(op.reg)
            if not n.startswith("xmm"):
                raise Unsupported("expected xmm " + n)
            self.used.add(n)
            return n
        return f"RX({self.addr(op)})"

    def xr(self, op):
        n = self.rname(op.reg)
        if not n.startswith("xmm"):
            raise Unsupported("expected xmm " + n)
        self.used.add(n)
        return n

    def isx(self, op):
        return op.type == K.X86_OP_REG and self.rname(op.reg).startswith("xmm")

    def lowf(self, op):
        return f"{self.xr(op)}.f[0]" if self.isx(op) else f"RF({self.addr(op)})"

    def lowd(self, op):
        return f"{self.xr(op)}.g[0]" if self.isx(op) else f"RD({self.addr(op)})"


def bits(op):
    return op.size * 8


def alu(g, m, ops):
    a, b = ops[0], ops[1]
    w = bits(a)
    T = "u32"
    ra, rb = g.rd(a), g.rd(b)
    mask = "" if w == 32 else f"&0x{(1 << w) - 1:x}u"
    if m == "add":
        return f"{{{T} a_={ra},b_={rb},r_=(a_+b_){mask};FADD(r_,a_,b_,{w});{g.wr(a, 'r_')}}}"
    if m == "sub":
        return f"{{{T} a_={ra},b_={rb},r_=(a_-b_){mask};FSUB(r_,a_,b_,{w});{g.wr(a, 'r_')}}}"
    if m == "cmp":
        return f"{{{T} a_={ra},b_={rb},r_=(a_-b_){mask};FSUB(r_,a_,b_,{w});}}"
    if m == "test":
        return f"{{{T} r_=({ra})&({rb});FLOG(r_,{w});}}"
    if m in ("and", "or", "xor"):
        op = {"and": "&", "or": "|", "xor": "^"}[m]
        return f"{{{T} r_=({ra}){op}({rb});FLOG(r_,{w});{g.wr(a, 'r_')}}}"
    if m == "adc":
        return f"{{u32 a_={ra},b_={rb},c_=cf;u64 w_=(u64)a_+b_+c_;u32 r_=(u32)w_{mask};SZP(r_,{w});cf=(w_>>{w})&1;of=(((a_^r_)&(b_^r_))>>{w - 1})&1;{g.wr(a, 'r_')}}}"
    if m == "sbb":
        return f"{{u32 a_={ra},b_={rb},c_=cf;u64 w_=(u64)a_-b_-c_;u32 r_=(u32)w_{mask};SZP(r_,{w});cf=(w_>>{w})&1;of=(((a_^b_)&(a_^r_))>>{w - 1})&1;{g.wr(a, 'r_')}}}"
    raise Unsupported(m)


def shift(g, m, ops):
    a = ops[0]
    w = bits(a)
    c = g.rd(ops[1]) if len(ops) > 1 else "1u"
    ra = g.rd(a)
    mask = "" if w == 32 else f"&0x{(1 << w) - 1:x}u"
    if m == "shl":
        return f"{{u32 c_=({c})&31;if(c_){{u32 a_={ra},r_=(a_<<c_){mask};cf=(a_>>({w}-c_))&1;SZP(r_,{w});of=((r_>>{w - 1})&1)^cf;{g.wr(a, 'r_')}}}}}"
    if m == "shr":
        return f"{{u32 c_=({c})&31;if(c_){{u32 a_={ra},r_=a_>>c_;cf=(a_>>(c_-1))&1;SZP(r_,{w});of=(a_>>{w - 1})&1;{g.wr(a, 'r_')}}}}}"
    if m == "sar":
        st = {8: "s8", 16: "s16", 32: "s32"}[w]
        return f"{{u32 c_=({c})&31;if(c_){{s32 a_=({st})({ra});u32 r_=(u32)(a_>>c_){mask};cf=(a_>>(c_-1))&1;SZP(r_,{w});of=0;{g.wr(a, 'r_')}}}}}"
    if m == "rol":
        return f"{{u32 c_=({c})&31;if(c_%{w}){{u32 a_={ra},k_=c_%{w},r_=((a_<<k_)|(a_>>({w}-k_))){mask};cf=r_&1;of=((r_>>{w - 1})&1)^cf;{g.wr(a, 'r_')}}}}}"
    if m == "ror":
        return f"{{u32 c_=({c})&31;if(c_%{w}){{u32 a_={ra},k_=c_%{w},r_=((a_>>k_)|(a_<<({w}-k_))){mask};cf=(r_>>{w - 1})&1;of=((r_>>{w - 1})^(r_>>{w - 2}))&1;{g.wr(a, 'r_')}}}}}"
    if m == "rcr" and w == 32:
        return f"{{u32 c_=({c})&31;if(c_){{u64 a_=((u64)cf<<32)|{ra};for(u32 k_=0;k_<c_;k_++){{u64 b_=a_&1;a_=(a_>>1)|(b_<<32);}}cf=(a_>>32)&1;{g.wr(a, '(u32)a_')}}}}}"
    raise Unsupported(m + str(w))


def xmmop(g, m, ops):
    a, b = (ops + [None, None])[:2]
    pk = {"addps": "p_addps", "subps": "p_subps", "mulps": "p_mulps", "divps": "p_divps", "addpd": "p_addpd", "subpd": "p_subpd", "mulpd": "p_mulpd", "minps": "p_minps", "maxps": "p_maxps",
          "paddd": "p_paddd", "psubd": "p_psubd", "paddw": "p_paddw", "paddq": "p_paddq", "psubq": "p_psubq", "pcmpeqd": "p_pcmpeqd", "pcmpgtd": "p_pcmpgtd", "pminsw": "p_pminsw", "pmaxsw": "p_pmaxsw",
          "xorps": "p_xor", "xorpd": "p_xor", "pxor": "p_xor", "andps": "p_and", "andpd": "p_and", "pand": "p_and", "orps": "p_or", "orpd": "p_or", "por": "p_or", "andnps": "p_andn", "andnpd": "p_andn", "pandn": "p_andn",
          "unpcklps": "p_unpcklps", "unpckhps": "p_unpckhps", "unpcklpd": "p_unpcklpd", "unpckhpd": "p_unpckhpd", "punpckldq": "p_unpcklps", "punpckhdq": "p_unpckhps", "punpcklqdq": "p_unpcklpd", "punpckhqdq": "p_unpckhpd",
          "punpcklbw": "p_punpcklbw", "punpcklwd": "p_punpcklwd", "punpckhwd": "p_punpckhwd", "packuswb": "p_packuswb", "pmuludq": "p_pmuludq", "pshufb": "p_pshufb", "cmpltps": "p_cmpltps_"}
    if m in pk:
        return f"{g.xr(a)}={pk[m]}({g.x(a)},{g.x(b)});"
    un = {"cvtdq2ps": "p_cvtdq2ps", "cvtps2dq": "p_cvtps2dq", "cvtpd2ps": "p_cvtpd2ps", "rcpps": "p_rcpps", "rsqrtps": "p_rsqrtps", "sqrtps": "p_sqrtps"}
    if m in un:
        return f"{g.xr(a)}={un[m]}({g.x(b)});"
    if m in ("cvtps2pd",):
        src = g.xr(b) if g.isx(b) else f"X_q(R64({g.addr(b)}))"
        return f"{g.xr(a)}=p_cvtps2pd({src});"
    if m == "cvtdq2pd":
        src = g.xr(b) if g.isx(b) else f"X_q(R64({g.addr(b)}))"
        return f"{g.xr(a)}=p_cvtdq2pd({src});"
    if m in ("movaps", "movups", "movapd", "movdqa", "movdqu", "movupd"):
        if a.type == K.X86_OP_MEM:
            return f"WX({g.addr(a)},{g.xr(b)});"
        return f"{g.xr(a)}={g.x(b)};"
    if m == "movss":
        if a.type == K.X86_OP_MEM:
            return f"W32({g.addr(a)},{g.xr(b)}.d[0]);"
        if g.isx(b):
            return f"{g.xr(a)}.d[0]={g.xr(b)}.d[0];"
        return f"{g.xr(a)}=X_d(R32({g.addr(b)}));"
    if m == "movsd":
        if a.type == K.X86_OP_MEM:
            return f"W64({g.addr(a)},{g.xr(b)}.q[0]);"
        if g.isx(b):
            return f"{g.xr(a)}.q[0]={g.xr(b)}.q[0];"
        return f"{g.xr(a)}=X_q(R64({g.addr(b)}));"
    if m == "movq":
        if a.type == K.X86_OP_MEM:
            return f"W64({g.addr(a)},{g.xr(b)}.q[0]);"
        if g.isx(b):
            return f"{g.xr(a)}=X_q({g.xr(b)}.q[0]);"
        return f"{g.xr(a)}=X_q(R64({g.addr(b)}));"
    if m == "movd":
        if g.isx(a):
            return f"{g.xr(a)}=X_d({g.rd(b)});"
        return g.wr(a, f"{g.xr(b)}.d[0]")
    if m == "movlpd":
        if a.type == K.X86_OP_MEM:
            return f"W64({g.addr(a)},{g.xr(b)}.q[0]);"
        return f"{g.xr(a)}.q[0]=R64({g.addr(b)});"
    sd = {"addsd": "+", "subsd": "-", "mulsd": "*", "divsd": "/"}
    if m in sd:
        return f"{g.xr(a)}.g[0]={g.xr(a)}.g[0]{sd[m]}{g.lowd(b)};"
    ss = {"addss": "+", "subss": "-", "mulss": "*", "divss": "/"}
    if m in ss:
        return f"{g.xr(a)}.f[0]={g.xr(a)}.f[0]{ss[m]}{g.lowf(b)};"
    if m == "sqrtsd":
        return f"{g.xr(a)}.g[0]=sqrt({g.lowd(b)});"
    if m == "cvtss2sd":
        return f"{g.xr(a)}.g[0]=(double){g.lowf(b)};"
    if m == "cvtsd2ss":
        return f"{g.xr(a)}.f[0]=(float){g.lowd(b)};"
    if m == "cvtsi2ss":
        return f"{g.xr(a)}.f[0]=(float)(s32){g.rd(b)};"
    if m == "cvtsi2sd":
        return f"{g.xr(a)}.g[0]=(double)(s32){g.rd(b)};"
    if m == "cvttsd2si":
        return g.wr(a, f"cvt_d2i({g.lowd(b)})")
    if m == "cvttss2si":
        return g.wr(a, f"cvt_d2i((double){g.lowf(b)})")
    if m == "cvtsd2si":
        return g.wr(a, f"round_d2i({g.lowd(b)})")
    if m in ("comisd", "ucomisd"):
        return f"{{double a_={g.xr(a)}.g[0],b_={g.lowd(b)};COMI(a_,b_);}}"
    if m in ("comiss", "ucomiss"):
        return f"{{float a_={g.xr(a)}.f[0],b_={g.lowf(b)};COMI(a_,b_);}}"
    if m in ("cmpltsd", "cmpnlesd", "cmpeqsd"):
        c = {"cmpltsd": "a_<b_", "cmpnlesd": "!(a_<=b_)", "cmpeqsd": "a_==b_"}[m]
        return f"{{double a_={g.xr(a)}.g[0],b_={g.lowd(b)};{g.xr(a)}.q[0]=({c})?~0ull:0;}}"
    if m in ("cmpnlepd", "cmpneqpd"):
        c = {"cmpnlepd": "!(a_<=b_)", "cmpneqpd": "a_!=b_"}[m]
        return f"{{X s_={g.x(a)},t_={g.x(b)};for(int k_=0;k_<2;k_++){{double a_=s_.g[k_],b_=t_.g[k_];{g.xr(a)}.q[k_]=({c})?~0ull:0;}}}}"
    if m == "shufps":
        return f"{g.xr(a)}=p_shufps({g.xr(a)},{g.x(b)},{ops[2].imm & 255}u);"
    if m == "shufpd":
        return f"{g.xr(a)}=p_shufpd({g.xr(a)},{g.x(b)},{ops[2].imm & 255}u);"
    if m == "pshufd":
        return f"{g.xr(a)}=p_pshufd({g.x(b)},{ops[2].imm & 255}u);"
    sh = {"pslld": "p_pslld", "psrld": "p_psrld", "psrad": "p_psrad", "psllq": "p_psllq", "psrlq": "p_psrlq", "psllw": "p_psllw", "psrlw": "p_psrlw"}
    if m in sh:
        c = f"{b.imm & 255}u" if b.type == K.X86_OP_IMM else f"(u32){g.x(b)}.q[0]"
        return f"{g.xr(a)}={sh[m]}({g.xr(a)},{c});"
    if m == "pslldq":
        return f"{g.xr(a)}=p_pslldq({g.xr(a)},{b.imm & 255}u);"
    if m == "psrldq":
        return f"{g.xr(a)}=p_psrldq({g.xr(a)},{b.imm & 255}u);"
    if m == "pmovmskb":
        return g.wr(a, f"p_pmovmskb({g.xr(b)})")
    if m == "pextrw":
        return g.wr(a, f"{g.xr(b)}.w[{ops[2].imm & 7}]")
    if m == "pinsrw":
        return f"{g.xr(a)}.w[{ops[2].imm & 7}]=(u16)({g.rd(b)});"
    raise Unsupported(m)


def x87(g, m, ops):
    txt = g.i.op_str
    st = lambda op: int(g.rname(op.reg)[-2]) if g.rname(op.reg) != "st(0)" else 0
    mem = ops and ops[0].type == K.X86_OP_MEM
    if m == "fld":
        if mem:
            return {4: f"FPUSH(RF({g.addr(ops[0])}));", 8: f"FPUSH(RD({g.addr(ops[0])}));", 10: f"FPUSH(rd80({g.addr(ops[0])}));"}[ops[0].size]
        return f"{{double v_=ST({st(ops[0])});FPUSH(v_);}}"
    if m in ("fst", "fstp"):
        pop = "FPOP();" if m == "fstp" else ""
        if mem:
            return {4: f"WF({g.addr(ops[0])},(float)ST(0));", 8: f"WD({g.addr(ops[0])},ST(0));", 10: f"wr80({g.addr(ops[0])},ST(0));"}[ops[0].size] + pop
        return f"ST({st(ops[0])})=ST(0);" + pop
    if m == "fild":
        return {2: f"FPUSH((double)(s16)R16({g.addr(ops[0])}));", 4: f"FPUSH((double)(s32)R32({g.addr(ops[0])}));", 8: f"FPUSH((double)(s64)R64({g.addr(ops[0])}));"}[ops[0].size]
    if m == "fistp":
        return {2: f"W16({g.addr(ops[0])},(u16)(s32)frnd(ST(0)));", 4: f"W32({g.addr(ops[0])},cvt_d2i(frnd(ST(0))));", 8: f"W64({g.addr(ops[0])},(u64)(s64)frnd(ST(0)));"}[ops[0].size] + "FPOP();"
    if m in ("fist", "fisttp"):
        rd = "trunc(ST(0))" if m == "fisttp" else "frnd(ST(0))"
        pop = "FPOP();" if m == "fisttp" else ""
        return {2: f"W16({g.addr(ops[0])},(u16)(s32){rd});", 4: f"W32({g.addr(ops[0])},cvt_d2i({rd}));", 8: f"W64({g.addr(ops[0])},(u64)(s64){rd});"}[ops[0].size] + pop
    arith = {"fadd": "a_+b_", "fsub": "a_-b_", "fsubr": "b_-a_", "fmul": "a_*b_", "fdiv": "a_/b_", "fdivr": "b_/a_"}
    p = {"faddp": "fadd", "fsubp": "fsub", "fsubrp": "fsubr", "fmulp": "fmul", "fdivp": "fdiv", "fdivrp": "fdivr"}
    if m in p:
        i = st(ops[0]) if ops else 1
        return f"{{double a_=ST({i}),b_=ST(0);ST({i})={arith[p[m]]};FPOP();}}"
    if m in arith:
        if mem:
            src = f"RF({g.addr(ops[0])})" if ops[0].size == 4 else f"RD({g.addr(ops[0])})"
            return f"{{double a_=ST(0),b_={src};ST(0)={arith[m]};}}"
        if len(ops) == 2 and g.rname(ops[0].reg) != "st(0)":
            i = st(ops[0])
            return f"{{double a_=ST({i}),b_=ST(0);ST({i})={arith[m]};}}"
        i = st(ops[-1]) if ops else 1
        return f"{{double a_=ST(0),b_=ST({i});ST(0)={arith[m]};}}"
    ia = {"fiadd": "a_+b_", "fimul": "a_*b_", "fidiv": "a_/b_", "fisub": "a_-b_"}
    if m in ia:
        rd = f"(double)(s32)R32({g.addr(ops[0])})" if ops[0].size == 4 else f"(double)(s16)R16({g.addr(ops[0])})"
        return f"{{double a_=ST(0),b_={rd};ST(0)={ia[m]};}}"
    if m in ("fcomi", "fucomi", "fcompi", "fucompi"):
        i = st(ops[-1]) if ops else 1
        return f"{{double a_=ST(0),b_=ST({i});COMI(a_,b_);}}" + ("FPOP();" if m.endswith("pi") else "")
    if m in ("fcom", "fcomp", "fucom", "fucomp"):
        pop = "FPOP();" if m.endswith("p") else ""
        if mem:
            src = f"RF({g.addr(ops[0])})" if ops[0].size == 4 else f"RD({g.addr(ops[0])})"
            return f"FCOMSW(ST(0),{src});" + pop
        i = st(ops[0]) if ops else 1
        return f"FCOMSW(ST(0),ST({i}));" + pop
    if m in ("fcompp", "fucompp"):
        return "FCOMSW(ST(0),ST(1));FPOP();FPOP();"
    if m == "fnstsw":
        v = "(FSW&0x4500)|((STP&7)<<11)"
        return g.wr(ops[0], v)
    if m == "fnstcw":
        return f"W16({g.addr(ops[0])},(u16)FCW);"
    if m == "fldcw":
        return f"FCW=R16({g.addr(ops[0])});"
    if m == "stmxcsr":
        return f"W32({g.addr(ops[0])},MXCSR);"
    if m == "ldmxcsr":
        return f"MXCSR=R32({g.addr(ops[0])});"
    if m == "fxch":
        i = st(ops[0]) if ops else 1
        return f"{{double t_=ST(0);ST(0)=ST({i});ST({i})=t_;}}"
    simple = {"fld1": "FPUSH(1.0);", "fldz": "FPUSH(0.0);", "fldpi": "FPUSH(3.14159265358979323846);", "fldlg2": "FPUSH(0.30102999566398119521);", "fldln2": "FPUSH(0.69314718055994530942);",
              "fchs": "ST(0)=-ST(0);", "fabs": "ST(0)=fabs(ST(0));", "fsqrt": "ST(0)=sqrt(ST(0));", "fsin": "ST(0)=sin(ST(0));", "fcos": "ST(0)=cos(ST(0));", "frndint": "ST(0)=frnd(ST(0));",
              "fptan": "ST(0)=tan(ST(0));FPUSH(1.0);", "fpatan": "{double a_=ST(1),b_=ST(0);ST(1)=atan2(a_,b_);FPOP();}", "fprem1": "ST(0)=remainder(ST(0),ST(1));FSW&=~0x400u;", "fprem": "ST(0)=fmod(ST(0),ST(1));FSW&=~0x400u;", "f2xm1": "ST(0)=expm1(ST(0)*0.69314718055994530942);",
              "fyl2x": "{double a_=ST(1),b_=ST(0);ST(1)=a_*log2(b_);FPOP();}", "fscale": "ST(0)=ldexp(ST(0),(int)trunc(ST(1)));", "wait": "", "fnclex": "",
              "fxam": "{double v_=ST(0);u32 c_=(v_!=v_)?0x100:isinf(v_)?0x500:v_==0?0x4000:0x400;if(signbit(v_))c_|=0x200;FSW=(FSW&~0x4700u)|c_;}"}
    if m in simple:
        return simple[m]
    raise Unsupported(m)


def plain(g, m, ops, ins):
    """Non-control instructions."""
    if m in ("add", "sub", "cmp", "test", "and", "or", "xor", "adc", "sbb"):
        return alu(g, m, ops)
    if m in ("shl", "shr", "sar", "rol", "ror", "rcr"):
        return shift(g, m, ops)
    if m == "mov":
        return g.wr(ops[0], g.rd(ops[1]))
    if m == "movzx":
        return g.wr(ops[0], g.rd(ops[1]))
    if m == "movsx":
        st = {1: "s8", 2: "s16"}[ops[1].size]
        return g.wr(ops[0], f"(u32)(s32)({st})({g.rd(ops[1])})")
    if m == "lea":
        return g.wr(ops[0], g.addr(ops[1]))
    if m == "push":
        g.used.add("esp")
        if ops[0].size == 2:
            raise Unsupported("push16")
        return f"{{u32 v_={g.rd(ops[0])};esp-=4;W32(esp,v_);}}"
    if m == "pop":
        g.used.add("esp")
        return f"{{u32 v_=R32(esp);esp+=4;{g.wr(ops[0], 'v_')}}}"
    if m == "inc":
        w = bits(ops[0])
        mask = "" if w == 32 else f"&0x{(1 << w) - 1:x}u"
        return f"{{u32 a_={g.rd(ops[0])},r_=(a_+1){mask};SZP(r_,{w});of=r_==(1u<<{w - 1});{g.wr(ops[0], 'r_')}}}"
    if m == "dec":
        w = bits(ops[0])
        mask = "" if w == 32 else f"&0x{(1 << w) - 1:x}u"
        return f"{{u32 a_={g.rd(ops[0])},r_=(a_-1){mask};SZP(r_,{w});of=a_==(1u<<{w - 1});{g.wr(ops[0], 'r_')}}}"
    if m == "neg":
        w = bits(ops[0])
        mask = "" if w == 32 else f"&0x{(1 << w) - 1:x}u"
        return f"{{u32 a_={g.rd(ops[0])},r_=(0u-a_){mask};cf=a_!=0;of=a_==(1u<<{w - 1});SZP(r_,{w});{g.wr(ops[0], 'r_')}}}"
    if m == "not":
        mask = "" if bits(ops[0]) == 32 else f"&0x{(1 << bits(ops[0])) - 1:x}u"
        return g.wr(ops[0], f"(~{g.rd(ops[0])}){mask}")
    if m == "xchg":
        return f"{{u32 a_={g.rd(ops[0])},b_={g.rd(ops[1])};{g.wr(ops[0], 'b_')}{g.wr(ops[1], 'a_')}}}"
    if m == "cdq":
        g.used |= {"eax", "edx"}
        return "edx=(u32)((s32)eax>>31);"
    if m == "cwde":
        g.used.add("eax")
        return "eax=(u32)(s32)(s16)eax;"
    if m == "cbw":
        g.used.add("eax")
        return "eax=(eax&0xffff0000u)|(u16)(s16)(s8)eax;"
    if m == "imul":
        if len(ops) == 1:
            if ops[0].size != 4:
                raise Unsupported("imul narrow")
            g.used |= {"eax", "edx"}
            return f"{{s64 w_=(s64)(s32)eax*(s32){g.rd(ops[0])};eax=(u32)w_;edx=(u32)(w_>>32);cf=of=(w_!=(s64)(s32)w_);}}"
        a, b = (ops[0], ops[0]) if False else (ops[-2], ops[-1]) if len(ops) == 3 else (ops[0], ops[1])
        if len(ops) == 3:
            a, b = ops[1], ops[2]
        if ops[0].size == 4:
            return f"{{s64 w_=(s64)(s32){g.rd(a)}*(s32){g.rd(b)};cf=of=(w_!=(s64)(s32)w_);{g.wr(ops[0], '(u32)w_')}}}"
        if ops[0].size == 2:
            return f"{{s32 w_=(s32)(s16){g.rd(a)}*(s16){g.rd(b)};cf=of=(w_!=(s32)(s16)w_);{g.wr(ops[0], '(u16)w_')}}}"
        raise Unsupported("imul narrow")
    if m == "mul":
        if ops[0].size != 4:
            raise Unsupported("mul narrow")
        g.used |= {"eax", "edx"}
        return f"{{u64 w_=(u64)eax*{g.rd(ops[0])};eax=(u32)w_;edx=(u32)(w_>>32);cf=of=edx!=0;}}"
    if m == "div":
        if ops[0].size != 4:
            raise Unsupported("div narrow")
        g.used |= {"eax", "edx"}
        return f"{{u64 n_=((u64)edx<<32)|eax;u32 v_={g.rd(ops[0])};eax=(u32)(n_/v_);edx=(u32)(n_%v_);}}"
    if m == "idiv":
        if ops[0].size != 4:
            raise Unsupported("idiv narrow")
        g.used |= {"eax", "edx"}
        return f"{{s64 n_=(s64)(((u64)edx<<32)|eax);s32 v_=(s32){g.rd(ops[0])};eax=(u32)(n_/v_);edx=(u32)(n_%v_);}}"
    if m == "shrd" or m == "shld":
        a = g.rd(ops[0])
        b = g.rd(ops[1])
        c = g.rd(ops[2])
        if m == "shrd":
            return f"{{u32 c_=({c})&31;if(c_){{u32 a_={a},b_={b},r_=(a_>>c_)|(b_<<(32-c_));cf=(a_>>(c_-1))&1;SZP(r_,32);{g.wr(ops[0], 'r_')}}}}}"
        return f"{{u32 c_=({c})&31;if(c_){{u32 a_={a},b_={b},r_=(a_<<c_)|(b_>>(32-c_));cf=(a_>>(32-c_))&1;SZP(r_,32);{g.wr(ops[0], 'r_')}}}}}"
    if m == "bsr":
        return f"{{u32 v_={g.rd(ops[1])};zf=v_==0;if(v_){{{g.wr(ops[0], '31-__builtin_clz(v_)')}}}}}"
    if m == "bsf":
        return f"{{u32 v_={g.rd(ops[1])};zf=v_==0;if(v_){{{g.wr(ops[0], '__builtin_ctz(v_)')}}}}}"
    if m == "bt":
        return f"cf=(({g.rd(ops[0])})>>(({g.rd(ops[1])})&31))&1;"
    if m == "bts":
        return f"{{u32 a_={g.rd(ops[0])},c_=({g.rd(ops[1])})&31;cf=(a_>>c_)&1;{g.wr(ops[0], 'a_|(1u<<c_)')}}}"
    if m == "lahf":
        g.used.add("eax")
        return "eax=(eax&0xffff00ffu)|(((u32)sf<<15)|((u32)zf<<14)|((u32)pf<<10)|(1u<<9)|((u32)cf<<8));"
    if m == "sahf":
        g.used.add("eax")
        return "sf=(eax>>15)&1;zf=(eax>>14)&1;pf=(eax>>10)&1;cf=(eax>>8)&1;"
    if m == "leave":
        g.used |= {"esp", "ebp"}
        return "esp=ebp;ebp=R32(esp);esp+=4;"
    if m == "nop" or m == "pause":
        return ""
    if m == "clc":
        return "cf=0;"
    if m == "stc":
        return "cf=1;"
    if m == "cmc":
        return "cf=!cf;"
    if m == "popfd":
        g.used.add("esp")
        return "{u32 v_=R32(esp);esp+=4;of=(v_>>11)&1;sf=(v_>>7)&1;zf=(v_>>6)&1;pf=(v_>>2)&1;cf=v_&1;DF=(v_>>10)&1;}"
    if m == "lodsb":
        g.used |= {"eax", "esi"}
        return "eax=(eax&0xffffff00u)|R8(esi);esi+=DF?-1:1;"
    if m == "cld":
        return "DF=0;"
    if m == "std":
        return "DF=1;"
    if m == "pushfd":
        g.used.add("esp")
        return "esp-=4;W32(esp,((u32)of<<11)|((u32)sf<<7)|((u32)zf<<6)|((u32)pf<<2)|2u|((u32)cf));"
    if m == "cpuid":
        g.used |= {"eax", "ebx", "ecx", "edx"}
        return "{u32 l_=eax;eax=l_==0?1:0x000006f0;ebx=l_==0?0x756e6547:0;ecx=l_==0?0x6c65746e:0;edx=l_==0?0x49656e69:0x07808011;}"
    if m == "rdtsc":
        g.used |= {"eax", "edx"}
        return "{u64 t_;__asm__ __volatile__(\"mrs %0, cntvct_el0\":\"=r\"(t_));eax=(u32)t_;edx=(u32)(t_>>32);}"
    if m == "xlatb":
        g.used |= {"eax", "ebx"}
        return "eax=(eax&0xffffff00u)|R8(ebx+(u8)eax);"
    if m.startswith("set") and m[3:] in CC:
        return g.wr(ops[0], f"({CC[m[3:]]})?1u:0u")
    if m.startswith("cmov") and m[4:] in CC:
        return f"if({CC[m[4:]]}){{{g.wr(ops[0], g.rd(ops[1]))}}}"
    if m in ("rep movsd", "rep movsb", "rep movsw", "movsd", "movsw", "movsb") and not any(o.type == K.X86_OP_REG and g.rname(o.reg).startswith("xmm") for o in ops):
        g.used |= {"esi", "edi", "ecx"}
        rep = 1 if m.startswith("rep") else 0
        sz = {"d": 4, "w": 2, "b": 1}[m[-1]]
        return f"rep_movs(&esi,&edi,&ecx,{sz},{rep});"
    if m in ("rep stosd", "stosd", "rep stosb", "stosb", "rep stosw", "stosw"):
        g.used |= {"eax", "edi", "ecx"}
        rep = 1 if m.startswith("rep") else 0
        sz = {"d": 4, "w": 2, "b": 1}[m[-1]]
        return f"rep_stos(eax,&edi,&ecx,{sz},{rep});"
    if m == "repne scasb":
        g.used |= {"eax", "edi", "ecx"}
        return "while(ecx){u32 a_=(u8)eax,b_=R8(edi),r_=(a_-b_)&0xffu;FSUB(r_,a_,b_,8);edi+=DF?-1:1;ecx--;if(zf)break;}"
    if m == "lock xadd":
        return f"{{u32 v_={g.rd(ops[1])},o_=__atomic_fetch_add((u32*)P({g.addr(ops[0])}),v_,__ATOMIC_SEQ_CST),r_=o_+v_;FADD(r_,o_,v_,32);{g.wr(ops[1], 'o_')}}}"
    if m == "lock cmpxchg":
        g.used.add("eax")
        return f"{{u32 e_=eax,n_={g.rd(ops[1])},a_=e_;zf=__atomic_compare_exchange_n((u32*)P({g.addr(ops[0])}),&a_,n_,0,__ATOMIC_SEQ_CST,__ATOMIC_SEQ_CST);eax=a_;}}"
    if m[:1] == "f" or m in ("wait", "stmxcsr", "ldmxcsr"):
        return x87(g, m, ops)
    return xmmop(g, m, ops)


def decode(pc):
    off = pc - TLO
    if not (0 <= off < TRS):
        return None
    for ins in md.disasm(text[off:off + 15], pc, 1):
        return ins
    return None


# ---- entries ----
ghidra = set()
for line in open(os.path.join(rdir, "func_ranges.tsv")):
    ghidra.add(int(line.split("\t", 1)[0], 16))
jumps = {}
for line in open(os.path.join(rdir, "computed_jumps.tsv")):
    p = line.rstrip("\n").split("\t")
    jumps[int(p[0], 16)] = [int(x, 16) for x in p[2].split(",") if ":" not in x] if len(p) > 2 and p[2] else []
covered = bytearray(TRS)
for line in open(os.path.join(rdir, "func_ranges.tsv")):
    for r in line.rstrip("\n").split("\t")[2].split(","):
        lo, hi = (int(x, 16) for x in r.split("-"))
        covered[lo - TLO:hi + 1 - TLO] = b"\1" * (hi + 1 - lo)
entries = set(ghidra)
source = {a: "ghidra" for a in ghidra}
for name in (".rdata", ".data"):
    lo, vs, p, r = secs[name]
    b = d[p:p + r]
    for i in range(0, r - 3, 4):
        v = struct.unpack_from("<I", b, i)[0]
        if TLO <= v < THI and not covered[v - TLO] and text[v - TLO] != 0xcc and v not in entries:
            entries.add(v)
            source[v] = "data pointer"
print("entries: ghidra", len(ghidra), "plus data pointers", len(entries) - len(ghidra), flush=True)

os.makedirs(outdir, exist_ok=True)
stats = collections.Counter()
unsup = collections.Counter()
unsup_ex = {}
done = set()
work = sorted(entries)
chunk_idx = 0
out_lines = []
fwd = set()
all_funcs = []
t0 = time.time()


def flush():
    global chunk_idx, out_lines, fwd
    if not out_lines:
        return
    with open(os.path.join(outdir, f"koa_{chunk_idx:03d}.c"), "w") as w:
        w.write('#include "rt.h"\n')
        for a in sorted(fwd):
            w.write(f"void f_{a:08x}(void);\n")
        w.write("".join(out_lines))
    chunk_idx += 1
    out_lines = []
    fwd = set()


while work:
    entry = work.pop()
    if entry in done:
        continue
    done.add(entry)
    # discover the function's instructions
    insns = {}
    labels = set()
    stack = [entry]
    calls = []
    while stack:
        pc = stack.pop()
        while pc not in insns:
            ins = decode(pc)
            if ins is None:
                insns[pc] = None
                stats["undecodable stops"] += 1
                break
            insns[pc] = ins
            m = ins.mnemonic
            nxt = pc + ins.size
            if m in ("ret", "retf", "int3", "ud2", "hlt", "repz ret"):
                break
            if m == "call":
                op = ins.operands[0]
                if op.type == K.X86_OP_IMM:
                    calls.append(op.imm & 0xffffffff)
                pc = nxt
                continue
            if m == "jmp":
                op = ins.operands[0]
                if op.type == K.X86_OP_IMM:
                    t = op.imm & 0xffffffff
                    if t in entries or not (TLO <= t < THI):
                        calls.append(t)
                        break
                    labels.add(t)
                    pc = t
                    continue
                if op.type == K.X86_OP_MEM and op.mem.scale == 4 and op.mem.index and not op.mem.base and op.mem.disp:
                    targets = jumps.get(pc) or []
                    if not targets:
                        tb = op.mem.disp & 0xffffffff
                        for k in range(256):
                            v = u32_at(tb + 4 * k)
                            if v is None or not (TLO <= v < THI):
                                break
                            targets.append(v)
                    targets = [x & 0xffffffff for x in targets]
                    labels.update(targets)
                    stack.extend(targets)
                    jumps[pc] = targets
                break
            if m[0] == "j":
                op = ins.operands[0]
                t = op.imm & 0xffffffff
                labels.add(t)
                stack.append(t)
                pc = nxt
                continue
            pc = nxt
    for t in calls:
        if TLO <= t < THI and t not in entries:
            entries.add(t)
            source[t] = "call target"
            work.append(t)
        elif TLO <= t < THI and t not in done:
            pass
    # Any fall-through that does not reach the next instruction in address order needs a label too.
    order = sorted(insns)
    for idx, pc in enumerate(order):
        ins = insns[pc]
        if ins is None or ins.mnemonic in ("ret", "retf", "repz ret", "int3", "ud2", "hlt", "jmp"):
            continue
        if (order[idx + 1] if idx + 1 < len(order) else None) != pc + ins.size:
            labels.add(pc + ins.size)
    # emit
    body = []
    used = {"esp"}
    fn_unsup = 0
    order = sorted(insns)
    fnames = set()
    for idx, pc in enumerate(order):
        ins = insns[pc]
        if pc in labels:
            body.append(f"L{pc:x}:;")
        if ins is None:
            body.append(f'trap_(0x{pc:x}u,"undecodable");return;')
            continue
        g = G(ins)
        m = ins.mnemonic
        ops = list(ins.operands)
        nxt = pc + ins.size
        code = None
        stats["instructions"] += 1
        try:
            if m in ("ret", "repz ret"):
                imm = ops[0].imm if ops else 0
                code = f"esp+={4 + imm};SV;return;"
            elif m in ("int3", "ud2", "hlt"):
                code = f'trap_(0x{pc:x}u,"{m}");return;'
            elif m == "call":
                op = ops[0]
                if op.type == K.X86_OP_IMM:
                    t = op.imm & 0xffffffff
                    if t == nxt:
                        code = f"esp-=4;W32(esp,0x{nxt:x}u);"
                    elif TLO <= t < THI:
                        fnames.add(t)
                        code = f"esp-=4;W32(esp,0x{nxt:x}u);SV;f_{t:08x}();LD;"
                    else:
                        code = f"esp-=4;W32(esp,0x{nxt:x}u);SV;dispatch(0x{t:x}u)();LD;"
                else:
                    code = f"{{u32 t_={g.rd(op)};esp-=4;W32(esp,0x{nxt:x}u);SV;dispatch(t_)();LD;}}"
            elif m == "jmp":
                op = ops[0]
                if op.type == K.X86_OP_IMM:
                    t = op.imm & 0xffffffff
                    if t in labels:
                        code = f"goto L{t:x};"
                    elif TLO <= t < THI:
                        fnames.add(t)
                        code = f"SV;__attribute__((musttail)) return f_{t:08x}();"
                    else:
                        code = f"SV;__attribute__((musttail)) return dispatch(0x{t:x}u)();"
                elif op.type == K.X86_OP_MEM and pc in jumps and jumps[pc] and op.mem.scale == 4 and op.mem.index and not op.mem.base:
                    cases = "".join(f"case 0x{t:x}u:goto L{t:x};" for t in sorted(set(jumps[pc])))
                    code = f'switch({g.rd(op)}){{{cases}default:trap_(0x{pc:x}u,"jump table miss");return;}}'
                    stats["jump tables"] += 1
                else:
                    stats["dynamic jumps"] += 1
                    code = f"{{u32 t_={g.rd(op)};SV;__attribute__((musttail)) return dispatch(t_)();}}"
            elif m[0] == "j":
                t = ops[0].imm & 0xffffffff
                if m == "jecxz":
                    g.used.add("ecx")
                    cond = "ecx==0"
                else:
                    cond = CC[m[1:]]
                code = f"if({cond})goto L{t:x};"
                labels.add(t)
            else:
                code = plain(g, m, ops, ins)
        except (Unsupported, KeyError, IndexError, AttributeError) as e:
            key = m
            unsup[key] += 1
            unsup_ex.setdefault(key, f"{pc:08x} {m} {ins.op_str} [{e}]")
            code = f'trap_(0x{pc:x}u,"{m}");return;'
            fn_unsup += 1
        used |= g.used
        body.append(code)
        # keep control flow correct when the next instruction in address order is not the fall-through
        if m not in ("ret", "retf", "repz ret", "int3", "ud2", "hlt", "jmp"):
            following = order[idx + 1] if idx + 1 < len(order) else None
            if following != nxt:
                labels.add(nxt)
                body.append(f"goto L{nxt:x};")
    used_regs = [r for r in GPR if r in used]
    used_x = [x for x in (f"xmm{i}" for i in range(8)) if any(x in s for s in body)]
    decl = "".join(f"u32 {r}=C.{r};" for r in used_regs) + "".join(f"X {x}=C.{x};" for x in used_x)
    sv = "".join(f"C.{r}={r};" for r in used_regs) + "".join(f"C.{x}={x};" for x in used_x)
    ld = "".join(f"{r}=C.{r};" for r in used_regs) + "".join(f"{x}=C.{x};" for x in used_x)
    fwd |= fnames
    fwd.add(entry)
    all_funcs.append(entry)
    out_lines.append(f"#define SV {sv}\n#define LD {ld}\nvoid f_{entry:08x}(void){{{decl}u8 cf=0,zf=0,sf=0,of=0,pf=0;(void)cf;(void)zf;(void)sf;(void)of;(void)pf;\n" + "\n".join(body) + "\nSV;return;}\n#undef SV\n#undef LD\n")
    if fn_unsup:
        stats["functions with traps"] += 1
    stats["functions"] += 1
    stats[source.get(entry, "?")] += 1
    if len(out_lines) >= 1500:
        flush()
    if stats["functions"] % 10000 == 0:
        print("  ", stats["functions"], "functions", stats["instructions"], "instructions", round(time.time() - t0), "s", flush=True)
    if limit and stats["functions"] >= limit:
        break
flush()
with open(os.path.join(outdir, "functions.txt"), "w") as w:
    for a in sorted(all_funcs):
        w.write(f"{a:08x}\n")
with open(os.path.join(rdir, "translate-report.txt"), "w") as w:
    w.write(json.dumps({"stats": stats, "unsupported": unsup.most_common(), "examples": unsup_ex}, indent=0))
print("STATS", stats.most_common())
print("chunks", chunk_idx, "seconds", round(time.time() - t0))
print("UNSUPPORTED kinds", len(unsup), "instances", sum(unsup.values()))
for k, v in unsup.most_common(40):
    print(f"  {v:6} {unsup_ex[k][:90]}")
