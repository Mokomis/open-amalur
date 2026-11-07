from pathlib import Path
import json,struct,ctypes,hashlib
R=Path(__file__).resolve().parent;E=R/'evidence';out=R/'resources';out.mkdir(exist_ok=True)
A=json.loads((R/'active-water-bindings.json').read_text());want={v['view']['image']:v['image'] for d in A for v in d['descriptors'].values() if v.get('view')};fn=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
meta=[]
with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb') as f:
 _,_,_,n=struct.unpack('<4sIII',f.read(16));f.seek(n*8,1);i=-1
 while h:=f.read(12):
  size,kind=struct.unpack('<QI',h);i+=1;off=f.tell();d=f.read(min(size,48))
  if kind&0x7fffffff==3 and len(d)>=48 and struct.unpack_from('<I',d)[0]&0xffff==8 and struct.unpack_from('<Q',d,20)[0] in want:
   cmd,thread,device,img,bytes_,aspect,layout,levels=struct.unpack('<IQQQQIII',d);d+=f.read(size-len(d));sizes=struct.unpack_from('<%dQ'%levels,d,48);head=48+8*levels;raw=d[head:]
   if kind&0x80000000:
    b=ctypes.create_string_buffer(bytes_);assert fn(raw,b,len(raw),bytes_)==bytes_;raw=b.raw
   assert len(raw)==bytes_;(out/f'image-{img}-aspect{aspect}.bin').write_bytes(raw);info=dict(image=img,block=i,file_offset=off,stored_bytes=size,compressed=bool(kind&0x80000000),bytes=bytes_,level_sizes=sizes,aspect=aspect,layout=layout,create_info=want[img],sha256=hashlib.sha256(raw).hexdigest());meta.append(info)
   if want[img]['format']=='VK_FORMAT_BC1_RGBA_UNORM_BLOCK' and want[img]['arrayLayers']==6:
    w=want[img]['extent']['width'];facebytes=((w+3)//4)**2*8;assert sizes[0]>=facebytes*6
    rgba=[]
    def decode(b):
     pixels=bytearray(w*w*4)
     for by in range(0,w,4):
      for bx in range(0,w,4):
       c0,c1,sel=struct.unpack_from('<HHI',b,((by//4)*(w//4)+bx//4)*8)
       col=lambda c:((c>>11)*255//31,((c>>5)&63)*255//63,(c&31)*255//31,255)
       a,b_=col(c0),col(c1)
       cs=[a,b_,tuple((2*a[j]+b_[j])//3 for j in range(3))+(255,),tuple((a[j]+2*b_[j])//3 for j in range(3))+(255,)] if c0>c1 else [a,b_,tuple((a[j]+b_[j])//2 for j in range(3))+(255,),(0,0,0,0)]
       for y in range(4):
        for x in range(4):pixels[((by+y)*w+bx+x)*4:((by+y)*w+bx+x)*4+4]=bytes(cs[(sel>>(2*(y*4+x)))&3])
     return bytes(pixels)
    for face in range(6):rgba.append(decode(raw[face*facebytes:(face+1)*facebytes]))
    (out/f'cube-{img}-{w}-rgba.bin').write_bytes(b''.join(rgba));info['rgba_file']=f'cube-{img}-{w}-rgba.bin';info['rgba_sha256']=hashlib.sha256(b''.join(rgba)).hexdigest()
    import zlib,binascii
    def chunk(k,d):return struct.pack('>I',len(d))+k+d+struct.pack('>I',binascii.crc32(k+d)&0xffffffff)
    rows=[]
    for y in range(w*2):
     rows.append(b'\0'+b''.join(rgba[(y//w)*3+x][(y%w)*w*4:(y%w+1)*w*4] for x in range(3)))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w*3,w*2,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')
    (out/f'cube-{img}-faces.png').write_bytes(png)
  else:f.seek(size-len(d),1)
(R/'image-provenance.json').write_text(json.dumps(meta,indent=2));print([(x['image'],x['bytes'],x.get('rgba_file')) for x in meta])
