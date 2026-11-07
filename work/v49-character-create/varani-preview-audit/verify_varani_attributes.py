"""Independent format/source validator; does not import the exporter or mutate source/pack files."""
from pathlib import Path
import struct,hashlib,json,math
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).digest()
class Invalid(ValueError):pass
def need(ok,s):
 if not ok:raise Invalid(s)
def base_parts(b):
 need(b[:8]==b'OACHAR01','base magic')
 j,c,n,t=struct.unpack_from('<4I',b,8);off=24+2*j
 for _ in range(c):
  frames=struct.unpack_from('<I',b,off)[0];off+=8+frames*j*28
 for _ in range(t):
  w,h=struct.unpack_from('<II',b,off);off+=8+4*w*h
 result=[]
 for i in range(n):
  v,k,p,tex=struct.unpack_from('<IIIi',b,off);off+=16+p*32
  result.append((v,k,b[off:off+52*v],b[off+52*v:off+52*v+4*k]))
  off+=52*v+4*k
 need(off==len(b),'base size')
 return result
def validate(data,base):
 need(len(data)>=64 and len(data)<4*1024*1024,'sidecar size')
 need(data[:8]==b'OACAT01\0','sidecar magic')
 version,total,count,rb,ab,res=struct.unpack_from('<6I',data,8)
 need((version,rb,ab,res)==(1,128,64,0),'header contract')
 need(0<count<=total<=24,'part counts')
 need(data[32:64]==H(base),'base pack identity')
 bp=base_parts(base);need(total==len(bp),'base partcount')
 off=64;previous=-1;boundaries=[64];result=[]
 for _ in range(count):
  need(off+128<=len(data),'part record truncated')
  record=data[off:off+128];off+=128
  index,fab,assembly,mid,stride,nv,ni,flags=struct.unpack_from('<8I',record)
  need(previous<index<total and 0<nv<=1000000 and 0<ni<=6000000 and ni%3==0,'part domain')
  previous=index
  need(stride in (56,60,64),'layout domain')
  n=40 if stride==64 else 32;uv1=32 if stride==64 else None;color=56 if stride==60 else None
  expected_flags=15+(16 if uv1 is not None else 0)+(32 if color is not None else 0)
  need(flags==expected_flags,'source presence mask')
  need(off+nv*(64+stride)<=len(data),'vertex payload truncated')
  attrs=data[off:off+64*nv];off+=64*nv
  raw=data[off:off+stride*nv];off+=stride*nv;boundaries.append(off)
  bv,bi,braw,idx=bp[index]
  need((nv,ni)==(bv,bi),'base shape')
  need(record[32:64]==H(braw) and record[64:96]==H(raw) and record[96:128]==H(idx),'part hashes')
  for v in range(nv):
   s=raw[stride*v:stride*(v+1)];a=attrs[64*v:64*(v+1)];b=braw[52*v:52*(v+1)]
   need(s[:12]==b[:12] and s[24:32]==b[24:32] and s[12:16]==b[32:36],'source join P/UV0/joints')
   need(a[:24]==s[n:n+24],'exact packed TBN')
   need(a[24:32]==s[24:32],'exact UV0')
   need(a[32:40]==(s[uv1:uv1+8] if uv1 is not None else bytes(8)),'exact/absent UV1')
   need(a[40:44]==(s[color:color+4] if color is not None else bytes(4)),'exact/absent RGBA')
   need(struct.unpack_from('<II',a,44)==(flags,v) and a[52:64]==s[:12],'vertex source key')
   need(all(math.isfinite(x) for x in struct.unpack_from('<4f',a,24)),'finite UVs')
  result.append(dict(part=index,fab=fab,assembly=assembly,material=mid,stride=stride,vertices=nv,indices=ni))
 need(off==len(data),'trailer')
 return result,boundaries
def main():
 manifest=json.loads((OUT/'source-join-manifest.json').read_text())
 base=(ROOT/manifest['pack']).read_bytes();data=(OUT/manifest['sidecar']).read_bytes()
 rows,bounds=validate(data,base);checks=0
 for r,m in zip(rows,manifest['parts']):
  need(all(r[k]==m['material_id' if k=='material' else 'source_stride' if k=='stride' else k] for k in r),'manifest identity')
  raw=(ROOT/m['source_mesh']).read_bytes();fb=(ROOT/m['source_fab']).read_bytes()
  need(H(raw).hex()==m['source_mesh_sha256'] and H(fb).hex()==m['source_fab_sha256'],'source unchanged')
  at=m['material_file_offset']
  need(struct.unpack_from('<II',fb,at)==(m['material_id'],m['shader_id']),'exact descriptor material/shader')
  mat=json.loads((OUT/'materials'/str(m['material_id'])).with_suffix('.json').read_text())
  mb=(OUT/'materials'/str(m['material_id'])).with_suffix('.mat_bxml').read_bytes()
  need(H(mb).hex()==mat['sha256'],'material identity')
  for t in mat['source_slots']:need(struct.unpack_from('<II',mb,t['file_offset'])==(t['texture_id'],t['source_slot']),'native material texture slot bytes')
  checks+=1
 failures=[]
 for cut in sorted(set([0,1,7,8,31,32,63,*[x-1 for x in bounds],*bounds[:-1]])):
  try:validate(data[:cut],base);raise AssertionError('accepted truncated '+str(cut))
  except Invalid:failures.append('truncated-'+str(cut))
 for label,at,mask in [('magic',0,1),('version',8,2),('total',12,128),('count',16,128),('record-size',20,1),('stride-size',24,1),('reserved',28,1),('pack-sha',32,1),('partid',64,255),('source-stride',80,1),('presence',92,64),('attribute',192,1),('raw-vb',192+8144*0+1086*64,1)]:
  b=bytearray(data);b[at]^=mask
  try:validate(bytes(b),base);raise AssertionError('accepted corrupt '+label)
  except Invalid:failures.append(label)
 try:validate(data+b'X',base);raise AssertionError('trailer accepted')
 except Invalid:failures.append('trailer')
 badbase=bytearray(base);badbase[100]^=1
 try:validate(data,bytes(badbase));raise AssertionError('wrong base accepted')
 except Invalid:failures.append('wrong-base')
 receipt=dict(result='PASS',weighted_parts=len(rows),vertices=sum(r['vertices'] for r in rows),indices=sum(r['indices'] for r in rows),
  exact_source_join_checks=checks,negative_cases=len(failures),negative_case_names=failures,
  preserved_pack_sha256=H(base).hex(),sidecar_sha256=H(data).hex(),
  normal_mismatch_vertices=sum(m['old_normals_disagree_vertices'] for m in manifest['parts']),
  limits='Offline structural/source verification only. No GPU draw/animation/actual candidate pipeline validation; runtime stream1 remains unknown.')
 (OUT/'validation-receipt.json').write_text(json.dumps(receipt,indent=2))
 print(json.dumps(receipt))
if __name__=='__main__':main()
