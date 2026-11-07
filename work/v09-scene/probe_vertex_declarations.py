from pathlib import Path
import json,struct,platform
assert platform.system()=='Windows'
s=Path('work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')])
rows=[]
for token in [b'TEXCOORD\x00',b'POSITION\x00',b'd3d9.dll',b'D3D11CreateDevice']:
 at=b.find(token);items=[]
 while at>=0:
  addr=va(at)
  if addr:items.append({'address':hex(addr),'refs':[hex(x) for x in list(refs(addr))[:40]]})
  at=b.find(token,at+1)
 rows.append({'token':repr(token),'items':items})
# D3D9 FLOAT2 TEXCOORD0 at byte12. Candidate only, requires native caller.
pat=bytes.fromhex('00000c0001000500');at=b.find(pat);matches=[]
while at>=0:
 addr=va(at)
 if addr:matches.append({'address':hex(addr),'around':raw(addr-16,64).hex(),'refs_to_prior_position':[hex(x) for x in list(refs(addr-8))[:20]]})
 at=b.find(pat,at+1)
j={'target_sha256':hashlib.sha256(b).hexdigest(),'strings':rows,'d3d9_uv12_candidates':matches};Path('outputs/scene-v09/vertex-declaration-probe.json').write_text(json.dumps(j,indent=2));print(json.dumps(j,indent=2))
