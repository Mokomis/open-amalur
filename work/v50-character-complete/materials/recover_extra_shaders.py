"""Read only the newly identified compressed DXBC prefix variants; retain only
the exact sword material-layout candidates. Never runs the old cache writer."""
from pathlib import Path
import struct,re,json,ctypes,hashlib,collections
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v50-character-complete/materials'
old=(ROOT/'work/v19-lighting/shx2.py').read_text()
exec(old[old.index('def aplib('):old.index("\nOUT=")])
exec(old[old.index('dll=ctypes.'):old.index('\nidx={};')])
c=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe').read_bytes()
known=json.loads((ROOT/'outputs/scene-v19/shader-index.json').read_text())
candidates=[];bad=[];seen={};parsed=0
for m in re.finditer(rb'D[\x01-\x1f]XBC',c):
 i=m.start();accepted=False
 for N in range(1,40):
  h=i-8-4*N
  if h<0:continue
  us,n=struct.unpack_from('<II',c,h)
  if n!=N or not 32<us<8000000:continue
  sizes=struct.unpack_from('<%dI'%N,c,h+8)
  try:
   parts=[];p=i
   for z in sizes:
    decoded,used=aplib(c,p,0x40000)
    if used>z:raise ValueError('compressed block overrun')
    parts.append(decoded);p+=z
   blob=b''.join(parts)
  except Exception:continue
  if len(blob)!=us or blob[:4]!=b'DXBC':continue
  accepted=True;parsed+=1;sha=hashlib.sha1(blob).hexdigest()[:16]
  if sha in known or sha in seen:break
  seen[sha]=True
  fields=[b'ConstantColor',b'SpecularValues',b'CharacterExtraTerms2',b'FresnelValues2']
  if (b'CharacterAmbientMap' in blob and b'EnvironmentMap' in blob) or (b'g_materialbuffer' not in blob and b'Fog' in blob and b'AlphaMap' in blob):
   text=dis(blob)
   if text and re.search(r'(?m)^ps_',text):
    dst=OUT/'extra-native-shaders';dst.mkdir(exist_ok=True)
    (dst/(sha+'.dxbc')).write_bytes(blob);(dst/(sha+'.asm')).write_text(text,encoding='latin1')
    row={'hash':sha,'file_offset':i,'header':h,'uncompressed':us,'blocks':N,'sizes':list(sizes),'prefix_tag':c[i+1],'lines':text.count('\n'),'textures':re.findall(r'^// (\S+)\s+texture',text,re.M)}
    candidates.append(row);print('candidate',sha,row['lines'],row['textures'],flush=True)
  break
 if not accepted:bad.append(i)
receipt={'scope':'New compressed prefix entries only; no existing cache edits. Retained only no-instance-buffer PS with the exact four sword material fields.','parsed_entries':parsed,'unique_new_blobs':len(seen),'unparsed_offsets':bad,'candidates':candidates}
(OUT/'extra-shader-recovery.json').write_text(json.dumps(receipt,indent=2))
print('done',parsed,'unique',len(seen),'candidates',len(candidates),'bad',len(bad))
