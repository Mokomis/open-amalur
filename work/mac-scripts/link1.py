import glob,os,struct,collections,subprocess,json
from pathlib import Path
g=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
d=Path('work/v19-inputs/initial_0.pak')
subprocess.run([str(g/'modding/pakfileunpacker.exe'),str(g/'data/initial_0.pak'),'unpack',str(Path.cwd()/d),'luminance_shift.bxml'],cwd=g/'modding',capture_output=True,timeout=200)
regs={}
for f in glob.glob('work/v19-inputs/*/*.region_bxml'):
    regs.setdefault(os.path.basename(f).split('.')[0],[]).append(f)
c=collections.Counter();miss=[];same=collections.Counter();both=0
for f in glob.glob('work/v19-inputs/*/*.space_bxml'):
    b=open(f,'rb').read();pl,fx=struct.unpack_from('<II',b)
    if 8+pl+fx!=len(b):c['badheader']+=1;continue
    rid=struct.unpack_from('<I',b,8+0x34)[0]
    arch=os.path.basename(os.path.dirname(f))
    if rid==0:c['zero']+=1;continue
    if str(rid) in regs:
        c['match']+=1
        if len(regs[str(rid)])>1:both+=1
        same[arch.split('_')[0]+'->'+','.join(sorted(os.path.basename(os.path.dirname(x)).split('_')[0] for x in regs[str(rid)]))]+=1
    else:c['nomatch']+=1;miss.append((os.path.basename(f),arch,rid))
print(dict(c),'regions',len(regs),'target has both',both);print(same.most_common(8));print(miss[:15])
L=set()
for n in('DATA','initial','patch'):
    x=open(f'outputs/{n}-archive-list.txt','rb').read();L|={s.strip() for s in x.decode('utf-16' if x[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines()}
print('missing listed as other',[(m[2],[k for k in (f'{m[2]}.region_bxml',f'{m[2]}.koaregion') if k in L]) for m in miss[:8]])
p=d/'luminance_shift.bxml';b=p.read_bytes();print('lum',len(b));print(b[:400]);
