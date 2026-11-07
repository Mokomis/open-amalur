from pathlib import Path
import json,struct,zlib,hashlib
O=Path(__file__).resolve().parent
r=json.loads((O/'exact-key-join.json').read_text())
H=lambda b:hashlib.sha256(b).hexdigest()
for row in r['all_shipped_assetinfo_versions']:
 b=(O/row['path']).read_bytes();assert H(b)==row['sha256']
 n,m=struct.unpack_from('<II',b);at=8;hits=[]
 for i in range(n+m):
  start=at;k,t,ln=struct.unpack_from('<IBB',b,at);at+=6
  name=b[at:at+ln].decode('utf-8');at+=ln
  if k==330590315:hits.append((i,start,t,name))
 assert at==len(b) and len(hits)==1
 assert hits[0][3]=='main_table.conditional_expression'and hits[0][2]==28
archive=r['archive'];p=Path(archive['path']);assert p.stat().st_size==archive['bytes']
with p.open('rb')as f:
 h=f.read(32);sig,valid,align,ca,di,_,_=struct.unpack('<4sIIIQII',h)
 assert sig==b'KARl'and valid==1 and align==16
 f.seek(di);n,s=struct.unpack('<II',f.read(8));directory=f.read(n*12)
 matches=[(i,x)for i,x in enumerate(struct.iter_unpack('<III',directory))if x[0]==zlib.crc32(b'main_table.conditional_expression')]
 assert len(matches)==1
 i,(crc,pos,sz)=matches[0];assert i==archive['directory_index']and struct.pack('<III',crc,pos,sz).hex()==archive['entry_raw_hex']
 f.seek(pos*align);head=f.read(8);outsize,chunks=struct.unpack('<II',head);lens=f.read(chunks*4)
 sizes=struct.unpack('<'+'I'*chunks,lens);block=head+lens+f.read(sum(sizes))
 assert H(block)==archive['compressed_block_sha256']and block==(O/'main-table-original-compressed-block.bin').read_bytes()
b=(O/'official-single-extract/main_table.conditional_expression').read_bytes()
assert len(b)==sz and H(b)==r['official_decode']['sha256']
assert b==(O.parent/'source/initial_0.pak/main_table.conditional_expression').read_bytes()
version,count=struct.unpack_from('<II',b);assert version==6;at=8;record2=None
for i in range(count):
 ln=struct.unpack_from('<I',b,at)[0];at+=4+ln
 ln=struct.unpack_from('<H',b,at)[0];at+=2;payload=b[at:at+ln]
 if i==2:record2=(at,payload)
 at+=ln
assert at==len(b)and record2==(1580,b'\0')
print('PASS exact sourcekey330590315 ->cataloguefilename ->PAKCRC/index/block ->officialdecodeSHA ->condition2 TRUE;bothassetinfo versions exactEOF')
