"""Compose an isolated closed-container preview; source/base assets never overwritten."""
from pathlib import Path
import os,json,struct,hashlib,re
import numpy as np
P=Path(__file__).resolve().parents[3];V=Path(__file__).resolve().parent
B=V/'probe-preview';S=P/'work/v48-opening/initial-sword-visuals/closed-idle-candidate';O=V/'probe-preview-closed-container';NONE=0xffffffff
def sha(b):return hashlib.sha256(b).hexdigest()
def atomic(path,b):
 t=path.with_name(path.name+'.new');t.write_bytes(b);t.replace(path)
def canonical_native(b):
 r=list(struct.unpack('<9I12f',b))
 if r[0]==11:r[20]=0.0 # packed UV.w is unused by the exact family11 shader.
 return struct.pack('<9I12f',*r)
def geo(b):
 magic,nv,ni,nd,vs,rs=struct.unpack_from('<8s5I',b);assert (magic,vs,rs)==(b'OARGEO1\0',76,48)
 va=28+nd*48;ia=va+nv*76;assert ia+ni*4==len(b)
 runs=[list(struct.unpack_from('<4I6fIf',b,28+i*48)) for i in range(nd)]
 for r in runs:assert r[1]+r[2]<=ni and r[2]%3==0
 verts=b[va:ia];ind=np.frombuffer(b,'<u4',ni,ia).copy();assert int(ind.max())<nv
 return nv,ni,runs,verts,ind
