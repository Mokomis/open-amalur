"""Extract only the three active ambient InitImage payloads, no replay/GPU."""
from pathlib import Path
import struct,json,hashlib
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v49-character-create/character-gloss-audit'
CAP=ROOT/'work/v31-native-slice/captures/amalur_trim_trigger_20261105T113036.gfxr'
def lz4(raw,expected):
 out=bytearray();i=0
 def length(base):
  nonlocal i
  n=base
  if base==15:
   while True:
    assert i<len(raw);x=raw[i];i+=1;n+=x
    if x!=255:break
  return n
 while i<len(raw):
  token=raw[i];i+=1;n=length(token>>4)
  assert i+n<=len(raw) and len(out)+n<=expected;out+=raw[i:i+n];i+=n
  if i==len(raw):break
  assert i+2<=len(raw);off=raw[i]|raw[i+1]<<8;i+=2;assert 0<off<=len(out)
  n=length(token&15)+4;assert len(out)+n<=expected
  for _ in range(n):out.append(out[-off])
 assert len(out)==expected
 return bytes(out)

want={13839:1880460,13844:1880461,13875:1880462};found={}
manifest=json.loads((ROOT/'work/v48-opening/initial-sword-visuals/texture-stage-manifest.json').read_text())
src={x['asset']:x for x in manifest['textures'] if x['asset'] in want.values()}
with CAP.open('rb') as f:
 sig,version,compression,opts=struct.unpack('<4sIII',f.read(16));f.seek(opts*8,1);index=-1
 while True:
  h=f.read(12)
  if not h:break
  assert len(h)==12;size,kind=struct.unpack('<QI',h);index+=1;start=f.tell();head=f.read(min(size,48))
  if kind&0x7fffffff==3 and len(head)>=48 and struct.unpack_from('<I',head)[0]&0xffff==8:
   meta,thread,device,image,n,aspect,layout,count=struct.unpack('<IQQQQIII',head)
   if image in want:
    sizes=struct.unpack('<%dQ'%count,f.read(count*8));packed=f.read(size-48-count*8)
    raw=lz4(packed,n) if kind&0x80000000 else packed;assert len(raw)==n==sum(sizes)
    item=src[want[image]];source=(ROOT/item['source']).read_bytes();assert hashlib.sha256(source).hexdigest()==item['source_sha256']
    assert count==len(item['native_bc_levels']);at=0;levels=[]
    for allocated,sl in zip(sizes,item['native_bc_levels']):
     tex=source[sl['source_offset']:sl['source_offset']+sl['bytes']];cap=raw[at:at+sl['bytes']]
     assert cap==tex
     levels.append({'source_level':sl['level'],'capture_allocated_bytes':allocated,'tight_bytes':len(tex),'source_file_offset':sl['source_offset'],'all_tight_BC_bytes_equal':True,'sha256':hashlib.sha256(tex).hexdigest()});at+=allocated
    (OUT/f'image-{image}-init.bin').write_bytes(raw)
    found[image]={'image':image,'source_asset':want[image],'source':item['source'],'source_sha256':item['source_sha256'],'capture_file_offset':start,'block_index':index,'data_size':n,'stored_size':size,'sha256':hashlib.sha256(raw).hexdigest(),'levels':levels,'all7authored_mips_exact':True}
  f.seek(start+size)
assert set(found)==set(want)
(OUT/'sword-texture-byte-join.json').write_text(json.dumps({'capture':str(CAP),'images':found,'scope':'Only3actuallyboundRustySwordmaps,all7mips; no image decoding/conversion, compares original authored BC blocks.'},indent=2)+'\n')
print(json.dumps({k:{'source_asset':v['source_asset'],'bytes':v['data_size'],'levels':len(v['levels']),'all_equal':v['all7authored_mips_exact']} for k,v in found.items()}))
