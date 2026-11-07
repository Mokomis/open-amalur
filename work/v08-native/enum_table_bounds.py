from pathlib import Path
import sys,json,struct
sys.argv=sys.argv[:1]
exec((Path(__file__).parent/'data_refs.py').read_text().split('import sys\nresult=[]')[0])
def s(addr):
 out=bytearray()
 for i in range(256):
  c=raw(addr+i,1)
  if c==b'\0':return out.decode('ascii')
  if not 32<=c[0]<127:raise ValueError('nonascii')
  out+=c
 raise ValueError('long')
def desc(addr):
 name,count,ptr=struct.unpack('<III',raw(addr,12));assert 0<count<=1000
 return {'address':hex(addr),'name':s(name),'members':[{'name':s(a),'value':v} for a,v in [struct.unpack('<Ii',raw(ptr+i*8,8)) for i in range(count)]]}
lo=hi=0x1771090
while True:
 try:desc(lo-12);lo-=12
 except (ValueError,AssertionError):break
while True:
 try:desc(hi+12);hi+=12
 except (ValueError,AssertionError):break
rows=[desc(a) for a in range(lo,hi+1,12)];j={'start':hex(lo),'end':hex(hi+12),'groups':len(rows),'entries':sum(len(r['members']) for r in rows),'descriptors':rows,'start_refs':[hex(a) for a in refs(lo)],'end_refs':[hex(a) for a in refs(hi+12)]}
(root/'outputs/scene-v08/enum-static-descriptors.json').write_text(json.dumps(j,indent=2));print(json.dumps({k:v for k,v in j.items() if k!='descriptors'}))
