from pathlib import Path
import re,json
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v30-engine');out=[]
for p in (r/'decomp').glob('*.c'):
 t=p.read_text(errors='replace')
 for m in re.finditer(r'FID_conflict__memcpy\s*\([^;]{0,400},\s*0x90\)',t):
  head=t.rfind('// ',0,m.start());header=t[head:t.find('\n',head)];out.append({'file':p.name,'function':header,'call':m.group()})
print(json.dumps(out,indent=2));(r.parent/'v33-native-camera/native-camera-copy-candidates.json').write_text(json.dumps(out,indent=2)+'\n')
