"""Inventory the native-confirmed payload + fixup-slot carrier in scene files.

The native loader0x00a6e7c0 copies the payload and applies each tail slot using
base + raw_word -8. Consequently the stored target word is a file-relative byte
offset; its payload-relative target is raw_word-8. No relocation is performed.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path

NATIVE_RELOCATION = {
    'function': '0x00a6e7c0',
    'evidence_id': 'ev_7b9c3ccd46c531ada6ac97c7567cad6344100def168548da4614af298724b0c5',
    'evidence_file': 'blob_asset_loader.json',
    'target_sha256': '16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314',
    'observed_rule': '*(base + tail_slot) = raw_word + base -8',
    'evidence_kind': 'native static pseudocode; not a live game observation',
}

class BlobError(ValueError): pass

@dataclass(frozen=True)
class Limits:
    max_file_bytes: int = 256 * 1024 * 1024
    max_slots: int = 1_000_000

def digest(data): return hashlib.sha256(data).hexdigest()

def parse_bytes(data: bytes, limits: Limits | None = None):
    limits = limits or Limits()
    if len(data) > limits.max_file_bytes: raise BlobError('file exceeds configured byte limit')
    if len(data) < 8: raise BlobError('truncated two-length header')
    payload_bytes, tail_bytes = struct.unpack_from('<II', data, 0)
    if payload_bytes + tail_bytes != len(data)-8:
        raise BlobError('two declared lengths plus8 do not equal the file size')
    if tail_bytes % 4: raise BlobError('relocation tail is not a multiple of4 bytes in the admitted profile')
    count = tail_bytes // 4
    if count > limits.max_slots: raise BlobError('relocation slot count exceeds configured limit')
    payload_start, tail_start = 8, 8+payload_bytes
    payload = data[payload_start:tail_start]
    tail = data[tail_start:]
    records = []
    counts = collections.Counter()
    for index in range(count):
        entry_offset = tail_start+4*index
        slot = struct.unpack_from('<I',data,entry_offset)[0]
        if slot > payload_bytes or payload_bytes-slot < 4:
            raise BlobError(f'relocation slot entry{index} offset{slot} cannot address a complete payload uint32')
        pointer = struct.unpack_from('<I',payload,slot)[0]
        following = struct.unpack_from('<I',payload,slot+4)[0] if payload_bytes-slot >= 8 else None
        raw = payload[slot:slot+min(8,payload_bytes-slot)]
        target_offset = pointer - 8
        in_payload = 0 <= target_offset < payload_bytes
        record = {'index':index,'entry_file_offset':entry_offset,'slot_payload_offset':slot,
                  'slot_file_offset':payload_start+slot,'slot_alignment_mod4':slot%4,
                  'word_u32':pointer,'word_hex':f'{pointer:08x}',
                  'target_payload_offset':target_offset,'target_file_offset':pointer,
                  'relocated_target_in_payload':in_payload,
                  'following_word_u32':following,'slot_preview_hex':raw.hex()}
        records.append(record)
        counts[slot] += 1
    duplicated = [{'slot_payload_offset':slot,'occurrences':count} for slot,count in sorted(counts.items()) if count>1]
    return {'schema_version':2,'tool':'opem-amalur-blob-reader',
            'format_status':'carrier relocation confirmed statically; payload object types remain unmodeled',
            'native_relocation':NATIVE_RELOCATION,
            'input_sha256':digest(data),'input_bytes':len(data),
            'header':{'file_offset':0,'bytes':8,'raw_hex':data[:8].hex(),
                      'payload_bytes':payload_bytes,'tail_bytes':tail_bytes},
            'payload':{'file_offset':payload_start,'bytes':payload_bytes,'sha256':digest(payload),
                       'prefix_hex':payload[:64].hex(),'interpretation':'opaque bytes'},
            'tail':{'file_offset':tail_start,'bytes':tail_bytes,'sha256':digest(tail),
                    'interpretation':'payload-relative uint32 relocation slot offsets'},
            'complete_carrier_consumption':True,'payload_semantics_decoded':False,
            'summary':{'relocation_slots':len(records),'unique_relocation_slots':len(counts),
                       'duplicate_slots':duplicated,'slots_unaligned_mod4':sum(r['slot_alignment_mod4']!=0 for r in records),
                       'relocated_targets_inside_payload':sum(r['relocated_target_in_payload'] for r in records),
                       'zero_slot_words':sum(r['word_u32']==0 for r in records),
                       'max_slot_payload_offset':max(counts,default=None)},
            'slots':records,
            'limitations':['Carrier loading and relocation are statically confirmed for the selected Windows executable; no live game behavior was observed.',
                           'Following words are retained as uninterpreted uint32 values; they are not declared array counts.',
                           'No pointers are relocated and no payload bytes are changed.',
                           'World objects, transforms, resource references and gameplay semantics remain undecoded.']}

def parse_file(path: Path, limits=None):
    limits = limits or Limits()
    if path.stat().st_size > limits.max_file_bytes: raise BlobError('file exceeds configured byte limit')
    result = parse_bytes(path.read_bytes(),limits)
    result['input_file'] = str(path)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    result=parse_file(args.input)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ['input_file','input_sha256','input_bytes','header','summary']},indent=2))

if __name__=='__main__':main()
