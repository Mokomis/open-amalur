from pathlib import Path
import json,struct,hashlib
r=Path(r'C:\Users\rwill\Documents\Opem Amalur');w=r/'work/v37-native-character';inputs=r/'work/v20-inputs';target=(w/'capture-2026-11-05T21-16-24-734Z/index.bin').read_bytes();budget=256*1024*1024;used=0;files=0;matches=[];clips=[];skipped=[]
for p in sorted(inputs.rglob('*')):
 if not p.is_file():continue
 if p.suffix=='.anm_bxml' and len(clips)<16:
  d=p.read_bytes();a=8
  if len(d)>a+0x50 and d[a:a+4]==b'50AE':clips.append({'path':str(p),'bytes':len(d),'fps':struct.unpack_from('<f',d,a+8)[0],'joints':struct.unpack_from('<H',d,a+0xe)[0],'frames':struct.unpack_from('<H',d,a+0x10)[0],'sets':struct.unpack_from('<H',d,a+0x12)[0],'compression_flags':d[a+0x26],'sha256':hashlib.sha256(d).hexdigest()})
 if p.suffix!='.fab_bxml':continue
 size=p.stat().st_size
 if size>32*1024*1024 or used+size>budget:skipped.append(str(p));continue
 d=p.read_bytes();used+=len(d);files+=1
 if target in d:matches.append({'path':str(p),'index_stream_offset':d.index(target),'match_bytes':len(target),'sha256':hashlib.sha256(d).hexdigest()})
out={'mesh_scan_scope':'existingv20-inputs .fab_bxml only; complete10752byteindexstream equality;256MiB readbudget; no files changed','scanned_files':files,'scanned_bytes':used,'skipped_count':len(skipped),'mesh_candidates':matches,'first16_existing_compressed_clips':clips};(w/'native-asset-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
