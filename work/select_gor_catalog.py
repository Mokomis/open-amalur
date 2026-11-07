from pathlib import Path
import platform,json,subprocess,sys,struct,hashlib
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';rows=[]
for p in sorted((r/'work/scene-inputs-v07').glob('*/globalobjectref_init*.bin')):
 b=p.read_bytes();v,n=struct.unpack_from('<II',b);assert v==1 and len(b)==8+n*8;u=struct.unpack_from('<'+str(n*2)+'I',b,8);rows.append({'file':str(p),'count':n,'sha256':hashlib.sha256(b).hexdigest(),'pairs':dict(zip(u[:n],u[n:]))})
conflicts=[];seen={};by_hash={}
for row in rows:
 for ident,h in row['pairs'].items():
  if ident in seen and seen[ident]['hash']!=h:conflicts.append({'id':ident,'earlier':seen[ident],'later':{'file':row['file'],'hash':h}})
  if h in by_hash and by_hash[h]['id']!=ident:conflicts.append({'hash':h,'earlier':by_hash[h],'later':{'file':row['file'],'id':ident}})
  by_hash[h]={'file':row['file'],'id':ident}
  seen[ident]={'file':row['file'],'hash':h}
for row in rows:del row['pairs']
receipt={'selection':'initial_0.pak/globalobjectref_init.bin only','reason':'Explicit base-game Android preview catalog; agreeing union rejected catalog name/ID conflicts; other variants remain excluded. Not a claim of native mount precedence','sources':rows,'conflicts':conflicts}
(out/'globalobjectref-catalog-selection.json').write_text(json.dumps(receipt,indent=2))
subprocess.run([sys.executable,str(r/'work/merge_asset_snapshots.py'),'--root',str(r/'work/scene-inputs-v07'),'--glob','initial_0.pak/globalobjectref_init.bin','--output',str(out/'assets/globalobjectref_init.bin')],check=True)
p=out/'asset-macros.json';m=json.loads(p.read_text());assert not any(x['name']=='GOR_ID' for x in m);m.append({'name':'GOR_ID','category':48,'file':'globalobjectref_init.bin','selection':receipt['selection']});p.write_text(json.dumps(m,indent=2));print(json.dumps({'conflicts':len(conflicts),'selection':receipt['selection']}))
