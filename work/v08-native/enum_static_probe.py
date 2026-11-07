from pathlib import Path
import sys,json,struct
sys.argv=sys.argv[:1]
exec((Path(__file__).parent/'data_refs.py').read_text().split('import sys\nresult=[]')[0])
def s(addr):
 out=bytearray()
 for i in range(256):
  c=raw(addr+i,1)
  if c==b'\0':return out.decode('ascii')
  out+=c
 raise ValueError('stringtoo long')
rows=[]
for addr in [0x1771090,0x177109c]:
 name,count,ptr=struct.unpack('<III',raw(addr,12));members=[]
 for i in range(count):
  a,v=struct.unpack('<Ii',raw(ptr+i*8,8));members.append({'name_address':hex(a),'name':s(a),'value':v})
 rows.append({'address':hex(addr),'name':s(name),'count':count,'members':members})
print(json.dumps(rows,indent=2));(root/'outputs/scene-v08/enum-static-table.json').write_text(json.dumps(rows,indent=2))
