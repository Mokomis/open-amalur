"""Validate the observed directory+concatenated-wrapper batch layout on Windows."""
import collections
import hashlib
import json
import platform
import struct
import sys
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur'
sys.path.insert(0,str(root/'src'))
from amalur_script import parse_bytes
source=root/'work/initial-script-corpus-v04'
inventory=json.loads((root/'outputs/initial-corpus-v04/inventory.json').read_text())
names=[r['file'] for r in inventory['records'] if 'parse_error' in r]
records=[]
for name in names:
    raw=(source/name).read_bytes()
    assert len(raw)<=16*1024*1024
    count=struct.unpack_from('<I',raw)[0]
    assert 1<=count<=4096 and 4+count*8<=len(raw)
    position=4+count*8;members=[];totals=collections.Counter();ids=set()
    for index in range(count):
        ident,length=struct.unpack_from('<II',raw,4+index*8)
        assert length and position+length<=len(raw)
        member=raw[position:position+length]
        result=parse_bytes(member)
        assert result['wrapper'] is not None
        sibling=source/(str(ident)+'.lua_bxml')
        sibling_sha=hashlib.sha256(sibling.read_bytes()).hexdigest() if sibling.exists() else None
        totals.update(result['chunk']['summary'])
        members.append({'index':index,'resource_id':ident,'bytes':length,'file_offset':position,
                        'sha256':result['input_sha256'],'name':result['wrapper']['name'],
                        'summary':result['chunk']['summary'],'metadata_strings':result['wrapper']['metadata_string_count'],
                        'standalone_sha256':sibling_sha,'matches_standalone':sibling_sha==result['input_sha256']})
        assert ident not in ids
        ids.add(ident);position+=length
    assert position==len(raw)
    records.append({'file':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
                    'member_count':count,'directory_bytes':4+count*8,'consumed_bytes':position,
                    'summary':dict(totals),'standalone_matches':sum(m['matches_standalone'] for m in members),
                    'standalone_missing':sum(m['standalone_sha256'] is None for m in members),'members':members})
out=root/'outputs/remaining-v05/batch-layout-validation.json'
out.write_text(json.dumps(records,indent=2),encoding='utf-8')
print(json.dumps([{k:v for k,v in r.items() if k!='members'} for r in records],indent=2))
