#!/usr/bin/env python3
"""d3d_needs.py <v30 dir>: what the game uses of Direct3D, across all recordings, and a census of its shader instructions."""
import collections,glob,os,re,struct,sys
E=sys.argv[1]
OPS="ADD AND BREAK BREAKC CALL CALLC CASE CONTINUE CONTINUEC CUT DEFAULT DERIV_RTX DERIV_RTY DISCARD DIV DP2 DP3 DP4 ELSE EMIT EMITTHENCUT ENDIF ENDLOOP ENDSWITCH EQ EXP FRC FTOI FTOU GE IADD IF IEQ IGE ILT IMAD IMAX IMIN IMUL INE INEG ISHL ISHR ITOF LABEL LD LD_MS LOG LOOP LT MAD MIN MAX CUSTOMDATA MOV MOVC MUL NE NOP NOT OR RESINFO RET RETC ROUND_NE ROUND_NI ROUND_PI ROUND_Z RSQ SAMPLE SAMPLE_C SAMPLE_C_LZ SAMPLE_L SAMPLE_D SAMPLE_B SQRT SWITCH SINCOS UDIV ULT UGE UMUL UMAD UMAX UMIN USHR UTOF XOR DCL_RESOURCE DCL_CONSTANT_BUFFER DCL_SAMPLER DCL_INDEX_RANGE DCL_GS_OUTPUT_TOPOLOGY DCL_GS_INPUT_PRIMITIVE DCL_MAX_OUTPUT_VERTEX DCL_INPUT DCL_INPUT_SGV DCL_INPUT_SIV DCL_INPUT_PS DCL_INPUT_PS_SGV DCL_INPUT_PS_SIV DCL_OUTPUT DCL_OUTPUT_SGV DCL_OUTPUT_SIV DCL_TEMPS DCL_INDEXABLE_TEMP DCL_GLOBAL_FLAGS".split()
recs=[d for d in glob.glob(E+"/oa_rec-*") if os.path.isdir(d)]+[E+"/run-rec/oa_rec"]
print("recordings",len(recs))
calls=collections.Counter()
for R in recs:
    if os.path.exists(R+"/stats.txt"):
        for l in open(R+"/stats.txt"):
            p=l.split()
            if len(p)==3: calls[(p[0],p[1])]=max(calls[(p[0],p[1])],int(p[2]))
print("-- methods used, excluding the 1-count ones (those are DXVK/our own setup probes)")
print(sorted(f"{k[0][0]}:{k[1]}" for k,v in calls.items() if v>1))
print("-- called once",sorted(k[1] for k,v in calls.items() if v==1))
fmt=collections.Counter();pred=0;layouts=set();chain=set()
for R in recs:
    if not os.path.exists(R+"/resources.txt"):continue
    for l in open(R+"/resources.txt",errors="replace"):
        p=l.split()
        if len(p)<2:continue
        if p[1]=="tex2d":
            kv=dict(x.split("=") for x in p[3:] if "=" in x); fmt[(kv.get("fmt"),kv.get("bind"),kv.get("usage"))]+=1
        elif p[1]=="tex3d": fmt[("3d",p[2],)]+=1
        elif p[1]=="layout": layouts.add(" ".join(p[2:]))
        elif p[1]=="swapchain": chain.add(" ".join(p[2:]))
print("-- texture format,bind,usage",sorted(fmt.items(),key=lambda x:-x[1])[:40])
print("-- input layouts",len(layouts))
print("-- swapchains",chain)
sh={}
for R in recs:
    for p in glob.glob(R+"/shaders/*.dxbc"): sh[os.path.basename(p)]=p
print("-- unique shaders",len(sh),collections.Counter(k[:2] for k in sh))
ops=collections.Counter();inshaders=collections.Counter();sizes=[];res=collections.Counter();flags=collections.Counter();idx=0;unk=collections.Counter()
for k,p in sh.items():
    d=open(p,"rb").read();n=struct.unpack_from("<I",d,28)[0];body=None
    for i in range(n):
        o=struct.unpack_from("<I",d,32+4*i)[0]
        if d[o:o+4] in(b"SHEX",b"SHDR"):
            sz=struct.unpack_from("<I",d,o+4)[0];body=d[o+8:o+8+sz]
    if not body:continue
    t=struct.unpack(f"<{len(body)//4}I",body[:len(body)//4*4]);i=2;seen=set();count=0
    while i<len(t):
        w=t[i];op=w&0x7ff;l=(w>>24)&0x7f
        if op==53: l=t[i+1]
        if l==0:break
        nm=OPS[op] if op<len(OPS) else f"op{op}"
        ops[nm]+=1;seen.add(nm);count+=1
        if op==88: res[(w>>11)&0x1f]+=1
        if op==106: flags[(w>>11)&0x1fff]+=1
        i+=l
    for s in seen: inshaders[s]+=1
    sizes.append(count)
sizes.sort()
print("instructions per shader median",sizes[len(sizes)//2],"max",sizes[-1],"total",sum(sizes))
print("-- opcode: count, shaders");
for k,v in ops.most_common(): print(f"   {k:22}{v:8}{inshaders[k]:6}")
print("resource dimensions (2=2D,3=3D,4=cube)",res,"global flags",flags)
