"""Windows-only bounded structural parse/diff probe for selected enum variants."""
import argparse,hashlib,json,platform,sys
from pathlib import Path
from amalur_bxml import parse_bytes,BxmlError
assert platform.system()=='Windows'
ap=argparse.ArgumentParser();ap.add_argument('input_dir',type=Path);ap.add_argument('--output',type=Path,required=True)
args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True);rows=[]
paths=sorted(p for p in args.input_dir.glob('compiled_enums*') if p.is_file())
for path in paths:
    data=path.read_bytes();row={'file':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'first64_hex':data[:64].hex()}
    try:
        result=parse_bytes(data)
        dest=args.output/(path.name+'.parsed.json');dest.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
        row.update(parsed_file=str(dest),summary=result['summary'],complete_consumption=result['complete_consumption'])
        hits=[v for v in result['values'] if any(term in (v['utf8'] or '').lower() for term in ['space_type','outdoor','indoor'])]
        indices={v['index'] for v in hits};owners={a['owner_node'] for a in result['attributes'] if a['value_index'] in indices}
        nodes=set(owners)
        for owner in owners:
            node=result['nodes'][owner];nodes.update(node['children'])
            if node['parent']!=-1:nodes.add(node['parent'])
        row['matching_values']=hits;row['matching_node_neighborhood']=[]
        for index in sorted(nodes):
            node=result['nodes'][index]
            attrs=result['attributes'][node['attribute_start']:node['attribute_start']+node['attribute_count']]
            enriched=[]
            for attr in attrs:
                enriched.append(dict(attr,value=None if attr['value_missing'] else result['values'][attr['value_index']]))
            row['matching_node_neighborhood'].append(dict(node,attributes=enriched))
        row['first_nodes']=result['nodes'][:5];row['local_symbols']=result['local_symbols'];row['first_values']=result['values'][:20]
    except (BxmlError,ValueError,IndexError) as exc:row['error']=str(exc)
    rows.append(row)
out=args.output/'108-enum-probe.json';out.write_text(json.dumps({'variants':rows},indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps({'report':str(out),'variants':[{k:r[k] for k in ['file','bytes','sha256','summary','error'] if k in r} for r in rows]},indent=2))
