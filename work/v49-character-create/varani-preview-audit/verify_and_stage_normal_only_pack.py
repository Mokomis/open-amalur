from pathlib import Path
import json,struct,hashlib,math,ast
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent
def H(b):return hashlib.sha256(b).hexdigest()
def ck(c,s):
 if not c:raise ValueError(s)
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return(w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
def conjugate(q):return(-q[0],-q[1],-q[2],q[3])
def rotate(q,p):return mul(mul(q,(*p,0.)),conjugate(q))[:3]
def skel(b):
 n=struct.unpack_from('<I',b,20)[0];a=28+struct.unpack_from('<i',b,28)[0];pa=32+struct.unpack_from('<i',b,32)[0];na=36+struct.unpack_from('<i',b,36)[0]
 parents=struct.unpack_from('<'+'H'*n,b,pa);names=struct.unpack_from('<'+'I'*n,b,na);world=[]
 for i in range(n):
  s=struct.unpack_from('<12f',b,a+48*i);q=conjugate(s[:4]);t=s[4:7];j=parents[i]
  ck(all(x==1 for x in s[8:11]),'nonunit source rig')
  if j!=65535:
   ck(j<i,'parent order');pq,pt=world[j];v=rotate(pq,t);q=mul(pq,q);t=tuple(pt[k]+v[k] for k in range(3))
  world.append((q,t))
 return parents,names,world
def parts(b):
 j,c,n,t=struct.unpack_from('<4I',b,8);a=24+((j+1)//2)*4
 for _ in range(c):nf=struct.unpack_from('<I',b,a)[0];a+=8+nf*j*28
 for _ in range(t):w,h=struct.unpack_from('<II',b,a);a+=8+w*h*4
 out=[]
 for i in range(n):
  nv,ni,pc,tx=struct.unpack_from('<IIIi',b,a);a+=16;pal=a;v=a+32*pc;idx=v+52*nv;a=idx+4*ni;out.append(dict(nv=nv,ni=ni,pc=pc,pal=pal,v=v,idx=idx))
 ck(a==len(b),'baseEOF');return out
def main():
 m=json.loads((O/'source-join-manifest.json').read_text());base=(P/m['pack']).read_bytes();ck(H(base)==m['pack_sha256'],'basehash');ps=parts(base)
 rigp=P/'work/v20-inputs/patch_0.pak/456813.fab_bxml';rp,rnames,rworld=skel(rigp.read_bytes());rindex={h:i for i,h in enumerate(rnames)}
 ck(struct.unpack_from('<I',base,8)[0]==len(rnames),'rigcount')
 ck(struct.unpack_from('<'+'H'*len(rp),base,24)==rp,'source rig parent order')
 weighted=[];patched=bytearray(base);allowed=set();changednormals=0
 for r in m['parts']:
  p=ps[r['part']];fb=(P/r['source_fab']).read_bytes();raw=(P/r['source_mesh']).read_bytes();ck(H(fb)==r['source_fab_sha256'] and H(raw)==r['source_mesh_sha256'],'sourcehash')
  sp,snames,sworld=skel(fb);desc=r['descriptor_offset'];sc=struct.unpack_from('<I',fb,desc+28)[0];ck(sc==p['pc'],'sourceown palettecount')
  mapping=[];palette_exact=True;maxerr=0
  for slot in range(sc):
   at=desc+32+slot*52;sid=struct.unpack_from('<i',fb,at+48)[0];cur=sid;chain=[]
   while snames[cur] not in rindex:
    chain.append(cur);cur=sp[cur];ck(cur!=65535 and len(chain)<128,'source ancestor mapping')
   j=rindex[snames[cur]];q,t=rworld[j];iq=conjugate(q);v=rotate(iq,t);it=tuple(-x for x in v);gold=struct.pack('<I7f',j,*iq,*it)
   old=base[p['pal']+slot*32:p['pal']+(slot+1)*32];ck(struct.unpack_from('<I',old)[0]==j,'own assembly rig mapping')
   err=max(abs(x-y) for x,y in zip(struct.unpack_from('<7f',old,4),struct.unpack_from('<7f',gold,4)));maxerr=max(maxerr,err);palette_exact&=old==gold
   ck(err<1e-5,'existing inverse common rest differs')
   mapping.append(dict(slot=slot,source_bone=sid,source_hash=snames[sid],target_rig_joint=j,ancestor_chain=chain,record_byte_exact=old==gold,max_error=err))
  n=40 if r['source_stride']==64 else 32;vb=r['source_vb_data_file_offset'];stride=r['source_stride'];normchanged=0
  for vi in range(p['nv']):
   sv=vb+vi*stride;old=p['v']+52*vi
   ck(raw[sv:sv+12]==base[old:old+12] and raw[sv+24:sv+32]==base[old+24:old+32] and raw[sv+12:sv+16]==base[old+32:old+36],'source vertex join')
   N=struct.pack('<3f',*(max(-1,x/32767) for x in struct.unpack_from('<3h',raw,sv+n)))
   normchanged+=N!=base[old+12:old+24];patched[old+12:old+24]=N;allowed.update(range(old+12,old+24))
  changednormals+=normchanged;weighted.append(dict(part=r['part'],fab=r['fab'],assembly=r['assembly'],source_palette_count=sc,palette_byte_exact=palette_exact,palette_max_error=maxerr,palette_mapping=mapping,changed_normal_vertices=normchanged))
 ck(len(patched)==len(base),'noresize')
 changed=[i for i,(x,y) in enumerate(zip(patched,base)) if x!=y];ck(all(i in allowed for i in changed),'onlynormalbytes')
 # Palette, indices, positions, UV,joints,weights, clips/textures/all headers are covered by the full-byte allowlist.
 target=O/'corrected/character.bin';target.parent.mkdir(exist_ok=True);target.write_bytes(patched)
 reread=target.read_bytes();ck(reread==patched,'exactoutput');ck(H((P/m['pack']).read_bytes())==m['pack_sha256'],'original untouched')
 report=dict(status='PASS independent source/palette reconstruction +normals-only newpack',base_pack=m['pack'],base_sha256=H(base),corrected_pack=str(target.relative_to(P)),corrected_sha256=H(patched),pack_bytes=len(base),parts=len(ps),weighted_parts=len(weighted),weighted_vertices=sum(r['vertices'] for r in m['parts']),normal_vertices_changed=changednormals,allowed_normal_span_bytes=len(allowed),actual_changed_bytes=len(changed),palette_all_slots_match_own_descriptor=True,palette_all_inverse_records_byte_exact=all(x['palette_byte_exact'] for x in weighted),weighted=weighted,preserved='Everybyteoutside52BvertexnormalXYZ@12..23 unchanged: clips/textures/header/palettes/P/UV/jointindices/weights/indexorder/rigidweapons remain original.',limits=['Current common64rig/facialancestor policy preserved; not a native full-face rig reconstruction.','No GPU rendering/animation or source defaultcolor application claim.','Do not apply base-bound OACAT companion to correctedpack; it intentionally matches original SHA only.'])
 (O/'independent-pack-validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['status','corrected_sha256','parts','weighted_parts','normal_vertices_changed','actual_changed_bytes','palette_all_inverse_records_byte_exact']}))
if __name__=='__main__':main()
