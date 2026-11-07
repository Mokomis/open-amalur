"""Windows-only read-only bounded probe of scene render data and bundle links."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,platform,re,struct
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur'
index=defaultdict(list);extensions=Counter();nearby=[]
for archive,prefix in [('DATA_0.pak','DATA'),('initial_0.pak','initial'),('patch_0.pak','patch')]:
    raw=(root/f'outputs/{prefix}-archive-list.txt').read_bytes()
    text=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
    for line in text.splitlines():
        name=line.strip();match=re.fullmatch(r'(\d+)(?:_(\d+))?\.(\w+)',name)
        if match:
            key=int(match[1]);index[key].append({'archive':archive,'name':name})
            extensions[match[3]]+=1
            if 524850<=key<=524920 and match[3] not in {'dds','tex_bxml','material_bxml','mtl_bxml'}:
                nearby.append({'id':key,'archive':archive,'name':name})
report={'scope':'Selected scene and already extracted bundle/region; inventories are source evidence only, not dependency proof.',
        'extension_counts':dict(extensions),'nearby_numeric_names':nearby,'files':[]}
for archive,name in [('DATA_0.pak','524859.space_bxml'),('DATA_0.pak','524912.region_bxml'),
                     ('initial_0.pak','524859.bundle'),('initial_0.pak','524912.bundle')]:
    path=root/'work/scene-inputs-v07'/archive/name
    if not path.is_file():report['files'].append({'archive':archive,'name':name,'missing':True});continue
    data=path.read_bytes();row={'archive':archive,'name':name,'bytes':len(data),
        'sha256':hashlib.sha256(data).hexdigest(),'first_128_hex':data[:128].hex()}
    if name.endswith('.space_bxml'):
        arrays=[]
        for slot in [0x58,0x60,0x68,0x118,0x120,0x188,0x190,0x198,0x1a0,0x1a8,0x1b0,0x1c8,0x1d0,0x1d8,0x1e0]:
            target,count=struct.unpack_from('<II',data,8+slot)
            if count>1000 or target+count*4>len(data):raise ValueError('bounded root list assumption failed')
            vals=list(struct.unpack_from('<'+'I'*count,data,target))
            arrays.append({'slot':hex(slot),'target_file':target,'count':count,'u32_values':vals,
                'exact_inventory_matches':[{'index':i,'value':v,'files':index[v]} for i,v in enumerate(vals) if v in index]})
        row['candidate_u32_arrays']=arrays
    elif name.endswith('.bundle'):
        count=struct.unpack_from('<I',data,8)[0]
        if count>10000 or 16+count*4>len(data):raise ValueError('bounded bundle prefix assumption failed')
        vals=list(struct.unpack_from('<'+'I'*count,data,16));tail=data[16+count*4:]
        row.update(candidate_prefix_count=count,candidate_prefix_end=16+count*4,tail_bytes=len(tail),tail_first_256_hex=tail[:256].hex())
        row['non_texture_candidate_references']=[{'index':i,'value':v,'files':index.get(v,[])} for i,v in enumerate(vals)
            if not index.get(v) or any(n['name'].split('.',1)[1] not in {'dds','tex_bxml','material_bxml','mtl_bxml'} for n in index[v])]
        row['prefix_duplicate_ids']=[v for v,n in Counter(vals).items() if n>1]
    else:
        row['header_u32']=list(struct.unpack_from('<'+'I'*min(128,len(data)//4),data))
        row['header_inventory_hits']=[{'file_offset':i,'value':v,'files':index[v]} for i in range(0,min(len(data)-3,512),4)
            if (v:=struct.unpack_from('<I',data,i)[0]) in index]
    report['files'].append(row)
out=root/'outputs/scene-v07/100-shell-reference-probe.json'
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'output':str(out),'bytes':out.stat().st_size,'files':[{k:v for k,v in f.items() if k in {'name','bytes','candidate_prefix_count','tail_bytes'}} for f in report['files']]},indent=2))
