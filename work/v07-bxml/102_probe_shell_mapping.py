"""Read-only correlation of selected scene render records and typed FAB IDs."""
from pathlib import Path
from collections import defaultdict,Counter
import hashlib,json,platform,struct
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur'
path=root/'work/scene-inputs-v07/DATA_0.pak/524859.space_bxml';data=path.read_bytes()
assert hashlib.sha256(data).hexdigest()=='775fb38b3fd9ff67ed3181579e935c70b33bd6831ccebf744ce4b2f6cd590143'
def array(slot,stride):
    target,count=struct.unpack_from('<II',data,8+slot)
    if count>100000 or target<8 or target+count*stride>8+struct.unpack_from('<I',data)[0]:raise ValueError('array span invalid')
    return [data[target+i*stride:target+(i+1)*stride] for i in range(count)]
def u32s(slot):return [struct.unpack('<I',r)[0] for r in array(slot,4)]
ids=u32s(0x118);counts=u32s(0x120);assert len(ids)==len(counts)
expected=dict(zip(ids,counts));assert len(expected)==len(ids)
report={'source_file':str(path),'source_sha256':hashlib.sha256(data).hexdigest(),
        'profile':'Selected scene correlations only; typed-ID mask and assembly ordering remain unconfirmed by native consumers',
        'fab_list_count':len(ids),'sum_parallel_counts':sum(counts),
        'fab_parallel_counts':[{'fab_id':key,'parallel_count':n} for key,n in zip(ids,counts)],'correlations':[]}

def record(raw,index):
    return {'index':index,'raw_hex':raw.hex(),'sphere_xyz_radius':list(struct.unpack_from('<4f',raw)),
        'position_xyz_w':list(struct.unpack_from('<4f',raw,16)),
        'quaternion_xyzw':list(struct.unpack_from('<4f',raw,32)),
        'scale_xyz':list(struct.unpack_from('<3f',raw,48)),
        'flags':struct.unpack_from('<I',raw,60)[0],'material_id_candidate':struct.unpack_from('<I',raw,64)[0],
        'opaque_tail_words':list(struct.unpack_from('<4I',raw,68))}

# Test association and repetition hypotheses separately. No result is rendered.
for slot,refslot,repeat in [(0x160,0x1b0,1),(0x150,0x1b0,2),(0x180,0x1e0,3)]:
    records=array(slot,84);refs=u32s(refslot)
    row={'render_slot':hex(slot),'reference_slot':hex(refslot),'render_count':len(records),'reference_count':len(refs),
         'tested_repeat':repeat,'count_ratio_matches':len(records)==len(refs)*repeat,
         'typed_tag_counts':dict(Counter(hex(v>>28) for v in refs)),
         'all_low28_ids_in_fab_list':all((v&0xfffffff) in expected for v in refs)}
    if not row['count_ratio_matches']:report['correlations'].append(row);continue
    groups=defaultdict(list);block_differences=[];mapped=[]
    for j,typed in enumerate(refs):
        fab=typed&0xfffffff;block=records[j*repeat:(j+1)*repeat];first=block[0]
        same=[v==first for v in block]
        if not all(same):block_differences.append({'reference_index':j,'differing_fields_by_repeat':[
            [offset for offset in range(0,84,4) if v[offset:offset+4]!=first[offset:offset+4]] for v in block]})
        key=(fab,first[16:60]) # pose only, excludes bounds and material
        groups[key].append(j)
        mapped.append({'reference_index':j,'typed_id':typed,'fab_id_candidate':fab,
                       'render_indices':list(range(j*repeat,(j+1)*repeat)),
                       'repeat_records_exactly_equal':all(same),'first_render_record':record(first,j*repeat)})
    row.update(exact_repeat_blocks=len(refs)-len(block_differences),repeat_block_differences=block_differences,
               mapped_records=mapped,pose_groups=[])
    for (fab,pose),indices in groups.items():
        expected_count=expected[fab]
        row['pose_groups'].append({'fab_id_candidate':fab,'reference_indices':indices,
            'candidate_assembly_count':len(indices),'parallel_count':expected_count,
            'count_matches_parallel':len(indices)==expected_count,
            'material_ids':[mapped[i]['first_render_record']['material_id_candidate'] for i in indices],
            'pose_raw_hex':pose.hex()})
    row['pose_group_summary']={'groups':len(groups),'count_matches_parallel':sum(g['count_matches_parallel'] for g in row['pose_groups'])}
    report['correlations'].append(row)
# Check whether the single-record stream reproduces the two-repeat stream.
a=array(0x150,84);b=array(0x160,84)
report['double_vs_single']={'count_relation':len(a)==2*len(b),
    'matching_first_of_pair':sum(a[2*i]==v for i,v in enumerate(b)) if len(a)==2*len(b) else None,
    'single_count':len(b)}
out=root/'outputs/scene-v07/102-shell-mapping-probe.json';out.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps({'output':str(out),'sum_parallel_counts':report['sum_parallel_counts'],
                 'double_vs_single':report['double_vs_single'],
                 'correlations':[{k:v for k,v in r.items() if k not in {'mapped_records','pose_groups','repeat_block_differences'}} for r in report['correlations']]},indent=2))
