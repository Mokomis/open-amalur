from pathlib import Path
import ctypes,struct,json,hashlib
p=Path(__file__).parent;cap=Path('/private/tmp/oa-dalentarth-20261105.gfxr');want={4443:'lut4443',1833:'lut1833'};found={}
fn=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
with cap.open('rb') as f:
 _,_,_,opts=struct.unpack('<4sIII',f.read(16));f.seek(opts*8,1);idx=-1
 while True:
  h=f.read(12)
  if not h:break
  size,kind=struct.unpack('<QI',h);idx+=1;at=f.tell();head=f.read(min(size,48))
  if kind&0x7fffffff==3 and len(head)>=48 and struct.unpack_from('<I',head)[0]&0xffff==8:
   meta,thread,device,image,n,aspect,layout,count=struct.unpack('<IQQQQIII',head)
   if image in want:
    levels=struct.unpack('<%dQ'%count,f.read(count*8));remain=f.read(size-48-count*8)
    if kind&0x80000000:
     buf=ctypes.create_string_buffer(n);assert fn(remain,buf,len(remain),n)==n;raw=buf.raw
    else:raw=remain
    assert len(raw)==n==sum(levels)
    name=want[image];(p/f'{name}-allmips.bin').write_bytes(raw);(p/f'{name}-mip0.bin').write_bytes(raw[:levels[0]])
    found[image]=dict(name=name,block=idx,file_offset=at,stored_size=size,compressed=bool(kind&0x80000000),meta=meta,thread=thread,device=device,image=image,aspect=aspect,layout=layout,data_size=n,level_sizes=levels,sha256=hashlib.sha256(raw).hexdigest(),mip0_sha256=hashlib.sha256(raw[:levels[0]]).hexdigest())
  f.seek(at+size)
(p/'lut-image-extraction.json').write_text(json.dumps(found,indent=2));assert set(found)==set(want);print(json.dumps(found,indent=2))
