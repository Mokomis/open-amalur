import glob,os,re,struct,collections
R='work/v19-inputs/initial_0.pak/'
fs=sorted(glob.glob(R+'*.shader_bxml'),key=os.path.getsize,reverse=True)
print(len(fs),[os.path.getsize(f) for f in fs[:6]],[os.path.getsize(f) for f in fs[-3:]])
b=open(fs[0],'rb').read();print(b[:64].hex())
tok=collections.Counter()
for f in fs:
    b=open(f,'rb').read()
    for m in re.finditer(rb'[A-Za-z_][A-Za-z0-9_\.]{3,60}',b):tok[m.group().decode()]+=1
print(len(tok));print([k for k,v in tok.most_common(120)])
print('--bins')
for f in sorted(glob.glob(R+'*.bin'),key=os.path.getsize,reverse=True)[:12]:print(os.path.getsize(f),os.path.basename(f),open(f,'rb').read(32).hex())
