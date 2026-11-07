from pathlib import Path
import sys,struct,json,collections,math
import numpy as np
sys.dont_write_bytecode=True
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_fab
A=P/'work/v49-character-create/vertex-contract-audit';m=json.loads((A/'source-join-manifest.json').read_text());b=(P/m['pack']).read_bytes()
J,C,N,T=struct.unpack_from('<4I',b,8);o=24+((J+1)//2)*4
for _ in range(C):
 n=struct.unpack_from('<I',b,o)[0];o+=8+n*J*28
for _ in range(T):
 w,h=struct.unpack_from('<II',b,o);o+=8+w*h*4
parts=[]
for _ in range(N):
 nv,ni,pc,tx=struct.unpack_from('<IIIi',b,o);o+=16
 parts.append((np.frombuffer(b,dtype=[('j','<u4'),('q','<f4',4),('t','<f4',3)],count=pc,offset=o),o+pc*32))
 o+=pc*32+52*nv+4*ni
S=json.loads((P/'work/v20-inputs/symbols.json').read_text());bn=S['ragdoll_bone_mappings']
rig=amalur_fab.parse_file(P/'work/v20-inputs/patch_0.pak/456813.fab_bxml')
for r in m['parts']:
 raw=(P/r['source_mesh']).read_bytes();v=np.ndarray((r['vertices'],r['source_stride']),'u1',raw,r['source_vb_data_file_offset'])
 w=np.ndarray((r['vertices'],4),'<i2',raw,r['source_vb_data_file_offset']+16,(r['source_stride'],2)).astype(float)/32767
 old=np.ndarray((r['vertices'],4),'<f4',b,parts[r['part']][1]+36,(52,4)).astype(float)
 residual=1-w[:,:3].sum(1)
 f=amalur_fab.parse_file(P/r['source_fab']);d=f['mesh_descriptors'][r['assembly']]
 mapped=[]
 for rem in d['remaps']:
  sh=f['bones'][rem['bone_index']]['name_hash_u32'];mapped.append(bn.get(str(sh),str(sh)))
 oldnames=[bn.get(str(rig['bones'][int(z)]['name_hash_u32']),str(z)) for z in parts[r['part']][0]['j']]
 print(r['part'],r['label'],'summinmax',w.sum(1).min(),w.sum(1).max(),'negative',int((w<0).sum()),'residualmin',residual.min(),'4diffcount',int((abs(w[:,3]-residual)>1e-10).sum()),'oldWerr',abs(old-np.column_stack([w[:,:3],np.maximum(0,residual)])).max(),'sourcepal',len(mapped),'oldpal',len(oldnames))
 print('SOURCE',mapped if r['part'] in [0,1,2,4,5] else mapped[:3]);print('OLD',oldnames if r['part'] in [0,1,2,4,5] else oldnames[:3])
