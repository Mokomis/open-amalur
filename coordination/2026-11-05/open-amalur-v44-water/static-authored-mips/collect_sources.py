from pathlib import Path
import json,hashlib,struct
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');R=P/'work/v44-native-fidelity';Q=R/'water-research/static-authored-mips';Q.mkdir(parents=True,exist_ok=True)
g=json.loads((R/'static-overlay/manifest.json').read_text());plan=json.loads((R/'water-research/static-material-followup/material-texture-plan.json').read_text());rows=[]
for row in g['extra_textures']:
 tid=row['texture']
 if not 658<=tid<=676:continue
 src=row['source'];asset=src['asset'];initial=P/src['source'];arch=initial.parent.name
 candidates=set()
 for folder in [initial.parent,P/'work/v20-inputs'/arch,R/'water-research/static-material-followup/inputs'/arch]:
  if folder.exists():
   for p in folder.glob(f'{asset}*.dds'):
    if p.name==f'{asset}.dds' or p.name.startswith(f'{asset}_'):candidates.add(p)
 files=[]
 for p in sorted(candidates):
  raw=p.read_bytes()
  if raw[16:20]!=b'KEEN' or raw[29]not in (1,5):continue
  w,h=struct.unpack_from('<2H',raw,20);fmt=raw[29];nm=struct.unpack_from('<H',raw,35)[0];o=38;levels=[]
  for i in range(nm):
   lw,lh=max(1,w>>i),max(1,h>>i);n=((lw+3)//4)*((lh+3)//4)*(8 if fmt==1 else 16);bc=raw[o:o+n];assert len(bc)==n
   levels.append(dict(level=i,width=lw,height=lh,offset=o,bytes=n,sha256=hashlib.sha256(bc).hexdigest()));o+=n
  assert o==len(raw),(p,o,len(raw));files.append(dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),format='VK_FORMAT_BC1_RGBA_UNORM_BLOCK'if fmt==1 else'VK_FORMAT_BC3_UNORM_BLOCK',width=w,height=h,mips=nm,levels=levels))
 users=[dict(native_material=m['material'],slot=s['slot'])for m in plan['materials']for s in m['maps']if s['asset']==asset and s['kind']==src['kind']]
 rows.append(dict(texture=tid,asset=asset,kind=src['kind'],old_texture=row,material_users=users,files=files))
assert len(rows)==19 and all(r['files']for r in rows)
(Q/'source-catalog.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
