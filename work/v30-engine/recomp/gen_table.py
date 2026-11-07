#!/usr/bin/env python3
"""gen_table.py <out dir>: write the sorted guest-address to function table used by dispatch()."""
import os, sys

out = sys.argv[1]
fs = [l.strip() for l in open(os.path.join(out, "functions.txt")) if l.strip()]
fs = sorted(set(fs), key=lambda x: int(x, 16))
with open(os.path.join(out, "table.c"), "w") as w:
    w.write('#include "rt.h"\n')
    for a in fs:
        w.write(f"void f_{a}(void);\n")
    w.write("typedef struct { u32 addr; fn f; } func_entry;\nconst func_entry g_funcs[] = {\n")
    for a in fs:
        w.write(f"{{0x{a}u,f_{a}}},\n")
    w.write(f"}};\nconst u32 g_nfuncs = {len(fs)};\n")
print("table entries", len(fs))
