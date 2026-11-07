from pathlib import Path
import sys,json,struct
sys.argv=sys.argv[:1]
exec((Path(__file__).parent/'data_refs.py').read_text().split('import sys\nresult=[]')[0])
rows=[]
for needle in [b'parent\0',b'function parent',b'__parent\0']:
 start=0
 while True:
  p=b.find(needle,start)
  if p<0:break
  a=va(p);start=p+1
  rows.append({'needle':needle.decode('ascii'),'address':hex(a),'bytes':b[max(0,p-80):p+150].hex(),'refs':[hex(x) for x in refs(a)] if a else []})
print(json.dumps(rows,indent=2));(root/'outputs/scene-v08/parent-string-refs.json').write_text(json.dumps(rows,indent=2))
