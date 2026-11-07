from pathlib import Path
import json,struct,hashlib
R=Path(__file__).resolve().parent;A={x['draw']['index']:x for x in json.loads((R/'active-water-bindings.json').read_text())};meshes=json.loads((R/'water-mesh-manifest.json').read_text())['draws'];images=json.loads((R/'image-provenance.json').read_text());byimg={x['image']:x for x in images if x['aspect']==1};mats={x['id']:x for x in json.loads((R/'decoded-materials.json').read_text())};want={m['reflection_image'] for m in meshes}|{A[m['draw']]['descriptors'][str(k)]['view']['image'] for m in meshes for k in range(35,40)}
def decode(raw,w,h,bc3):
 out=bytearray(w*h*4);bs=16 if bc3 else 8
 for by in range(0,h,4):
  for bx in range(0,w,4):
   off=((by//4)*((w+3)//4)+bx//4)*bs;block=raw[off:off+bs];c0,c1,sel=struct.unpack_from('<HHI',block,8 if bc3 else 0)
   col=lambda c:((c>>11)*255//31,((c>>5)&63)*255//63,(c&31)*255//31,255)
   a,b=col(c0),col(c1);cs=[a,b,tuple((2*a[j]+b[j])//3 for j in range(3))+(255,),tuple((a[j]+2*b[j])//3 for j in range(3))+(255,)] if c0>c1 or bc3 else [a,b,tuple((a[j]+b[j])//2 for j in range(3))+(255,),(0,0,0,0)]
   if bc3:
    a0,a1=block[:2];alphas=[a0,a1]+([( (7-i)*a0+i*a1)//7 for i in range(1,7)] if a0>a1 else [((5-i)*a0+i*a1)//5 for i in range(1,5)]+[0,255]);asel=int.from_bytes(block[2:8],'little')
   for y in range(4):
    for x in range(4):
     if by+y>=h or bx+x>=w:continue
     c=list(cs[(sel>>(2*(y*4+x)))&3]);
     if bc3:c[3]=alphas[(asel>>(3*(y*4+x)))&7]
     o=((by+y)*w+bx+x)*4;out[o:o+4]=bytes(c)
 return bytes(out)
tex=[]
for id in sorted(want):
 info=byimg[id];ci=info['create_info'];w=ci['extent']['width'];h=ci['extent']['height'];faces=ci['arrayLayers'];raw=(R/'resources'/f'image-{id}-aspect1.bin').read_bytes();fmt=ci['format'];assert fmt in ['VK_FORMAT_BC1_RGBA_UNORM_BLOCK','VK_FORMAT_BC3_UNORM_BLOCK'];fb=((w+3)//4)*((h+3)//4)*(16 if 'BC3' in fmt else 8);rgba=b''.join(decode(raw[f*fb:(f+1)*fb],w,h,'BC3' in fmt) for f in range(faces));tex.append((id,faces,w,h,rgba))
pack=bytearray(struct.pack('<4s3I',b'OAWP',1,len(tex),len(meshes)))
for id,faces,w,h,rgba in tex:pack+=struct.pack('<5I',id,faces,w,h,len(rgba))+rgba
for mesh in meshes:
 d=A[mesh['draw']];m=mats[mesh['material']];b=(R/'meshes'/mesh['file']).read_bytes();lights=next((u['float_values'] for u in d['draw']['uniforms'] if u['binding']==5),[0.0]*32)[:32];ids=[d['descriptors'][str(k)]['view']['image'] for k in range(35,40)]
 pack+=struct.pack('<6I',mesh['draw'],mesh['material'],mesh['reflection_image'],mesh['vertices'],mesh['indices'],int(d['draw']['pipeline']==13183));pack+=struct.pack('<24f',*m['native_float24']);pack+=struct.pack('<32f',*lights);pack+=struct.pack('<4f',*mesh['global_tint'])+struct.pack('<4f',*mesh['luminance_factors'])+struct.pack('<3f',*mesh['luminance_tint'])+struct.pack('<5I',*ids)+b[32:]
(R/'water-native.bin').write_bytes(pack);(R/'water-pack.json').write_text(json.dumps(dict(file='water-native.bin',bytes=len(pack),sha256=hashlib.sha256(pack).hexdigest(),textures=[dict(id=id,faces=f,w=w,h=h,bytes=len(rgba)) for id,f,w,h,rgba in tex],draws=len(meshes),mips='native top-mip decoded; renderer generates filtered mipchain, source full compressed mipchain retained separately'),indent=2));print(len(pack),len(tex),len(meshes))
