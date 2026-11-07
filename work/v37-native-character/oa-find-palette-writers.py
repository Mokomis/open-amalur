from pathlib import Path
import re,json
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\decomp');results=[]
for p in r.glob('unnamed_00c*.c'):
 for b in re.split(r'\n(?=// [0-9a-f]{8} )',p.read_text(errors='replace')):
  a=re.findall(r'\+\s*0x(?:30|34|38)\)\s*=[^;]*;',b)
  offsets={re.search(r'0x(30|34|38)',x).group(1) for x in a}
  if '30' in offsets and '34' in offsets:
   results.append({'function':b.splitlines()[0],'file':p.name,'assignments':a[:8]})
out=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v37-native-character\palette-writer-candidates.json');out.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'count':len(results),'candidates':results},indent=2))
