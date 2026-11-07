from pathlib import Path
import hashlib,json,struct,subprocess
R=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
ARCH=[('DATA_0.pak','DATA'),('initial_0.pak','initial'),('patch_0.pak','patch')]
LIST={}
for a,label in ARCH:
 b=(R/f'outputs/{label}-archive-list.txt').read_bytes()
 LIST[a]=set(x.strip() for x in b.decode('utf-16' if b[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines())
def H(b):return hashlib.sha256(b).hexdigest()
def extract(names):
 result={};receipts=[]
 for archive,label in ARCH:
  selected=sorted(set(names)&LIST[archive]);todo=[];dst=O/'source'/archive;dst.mkdir(parents=True,exist_ok=True)
  for name in selected:
   existing=[d/archive/name for d in [O/'source',R/'work/v49-character-create/source',R/'work/v20-inputs']]
   old=next((p for p in existing if p.exists()),None)
   if old:result[name]=old
   else:todo.append(name)
  for i in range(0,len(todo),30):
   batch=todo[i:i+30]
   z=subprocess.run([str(GAME/'modding/pakfileunpacker.exe'),str(GAME/'data'/archive),'unpack',str(dst),*batch],cwd=GAME/'modding',capture_output=True,timeout=240)
   (O/f'extract-{archive}-{H(chr(10).join(batch).encode())[:10]}.log').write_bytes(z.stdout+z.stderr)
   if z.returncode:raise RuntimeError('extract failed '+str(z.returncode))
   for name in batch:
    p=dst/name;assert p.exists();result[name]=p
  receipts.append(dict(archive=archive,requested_present=len(selected),extracted=len(todo),reused=len(selected)-len(todo)))
 out={name:dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=H(p.read_bytes())) for name,p in result.items()}
 log=O/'asset-source-receipts.jsonl'
 with log.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(archives=receipts,selected=out))+'\n')
 return result
def bundle(sid):
 p=extract([f'{sid}.bundle'])[f'{sid}.bundle'];b=p.read_bytes();n,m=struct.unpack_from('<II',b,8)
 ids=list(struct.unpack_from('<'+str(n)+'I',b,16));kinds=list(b[16+4*(n+m):16+4*(n+m)+n])
 return dict(path=str(p.relative_to(R)),sha256=H(b),count=n,typed_count=m,ids=ids,kinds=kinds)