def build_geo(runs,verts,ind):
 return struct.pack('<8s5I',b'OARGEO1\0',len(verts)//76,len(ind),len(runs),76,48)+b''.join(struct.pack('<4I6fIf',*r) for r in runs)+verts+ind.astype('<u4').tobytes()
assert not O.exists(),'Use a new root; preserve previous stage.'
source=json.loads((S/'manifest.json').read_text());base=json.loads((B/'preview-manifest.json').read_text())
# Fingerprint base files before linking. Every changed child is replaced atomically.
before={str(f.relative_to(B)):sha(f.read_bytes()) for f in B.rglob('*') if f.is_file()}
for f in B.rglob('*'):
 d=O/f.relative_to(B)
 if f.is_dir():d.mkdir(parents=True,exist_ok=True)
 else:d.parent.mkdir(parents=True,exist_ok=True);os.link(f,d)
W=O/'world';bm=(B/'world/materials.bin').read_bytes();bn=(B/'world/native-materials.bin').read_bytes()
mc=struct.unpack_from('<I',bm)[0];assert len(bm)==4+mc*28 and bn[:8]==b'OANM001\0' and struct.unpack_from('<I',bn,8)[0]==mc and len(bn)==12+mc*84
mrows=[bm[4+i*28:4+(i+1)*28] for i in range(mc)];nrows=[bn[12+i*84:12+(i+1)*84] for i in range(mc)]
base_ids={r['native_material']:r['local_material'] for r in base['materials']}
index=(B/'world/index.bin').read_bytes();assert index[:4]==b'OAWI'
tile,ncells,tc,flags=struct.unpack_from('<fIII',index,4);assert len(index)==20+ncells*48
thash={sha((W/f't{i}.bin').read_bytes()):i for i in range(tc)};tmap={};addedtex=[]
for i in range(source['texture_count']):
 payload=(S/f'world/t{i}.bin').read_bytes();h=sha(payload)
 if h not in thash:
  thash[h]=tc;atomic(W/f't{tc}.bin',payload);addedtex.append(dict(new=tc,source=i,sha256=h));tc+=1
 tmap[i]=thash[h]
sm=(S/'world/materials.bin').read_bytes();sn=(S/'world/native-materials.bin').read_bytes();mmap={};mreceipt=[]
for p in source['profiles']:
 i=p['local_material'];raw=list(struct.unpack_from('<7I',sm,4+i*28));raw[1:]=[tmap[x] if x!=NONE else NONE for x in raw[1:]]
 nr=list(struct.unpack_from('<9I12f',sn,12+i*84));nr[1:9]=[tmap[x] if x!=NONE else NONE for x in nr[1:9]]
 mb=struct.pack('<7I',*raw);nb=struct.pack('<9I12f',*nr)
 old=base_ids.get(p['native_material'])
 if old is not None:
  assert mrows[old]==mb and canonical_native(nrows[old])==canonical_native(nb),(p['native_material'],'material mismatch')
  mmap[i]=old;action='reused same source material'
 else:
  mmap[i]=len(mrows);mrows.append(mb);nrows.append(nb);action='added exact source profile'
 mreceipt.append(dict(source_material=p['native_material'],local=mmap[i],action=action,source_profile=p))
atomic(W/'materials.bin',struct.pack('<I',len(mrows))+b''.join(mrows));atomic(W/'native-materials.bin',b'OANM001\0'+struct.pack('<I',len(nrows))+b''.join(nrows))
ridx=(B/'world/region-index.bin').read_bytes();magic,nr,oldmc,scale,res=struct.unpack_from('<8sIIfI',ridx);assert magic==b'OARGIDX1' and oldmc==mc
regions={tuple(struct.unpack_from('<ii',ridx,24+i*40)):list(struct.unpack_from('<iiII6f',ridx,24+i*40)) for i in range(nr)}
cells={tuple(struct.unpack_from('<ii',index,20+i*48)):list(struct.unpack_from('<ii6f4I',index,20+i*48)) for i in range(ncells)}
added=[]
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('mid','<u4'),('flags','<u4')])
for f in (S/'world').glob('r*_*.bin'):
 xy=tuple(map(int,f.stem[1:].split('_')));anv,ani,ar,av,ai=geo(f.read_bytes())
 target=W/f.name
 if target.exists():nv,ni,r,v,ind=geo(target.read_bytes())
 else:nv=ni=0;r=[];v=b'';ind=np.array([],dtype='<u4')
 offset=len(r);original_runs=[x.copy() for x in ar]
 for row in ar:row[0]=mmap[row[0]];row[1]+=ni
 out=build_geo(r+ar,v+av,np.concatenate([ind,ai+nv]));atomic(target,out)
 onv,oni,orr,ov,oi=geo(out);assert ov[:len(v)]==v and ov[len(v):]==av and np.array_equal(oi[:ni],ind) and np.array_equal(oi[ni:]-nv,ai)
 for old,new in zip(original_runs,orr[offset:]):assert old[2:]==new[2:]
 vv=np.frombuffer(ov,DT)['v'][:,:3];lo=vv.min(0).tolist();hi=vv.max(0).tolist();regions[xy]=[*xy,oni//3,len(orr),*lo,*hi]
 if xy in cells:cell=cells[xy];cell[2:5]=np.minimum(cell[2:5],lo).tolist();cell[5:8]=np.maximum(cell[5:8],hi).tolist()
 else:cells[xy]=[*xy,*lo,*hi,0,0,0,0]
 added.append(dict(cell=xy,first_object_range=offset,range_count=len(ar),vertices=anv,triangles=ani//3,file=f.name,merged_sha256=sha(out)))
atomic(W/'region-index.bin',struct.pack('<8sIIfI',b'OARGIDX1',len(regions),len(mrows),scale,res)+b''.join(struct.pack('<iiII6f',*row) for _,row in sorted(regions.items())))
atomic(W/'index.bin',b'OAWI'+struct.pack('<fIII',tile,len(cells),tc,flags)+b''.join(struct.pack('<ii6f4I',*row) for _,row in sorted(cells.items())))
# The reused source family11 row already has a source505647 probe binding. No fallback.
probe=(W/'material-probe-map.bin').read_bytes();assert probe[:8]==b'OAPM001\0';pairs=[struct.unpack_from('<II',probe,12+i*8) for i in range(struct.unpack_from('<I',probe,8)[0])]
assert (mmap[1],505647) in pairs
assert all(sha((B/name).read_bytes())==h for name,h in before.items()),'Base preview mutated'
assert (O/'scene-profile.bin').read_bytes()==(B/'scene-profile.bin').read_bytes()
report=dict(status='Isolated composed ordinary-default CloseIdle actor preview; no GPU proof yet',source_GOR=1790948,embedded_instance=1789992,source_fab=1789717,source_manifest_sha256=sha((S/'manifest.json').read_bytes()),added=added,materials=mreceipt,added_textures=addedtex,material_count=len(mrows),texture_count=tc,base_files_sha256_unchanged=before,lighting_base_unchanged=True,limits=['SourceClosedIdle ordinary default only; death/override state conditions remain explicit.','17rigid supported parts only;3remapped/HardLight surfaces withheld; sword visible payload not fully admitted.','Static closed bake, no animation/interaction/inventory/door collision behavior yet.','No native original scene screenshot parity or Android runtime validation claimed.'])
(O/'closed-container-merge.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','added','material_count','texture_count','lighting_base_unchanged']},indent=2))
