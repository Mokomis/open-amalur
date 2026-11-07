from pathlib import Path
import struct,json,hashlib,collections
r=Path(__file__).resolve().parents[2];out=Path(__file__).resolve().parent/'material-audit';out.mkdir(exist_ok=True)
sy=json.loads((r/'work/v20-inputs/symbols.json').read_text());meta=json.loads((r/'work/v22-stress/zone-dal/zone_materials.json').read_text());native={};invalid=[]
for arch in ['patch_0.pak','initial_0.pak','DATA_0.pak']:
 for p in (r/'work/v20-inputs'/arch).glob('*.mat_bxml'):
  mid=int(p.name.split('.')[0])
  if mid in native:continue
  b=p.read_bytes()
  try:
   payload=struct.unpack_from('<I',b)[0];pp,pc,tp,tc,sh=struct.unpack_from('<5I',b,8)
   assert pc<256 and tc<64 and pp+pc*24<=8+payload and tp+tc*8<=8+payload
   params=[{'value':list(struct.unpack_from('<4f',b,pp+i*24)),'type':struct.unpack_from('<I',b,pp+i*24+16)[0],'key':struct.unpack_from('<I',b,pp+i*24+20)[0]} for i in range(pc)]
   tex=[struct.unpack_from('<2I',b,tp+i*8) for i in range(tc)]
   # Reproduce the existing importer's selected-map identity, without assuming shader semantics.
   refs=[]
   for i in range(0,len(b)-3,4):
    v=struct.unpack_from('<I',b,i)[0];nm=sy['texture'].get(str(v))
    if nm and v not in [x[0] for x in refs]:refs.append((v,str(nm).lower()))
   pick=lambda tail:next((x for x,n in refs if n.endswith(tail) and 'par_color' not in n),None)
   d=pick('_d') or next((x for x,n in refs if not n.endswith(('_n','_s','_g','_cubemap','_a','_e'))),None)
   sig=(d,pick('_a'),pick('_n'),pick('_s'))
   native[mid]={'id':mid,'name':sy['material'].get(str(mid)),'shader_id':sh,'shader':sy['shader'].get(str(sh)),'signature':sig,'params':params,'textures':tex,'path':str(p.relative_to(r)),'sha256':hashlib.sha256(b).hexdigest()}
  except (AssertionError,struct.error):invalid.append(str(p.relative_to(r)))
lookup=collections.defaultdict(list)
for v in native.values():lookup[tuple(v['signature'])].append(v)
rows=[]
for i,m in enumerate(meta['materials']):
 if m.get('kind') or m.get('terrain') or not isinstance(m.get('d'),int):continue
 sig=tuple(m.get(k) for k in ['d','a','n','s']);cand=lookup.get(sig,[])
 rows.append({'index':i,'signature':sig,'candidates':cand})
summary={'native_materials':len(native),'invalid':invalid,'legacy_rows':len(rows),'matched':sum(bool(x['candidates']) for x in rows),'unique':sum(len(x['candidates'])==1 for x in rows),'shader_counts':dict(collections.Counter(v['shader'] for x in rows for v in x['candidates']))}
(out/'material-candidates.json').write_text(json.dumps({'summary':summary,'rows':rows},indent=2));print(json.dumps(summary,indent=2))
