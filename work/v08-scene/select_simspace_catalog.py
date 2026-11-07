from pathlib import Path
import platform,json,subprocess,sys,struct,hashlib
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';rows=[]
for p in sorted((r/'work/scene-inputs-v07').glob('*/simspace_init*.bin')):
 b=p.read_bytes();v,n=struct.unpack_from('<II',b);assert v==1 and len(b)==8+n*8;u=struct.unpack_from('<'+str(n*2)+'I',b,8);rows.append({'file':str(p),'count':n,'sha256':hashlib.sha256(b).hexdigest(),'pairs':dict(zip(u[:n],u[n:]))})
conflicts=[];seen={}
for row in rows:
 for ident,h in row['pairs'].items():
  if ident in seen and seen[ident]['hash']!=h:conflicts.append({'id':ident,'earlier':seen[ident],'later':{'file':row['file'],'hash':h}})
  seen[ident]={'file':row['file'],'hash':h}
for row in rows:del row['pairs']
receipt={'selection':'patch_0.pak/simspace_init.bin only','reason':'Explicit Android preview catalog choice after agreeing-union rejected conflicting ID/name variants; not a claim of native mount precedence','sources':rows,'conflicts':conflicts}
(out/'simspace-catalog-selection.json').write_text(json.dumps(receipt,indent=2))
subprocess.run([sys.executable,str(r/'work/merge_asset_snapshots.py'),'--root',str(r/'work/scene-inputs-v07'),'--glob','patch_0.pak/simspace_init.bin','--output',str(out/'assets/simspace_init.bin')],check=True)
p=out/'asset-macros.json';m=json.loads(p.read_text());assert not any(x['name']=='SPACE_ID' for x in m);m.append({'name':'SPACE_ID','category':50,'file':'simspace_init.bin','selection':receipt['selection']});p.write_text(json.dumps(m,indent=2));print(json.dumps({'conflicts':len(conflicts),'selection':receipt['selection']}))
