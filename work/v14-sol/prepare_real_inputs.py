"""Preserve exact source records for the bounded decoder investigation."""
from pathlib import Path
import hashlib,json
root=Path.home()/'Documents/Opem Amalur';out=root/'outputs/scene-v14-sol';out.mkdir(exist_ok=True)
dest=root/'work/v14-sol/real-inputs';dest.mkdir(parents=True,exist_ok=True)
graph=json.loads((root/'outputs/scene-v12/type-graph.json').read_text());rows=[]
for node in graph['nodes']:
 origin=node['source'];p=root/'work/scene-inputs-v09'/origin['archive']/origin['batch'];batch=p.read_bytes();raw=batch[origin['offset']:origin['offset']+origin['bytes']]
 if len(raw)!=origin['bytes'] or hashlib.sha256(raw).hexdigest()!=origin['sha256']:raise ValueError('Source record provenance mismatch')
 target=dest/f"{node['type_id']}.simtype_bxml"
 if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve differing fixture')
 target.write_bytes(raw);rows.append(dict(type_id=node['type_id'],name=node['name'],bytes=len(raw),sha256=origin['sha256'],file=str(target),source=origin,selected_primary=node['type_id']==230417))
manifest=dict(status='exact original input snapshots; no field interpretation added',inputs=rows,acceptance_criteria=['One actual original type fully consumed by decoder without unknown-byte guessing','Field meaning and parsing operations linked to pinned native addresses or disassembly','Decoded structure consistent with native consumer; candidate source correlations labeled separately','Malformed/truncated inputs refused; original executable and source assets unchanged','No Android integration or gameplay claims from parser validation alone'])
(out/'real-inputs-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(dict(records=len(rows),total_bytes=sum(x['bytes'] for x in rows),primary=[x for x in rows if x['selected_primary']])))
