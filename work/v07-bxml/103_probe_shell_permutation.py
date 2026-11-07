"""Test center-vector/permutation hypotheses; no scene or mesh is changed."""
from pathlib import Path
import hashlib,json,math,platform,struct
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur';data=(root/'work/scene-inputs-v07/DATA_0.pak/524859.space_bxml').read_bytes()
assert hashlib.sha256(data).hexdigest()=='775fb38b3fd9ff67ed3181579e935c70b33bd6831ccebf744ce4b2f6cd590143'
def array(slot,stride):
    target,count=struct.unpack_from('<II',data,8+slot)
    assert count<100000 and target>=8 and target+count*stride<=8+struct.unpack_from('<I',data)[0]
    return [data[target+i*stride:target+(i+1)*stride] for i in range(count)]
def vec(b,o=0):return struct.unpack_from('<3f',b,o)
def dist(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def closest(center,records,offset):
    return sorted(({'index':i,'distance':dist(center,vec(r,offset))} for i,r in enumerate(records)),key=lambda r:r['distance'])[:2]
out={'source_sha256':hashlib.sha256(data).hexdigest(),'scope':'Permutation and geometric-center hypotheses only; no rendering','groups':[]}
for refslot,centerslot,renderslot,cullslot in [(0x1b0,0x1a8,0x160,0x158),(0x1e0,0x1d8,0x180,0x178)]:
    refs=[struct.unpack('<I',r)[0] for r in array(refslot,4)];centers=array(centerslot,12)
    render=array(renderslot,84);cull=array(cullslot,80);rows=[]
    assert len(refs)==len(centers)
    for i,(typed,centerbytes) in enumerate(zip(refs,centers)):
        center=vec(centerbytes);sphere=closest(center,render,0);pose=closest(center,render,16)
        row={'reference_index':i,'typed_id':typed,'fab_id_candidate':typed&0xfffffff,'reference_center':center,
             'nearest_render_spheres':sphere,'nearest_render_positions':pose}
        for label,match in [('sphere',sphere[0]),('pose',pose[0])]:
            if match['distance']<.01:
                r=render[match['index']];c=cull[match['index']]
                row[label+'_match_record']={'render_index':match['index'],'raw_hex':r.hex(),'sphere':list(struct.unpack_from('<4f',r)),
                    'position':list(struct.unpack_from('<4f',r,16)),'quaternion':list(struct.unpack_from('<4f',r,32)),
                    'scale':list(struct.unpack_from('<3f',r,48)),'material':struct.unpack_from('<I',r,64)[0],
                    'cull_words72_76':list(struct.unpack_from('<2I',c,72))}
        rows.append(row)
    group={'reference_slot':hex(refslot),'center_slot':hex(centerslot),'render_slot':hex(renderslot),
           'rows':rows,'summary':{'reference_count':len(refs),'render_count':len(render),
            'sphere_center_matches':sum('sphere_match_record' in r for r in rows),
            'pose_position_matches':sum('pose_match_record' in r for r in rows),
            'unique_matched_sphere_indices':len({r['sphere_match_record']['render_index'] for r in rows if 'sphere_match_record' in r})}}
    out['groups'].append(group)
out['culling_record_words']={hex(slot):[{'index':i,'words72_76':list(struct.unpack_from('<2I',r,72))} for i,r in enumerate(array(slot,80))] for slot in [0x148,0x158,0x178]}
p=root/'outputs/scene-v07/103-shell-permutation-probe.json';p.write_text(json.dumps(out,indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps({'output':str(p),'summary':[g['summary'] for g in out['groups']]},indent=2))
