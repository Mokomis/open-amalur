"""Read-only asset-identity overlap audit for the selected scene collections."""
from pathlib import Path
from collections import Counter
import hashlib,json,platform,struct
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur';path=root/'work/scene-inputs-v07/DATA_0.pak/524859.space_bxml';data=path.read_bytes()
assert hashlib.sha256(data).hexdigest()=='775fb38b3fd9ff67ed3181579e935c70b33bd6831ccebf744ce4b2f6cd590143'
def array(slot,stride):
    pointer,count=struct.unpack_from('<II',data,8+slot)
    assert pointer>=8 and pointer+count*stride<=8+struct.unpack_from('<I',data)[0]
    return [data[pointer+i*stride:pointer+(i+1)*stride] for i in range(count)]
catalog=[struct.unpack('<I',r)[0] for r in array(0x118,4)]
parallel=[struct.unpack('<I',r)[0] for r in array(0x120,4)]
props=Counter(struct.unpack_from('<I',r,52)[0] for r in array(0x98,80))
primary=Counter(struct.unpack('<I',r)[0]&0xfffffff for r in array(0x1b0,4))
secondary=Counter(struct.unpack('<I',r)[0]&0xfffffff for r in array(0x1e0,4))
singleton=Counter(struct.unpack('<I',r)[0]&0xfffffff for r in array(0x198,4))
summary={'catalog_ids':len(catalog),'prop_instances':sum(props.values()),'prop_unique_ids':len(props),
         'primary_assembly_references':sum(primary.values()),'primary_unique_ids':len(primary),
         'secondary_references':sum(secondary.values()),'secondary_unique_ids':len(secondary),
         'primary_prop_shared_ids':sorted(set(primary)&set(props)),
         'secondary_prop_shared_ids':sorted(set(secondary)&set(props)),
         'primary_secondary_shared_ids':sorted(set(primary)&set(secondary)),
         'catalog_ids_not_in_observed_collections':sorted(set(catalog)-(set(props)|set(primary)|set(secondary)|set(singleton)))}
report={'source_file':str(path),'source_sha256':hashlib.sha256(data).hexdigest(),'summary':summary,
        'rows':[{'fab_id':key,'parallel_count':count,'prop_instances':props[key],'primary_assembly_refs':primary[key],
                 'secondary_refs':secondary[key],'singleton_refs':singleton[key]} for key,count in zip(catalog,parallel)],
        'limitations':['Asset-ID disjointness rules out the same FAB being drawn twice across those two collections; it does not establish object transforms or native draw equivalence.',
                       'The76-ID root list is a resource inventory, not76 additional placements; never draw it by itself.']}
p=root/'outputs/scene-v07/107-scene-collection-audit.json';p.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
