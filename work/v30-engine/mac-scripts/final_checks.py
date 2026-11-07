import sys,glob,os,json,re,subprocess,collections
sys.path.insert(0,'work/v19-lighting')
import decode_scene_lighting as D
from pathlib import Path
g=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
def lst(n):
    b=open(f'outputs/{n}-archive-list.txt','rb').read();return [x.strip() for x in b.decode('utf-16' if b[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines() if x.strip()]
for n,a in [('DATA','DATA_0.pak'),('patch','patch_0.pak')]:
    names=[x for x in lst(n) if x.endswith('.space_bxml')];d=Path('work/v19-inputs')/a
    miss=[x for x in names if not (d/x).exists()]
    for i in range(0,len(miss),80):
        subprocess.run([str(g/'modding/pakfileunpacker.exe'),str(g/'data'/a),'unpack',str(Path.cwd()/d),*miss[i:i+80]],cwd=g/'modding',capture_output=True,timeout=500)
rk=collections.defaultdict(list);rerr=[]
for f in glob.glob('work/v19-inputs/*/*.region_bxml'):
    try:rk[D.decode_region(open(f,'rb').read())['region_key']['value']].append(os.path.basename(f))
    except D.DecodeError as e:rerr.append(os.path.basename(f))
ok=miss=err=0;lc=collections.Counter();ex=[]
for f in glob.glob('work/v19-inputs/*/*.space_bxml'):
    try:s=D.decode_space_lights(open(f,'rb').read())
    except Exception as e:err+=1;ex.append(os.path.basename(f));continue
    if s['region_key']['value'] in rk:ok+=1
    else:miss+=1
    lc[len(s['lights'])>0]+=1
    v=[x for l in s['lights'] for x in [l['position'][0]]]
print('spaces key-in-region',ok,'not',miss,'errors',err,ex[:4],'with lights',lc,'region keys',len(rk),'region errs',rerr)
for a in ('DATA_0.pak','patch_0.pak'):
    p=f'work/v19-inputs/{a}/524912.region_bxml';r=D.decode_region(open(p,'rb').read());e=r['environment']['time_keyed']
    print(a,'cubes',len(r['ambient_cubes']),'amb',[e['ambient_cube_index'][k]['value'] for k in D.KEYS],'char',[e['character_ambient_cube_index'][k]['value'] for k in D.KEYS],'cc',{e['color_correction_texture_id'][k]['value'] for k in D.KEYS})
print('zero or short files',[(os.path.basename(f),os.path.getsize(f)) for f in glob.glob('work/v19-inputs/DATA_0.pak/587658*')])
b=open('work/v19-inputs/DATA_0.pak/587658.region_bxml','rb').read();import struct;print(struct.unpack_from('<II',b),len(b))
L=lst('initial')+lst('patch');print('luminance',[x for x in L if 'luminance' in x.lower()][:6])
