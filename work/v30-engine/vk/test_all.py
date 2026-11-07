#!/usr/bin/env python3
"""test_all.py <v30 dir>: translate every recorded shader and validate it with spirv-val. Stores nothing outside work/v30-engine."""
import collections,glob,os,subprocess,sys
E=sys.argv[1]; V=E+"/vk"; O=V+"/spv"; os.makedirs(O,exist_ok=True)
val=os.path.join(E,"..","..","tools","android","android-ndk-r30","shader-tools","windows-x86_64","spirv-val.exe")
sh={}
for p in glob.glob(E+"/oa_rec-*/shaders/*.dxbc")+glob.glob(E+"/run-rec/oa_rec/shaders/*.dxbc"): sh[os.path.basename(p)]=p
ok=0;tf=collections.Counter();vf=collections.Counter();ex={}
for k,p in sorted(sh.items()):
    out=os.path.join(O,k[:-5]+".spv")
    r=subprocess.run([V+"/dxbc_test.exe",p,out],capture_output=True,text=True)
    if r.returncode:
        m=r.stdout.split(": ",1)[-1].strip() or f"exit {r.returncode}"; tf[m]+=1; ex.setdefault(m,k); continue
    r=subprocess.run([val,"--target-env","vulkan1.1",out],capture_output=True,text=True)
    if r.returncode:
        m=(r.stderr or r.stdout).strip().split("\n")[0][:150]; vf[m]+=1; ex.setdefault(m,k); continue
    ok+=1
print("shaders",len(sh),"valid",ok,"translate failures",sum(tf.values()),"validation failures",sum(vf.values()))
for m,n in tf.most_common(14): print(" T",n,m,ex[m])
for m,n in vf.most_common(14): print(" V",n,m,ex[m])
