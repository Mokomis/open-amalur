from pathlib import Path
from PIL import Image
import sys,json,struct,hashlib,ast,io
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;P=Q.parents[2]
H=P/'work/v44-native-fidelity/foliage-research/leaf-authored-auxiliary/build_authored_leaf_auxiliary.py'
tree=ast.parse(H.read_text(encoding='utf-8'));defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['rgb565','ref_sample']]
exec(compile(ast.Module(body=defs,type_ignores=[]),str(H),'exec'))
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 cat=json.loads((Q/'first-room-texture-catalog.json').read_text());O=Q/'candidate-first-room';B=O/'textures-native-bc';R=O/'textures-portable-512';Z=O/'textures-cube-native'
 for d in [B,R,Z]:d.mkdir(parents=True,exist_ok=True)
 out=[]
 for s in cat['selected']:
  tid=s['asset'];c=s['carrier'];raw=(P/c['path']).read_bytes();fmt=c['format'];assert fmt in [1,5]
  chunks=[];levels=[]
  for l in c['levels']:
   data=raw[l['source_offset']:l['source_offset']+l['bytes']];assert len(data)==l['bytes'];chunks.append(data);levels.append({**l,'bc_sha256':sha(data)})
  bc=struct.pack('<4s4I',b'OATX',0x83f1 if fmt==1 else 0x83f3,c['width'],c['height'],len(chunks))+b''.join(struct.pack('<I',len(v))+v for v in chunks)
  name=f'asset-{tid}.oatx';(B/name).write_bytes(bc)
  start=next((i for i,l in enumerate(c['levels']) if max(l['width'],l['height'])<=512),None);assert start is not None,tid
  rgba=[];receipts=[]
  for i,l in enumerate(c['levels'][start:],start):
   data=chunks[i];w,h=l['width'],l['height'];header=[124,0x81007,h,w,len(data),0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1' if fmt==1 else b'DXT5','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
   pixels=Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*header)+data)).convert('RGBA').tobytes()
   points={(0,0),(w-1,h-1),(w//2,h//2)}|{((j*173+tid+i*7)%w,(j*359+tid//7+i*13)%h) for j in range(32)}
   for x,y in points:assert tuple(pixels[(y*w+x)*4:(y*w+x)*4+4])==ref_sample(data,w,x,y,fmt),(tid,i,x,y)
   rgba.append(pixels);receipts.append(dict(source_level=i,width=w,height=h,rgba_sha256=sha(pixels),samples=len(points)))
  w,h=c['levels'][start]['width'],c['levels'][start]['height'];portable=struct.pack('<4s4I',b'OATX',0x8058,w,h,len(rgba))+b''.join(struct.pack('<I',len(v))+v for v in rgba);(R/name).write_bytes(portable)
  for blob,parts in [(bc,chunks),(portable,rgba)]:
   at=20
   for v in parts:
    n=struct.unpack_from('<I',blob,at)[0];at+=4;assert blob[at:at+n]==v;at+=n
   assert at==len(blob)
  out.append(dict(asset=tid,name=s['name'],source=c['path'],source_sha256=c['sha256'],source_width=c['width'],source_height=c['height'],source_mips=c['mips'],native_bc_file='textures-native-bc/'+name,native_bc_sha256=sha(bc),native_bc_bytes=len(bc),native_bc_levels=levels,portable_file='textures-portable-512/'+name,portable_sha256=sha(portable),portable_bytes=len(portable),portable_source_first_mip=start,portable_width=w,portable_height=h,portable_levels=receipts))
 cubes=[];unsupported=[]
 for s in cat['textures']:
  if s['selected_name']:continue
  cs=[c for c in s['carriers'] if not c.get('error')]
  if not cs:unsupported.append(s);continue
  c=max(cs,key=lambda c:(c['width']*c['height'],c['mips']));raw=(P/c['path']).read_bytes();n=c['expected_2d_bytes']-38
  if c['format'] in [1,5] and len(raw)==38+6*n:
   name=f"asset-{s['asset']}.keen";(Z/name).write_bytes(raw);cubes.append(dict(asset=s['asset'],name=s['name'],file='textures-cube-native/'+name,source=c['path'],source_sha256=sha(raw),width=c['width'],height=c['height'],mips=c['mips'],faces=6,bytes=len(raw),payload_bytes=len(raw)-38,face_chain_bytes=n,face_order='retained source byte order; face-vs-mip ordering not interpreted by thisstage'))
  else:unsupported.append(dict(asset=s['asset'],name=s['name'],reason='sourcefmt2blank retainedraw; no guessed decode/fallback describedasreal',carrier=c))
 report=dict(status='STAGED ONLY; no oldworldtextureIDs assigned',textures=out,cubemaps=cubes,unsupported=unsupported,native_bc_bytes=sum(x['native_bc_bytes'] for x in out),portable_rgba_bytes=sum(x['portable_bytes'] for x in out),selection=cat['selection'],portable_policy='Explicitpreview max512authored mip-tail; allstored levels afterchosenmip decodedUNORM byte-exact, noresize/generatedmips; notoriginalopeningresidency claim',native_bc_policy='Fullhighestdeclared completeauthored2D chains, sourceBC1_RGBA/BC3_UNORM payloadbytes preserved; AndroidGLESsupport NOTassumed',decoder_evidence=dict(helper=str(H.relative_to(P)),sha256=sha(H.read_bytes()),sample_decoder='Reviewedscalar rgb565/ref_sample; Pillowoutput checked each mip acrossdeterministicpoints'),validation='Full BC payload identity, scalar-vs-Pillow RGBA sample identity each portable mip, exact OATX reparse payload identity alllevels')
 (O/'texture-stage-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('STAGED',len(out),'BCMiB',report['native_bc_bytes']/1048576,'PORTABLEMiB',report['portable_rgba_bytes']/1048576,'CUBES',len(cubes),'UNSUPPORTED',len(unsupported))
if __name__=='__main__':main()
