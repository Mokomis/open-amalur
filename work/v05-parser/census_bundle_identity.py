"""Windows-only parsed-member identity census, without exporting chunk trees."""
import collections
import hashlib
import json
import platform
import sys
from pathlib import Path

assert platform.system() == 'Windows', 'run fresh artifact analysis on Windows'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from amalur_script import inspect_bundle_file, iter_bundle_file, parse_file
from test_amalur_real_bundles import EXPECTED

root=Path.home()/'Documents'/'Opem Amalur'
source=root/'work/initial-script-corpus-v04'
standalone={}
wrapped=set();payloads=set();bindings=[];records=[]
for name,expected in EXPECTED.items():
    path=source/name
    directory=inspect_bundle_file(path)
    assert directory['input_sha256']==expected['sha256']
    summary=collections.Counter();members=[]
    for member in iter_bundle_file(path):
        binding=member['container']
        ident=binding['resource_id']
        if ident not in standalone:
            sibling=source/(str(ident)+'.lua_bxml')
            if sibling.exists():
                parsed=parse_file(sibling)
                standalone[ident]={'file':sibling.name,'input_sha256':parsed['input_sha256'],
                                   'payload_sha256':parsed['payload_sha256']}
            else:standalone[ident]=None
        sibling=standalone[ident]
        wrapped.add(member['input_sha256']);payloads.add(member['payload_sha256'])
        record={**binding,'container_file':name,'member_input_sha256':member['input_sha256'],
                'wrapper':member['wrapper'],'summary':member['chunk']['summary'],
                'standalone':sibling,
                'same_wrapped_member_as_standalone':bool(sibling and sibling['input_sha256']==member['input_sha256']),
                'same_payload_as_standalone':bool(sibling and sibling['payload_sha256']==member['payload_sha256'])}
        members.append(record);bindings.append(record);summary.update(member['chunk']['summary'])
    assert len(members)==expected['member_count'] and dict(summary)==expected['summary']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==directory['input_sha256']
    records.append({'file':name,'input_sha256':directory['input_sha256'],
                    'member_count':len(members),'summary':dict(summary),'members':members})

summary={'containers':len(records),'unique_container_hashes':len({r['input_sha256'] for r in records}),
         'member_occurrences':len(bindings),'unique_wrapped_member_hashes':len(wrapped),
         'unique_payload_hashes':len(payloads),'unique_resource_ids':len(standalone),
         'resource_ids_without_standalone':sorted(k for k,v in standalone.items() if v is None),
         'occurrences_matching_standalone_wrapper':sum(r['same_wrapped_member_as_standalone'] for r in bindings),
         'occurrences_matching_standalone_payload':sum(r['same_payload_as_standalone'] for r in bindings),
         'occurrences_with_same_payload_different_wrapper':sum(r['same_payload_as_standalone'] and not r['same_wrapped_member_as_standalone'] for r in bindings),
         'occurrences_without_standalone':sum(r['standalone'] is None for r in bindings)}
out=root/'outputs/remaining-v05/batch-parser-validation.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({'summary':summary,'records':records,
    'interpretation':'Payload equality establishes identical serialized bytecode only. Wrapper metadata bindings are preserved and are not assumed equivalent. Directory order is an observed storage order, not a native-confirmed runtime loading order.'},indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
