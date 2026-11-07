"""Bounded authored slot-zero preview; no original shader equivalence claim."""
import json,struct,hashlib,subprocess,sys
from pathlib import Path
from keen_texture import decode
root=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(root/'work/v07-bxml'))
from amalur_blob import parse_bytes
sha=lambda b:hashlib.sha256(b).hexdigest()
profile=json.loads((root/'work/v09-textures/floor-preview-profile.json').read_text());profile['materials']=[]
profile['scope']='Approximate opaque slot-zero visualization on selected stride48 meshes. Material association, UV convention and base-color slot semantics remain partly inferred; original shaders not reconstructed.'
candidates=[];names=set()
for p in sorted((root/'work/scene-inputs-v09/initial_0.pak').glob('*.mat_bxml')):
 b=p.read_bytes();blob=parse_bytes(b)
 if {r['slot_payload_offset'] for r in blob['slots']}!={0,8}:continue
 pp,pc,tp,tc,shader=struct.unpack_from('<5I',b,8)
 if pp!=40 or tp!=pp+pc*24 or tp+tc*8!=8+blob['header']['payload_bytes']:continue
 pairs=[struct.unpack_from('<II',b,tp+8*i) for i in range(tc)];zero=[a for a,s in pairs if s==0]
 if len(zero)!=1 or zero[0]<=1:continue
 tid=zero[0];candidates.append((p,b,shader,tid))
 names.update([f'{tid}_2.dds',f'{tid}_0.dds',f'{tid}.dds'])
subprocess.run([sys.executable,str(root/'work/v09-scene/extract_scene_inputs.py'),*sorted(names)],check=True,stdout=subprocess.DEVNULL)
rejected=[]
for p,b,shader,tid in candidates:
 reason='no admitted texture'
 for archive in ('DATA_0.pak','initial_0.pak'):
  for name in (f'{tid}_2.dds',f'{tid}_0.dds',f'{tid}.dds'):
   f=root/'work/scene-inputs-v09'/archive/name
   if not f.exists():continue
   raw=f.read_bytes()
   try:
    rgba,r=decode(raw,0)
    if r['asset_id']!=tid or r['alpha_min']!=255:raise ValueError('nonopaque or ID mismatch')
    if max(r['decoded_width'],r['decoded_height'])>512:raise ValueError('dimension cap')
   except ValueError as e:reason=str(e);continue
   profile['materials'].append(dict(material_id=int(p.stem),material_file=str(p),material_sha256=sha(b),shader_id=shader,texture_slot=0,texture_id=tid,texture_file=str(f),texture_sha256=sha(raw),decode_level=0,evidence=['Authored approximate slot0 opaque preview; original shader semantics unverified.','Native material dependency reader proves texture IDs; exact material array/texture/geometry identities checked by assembler.','Explicit DATA then initial archive candidate preference; native mount precedence unverified.']))
   break
  else:continue
  break
 else:rejected.append(dict(material=p.stem,reason=reason))
(root/'work/v09-textures/opaque-preview-profile.json').write_text(json.dumps(profile,indent=2))
(root/'outputs/scene-v09/preview-selection.json').write_text(json.dumps(dict(selected=len(profile['materials']),rejected=rejected),indent=2))
print(json.dumps(dict(selected=len(profile['materials']),rejected=rejected),indent=2))
