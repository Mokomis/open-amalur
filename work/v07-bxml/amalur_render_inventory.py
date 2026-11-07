"""Bounded inventory of inferred scene render/culling arrays; never bakes them.

Native carrier relocation is confirmed. Record/component interpretations below
are hypotheses from the selected scene bytes and require consumer corroboration.
Repeated records are reported, never removed or treated as draw instructions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import struct
from collections import defaultdict
from pathlib import Path
from amalur_blob import parse_bytes as parse_blob
from amalur_scene import SPACE_SHA256,SPACE_ID,SceneError

# Counts and storage sizes align with the next observed root array. Their
# semantic roles are deliberately provisional. No mesh stream is inferred.
PROFILES=[
    (0x118,4,'uninterpreted_u32_list_a'),(0x120,4,'uninterpreted_u32_list_b'),
    (0x128,16,'candidate_spheres_a'),(0x130,16,'candidate_spheres_b'),
    (0x140,16,'candidate_spheres_c'),
    (0x148,80,'candidate_culling_a'),(0x150,84,'candidate_render_a'),
    (0x158,80,'candidate_culling_b'),(0x160,84,'candidate_render_b'),
    (0x178,80,'candidate_culling_c'),(0x180,84,'candidate_render_c'),
]

def floats(raw,offset,count):
    # JSON remains standards compliant even if an inferred float field is wrong.
    values=struct.unpack_from('<'+'f'*count,raw,offset)
    return [v if math.isfinite(v) else {'nonfinite_bits':raw[offset+4*i:offset+4*i+4].hex()} for i,v in enumerate(values)]

def parse_bytes(data):
    blob=parse_blob(data);size=blob['header']['payload_bytes'];payload=data[8:8+size]
    slots={r['slot_payload_offset'] for r in blob['slots']}
    arrays=[];material_like_ids=set();groups=defaultdict(list)
    for slot,stride,label in PROFILES:
        if slot+8>size:raise SceneError(f'root slot {slot:#x} outside carrier')
        if slot not in slots:raise SceneError(f'root slot {slot:#x} absent from native relocation list')
        raw_pointer,count=struct.unpack_from('<II',payload,slot);target=raw_pointer-8
        if count>1_000_000 or count*stride>64*1024*1024:raise SceneError('inventory array budget exceeded')
        if target<0 or target>size or count*stride>size-target:raise SceneError(f'array {slot:#x} exceeds carrier bounds')
        records=[];exact_groups=defaultdict(list)
        for index in range(count):
            offset=target+index*stride;raw=payload[offset:offset+stride]
            record={'index':index,'payload_offset':offset,'file_offset':offset+8,'raw_hex':raw.hex(),
                    'raw_words_u32':list(struct.unpack('<'+'I'*(stride//4),raw))}
            exact_groups[raw.hex()].append(index)
            if stride==84:
                resource=struct.unpack_from('<I',raw,64)[0];material_like_ids.add(resource)
                record['inferred']={'sphere_xyz_radius':floats(raw,0,4),'position_xyz_w':floats(raw,16,4),
                    'quaternion_xyzw':floats(raw,32,4),'scale_xyz':floats(raw,48,3),
                    'flags_u32':struct.unpack_from('<I',raw,60)[0],
                    'resource_id_at_64':resource,'resource_namespace_hypothesis':'material; observed sample IDs match research material.csv',
                    'unknown_tail_words_u32':list(struct.unpack_from('<4I',raw,68))}
                # Deliberately exclude sphere and unknown tail, but retain flags.
                # This grouping is an investigative hint, NOT safe draw deduplication.
                groups[raw[16:68].hex()].append({'slot':slot,'record_index':index,'resource_id':resource})
            elif stride==80:
                record['inferred']={'first_16_floats':floats(raw,0,16),
                    'distance_squared_pair_candidate':floats(raw,64,2),
                    'unknown_words_at_72_76':list(struct.unpack_from('<2I',raw,72))}
            elif stride==16:record['inferred']={'sphere_xyz_radius':floats(raw,0,4)}
            records.append(record)
        arrays.append({'slot_payload_offset':slot,'raw_pointer':raw_pointer,'target_payload_offset':target,
            'target_file_offset':raw_pointer,'count':count,'assumed_stride_bytes':stride,'byte_length':count*stride,
            'inferred_label':label,'semantics_confirmed':False,'records':records,
            'exact_duplicate_groups':[indices for indices in exact_groups.values() if len(indices)>1]})
    intervals=sorted((r['target_payload_offset'],r['target_payload_offset']+r['byte_length']) for r in arrays if r['count'])
    if any(left[1]>right[0] for left,right in zip(intervals,intervals[1:])):
        raise SceneError('inferred inventory array spans overlap; profile is invalid')
    grouped=[v for v in groups.values() if len(v)>1]
    return {'tool':'opem-amalur-render-array-inventory','schema_version':1,'source_sha256':hashlib.sha256(data).hexdigest(),
        'source_bytes':len(data),'space_id':struct.unpack_from('<I',payload,0)[0],
        'carrier_native_evidence':blob['native_relocation'],'carrier_complete_consumption':True,
        'array_semantics_status':'inferred; no native render consumer proof','arrays':arrays,
        'resource_ids_at_render_offset_64':sorted(material_like_ids),
        'same_transform_flags_resource_groups':grouped,
        'summary':{'inventoried_arrays':len(arrays),'inventoried_records':sum(a['count'] for a in arrays),
                   'candidate_render_records':sum(a['count'] for a in arrays if a['assumed_stride_bytes']==84),
                   'unique_resource_ids_at_64':len(material_like_ids),'repeated_transform_resource_groups':len(grouped)},
        'limitations':['No triangle data, geometry stream association, draw ranges, LOD selection, or material values are decoded.',
            'Resource IDs at offset64 match material research labels in inspected examples; they are not FAB asset IDs.',
            'Duplicate groups are investigative hints only. Records are never omitted, merged, or rendered by this tool.',
            'Complete carrier consumption does not mean complete semantic decoding of the payload.']}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('space',type=Path)
    parser.add_argument('--variant',required=True,choices=['DATA_0.pak']);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();data=args.space.read_bytes()
    if args.space.name!='524859.space_bxml' or hashlib.sha256(data).hexdigest()!=SPACE_SHA256:
        raise SceneError('CLI inventory profile requires the verified DATA scene524859')
    report=parse_bytes(data)
    if report['space_id']!=SPACE_ID:raise SceneError('selected scene ID differs')
    report.update(input_file=str(args.space),archive_variant=args.variant)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(report['summary'],indent=2))

if __name__=='__main__':main()
