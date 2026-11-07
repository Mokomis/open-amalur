"""Windows-only batch observation of explicitly selected extracted FAB copies."""
import argparse,hashlib,json,platform
from pathlib import Path
from amalur_fab import parse_file
assert platform.system()=='Windows','fresh artifact inspection runs on Windows'
ap=argparse.ArgumentParser();ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
files=sorted(args.inputs.rglob('*.fab_bxml'))
if len(files)>256:raise ValueError('explicit batch exceeds256-file boundary')
args.output.mkdir(parents=True,exist_ok=True);records=[];reports={};identities={}
for p in files:
    digest=hashlib.sha256(p.read_bytes()).hexdigest();asset_id=p.name.removesuffix('.fab_bxml')
    record={'file':str(p),'sha256':digest,'asset_id':asset_id};identities.setdefault(asset_id,set()).add(digest)
    try:
        report=parse_file(p);reports[digest]=report;name=digest+'.json';(args.output/name).write_text(json.dumps(report,indent=2),encoding='utf-8')
        descriptors=report['mesh_descriptors']
        record.update(status=report['status'],bones=len(report['bones']),mesh_count=report['mesh_count'],
                      static_bind_candidates=sum(d['static_bind_candidate'] is not None for d in descriptors),
                      nonidentity_bones=sum(b['world_matrix_row_major'] is not None and b['world_matrix_row_major']!=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1] for b in report['bones']),
                      report=name)
    except (ValueError,OverflowError) as exc:record.update(status='rejected',error=str(exc))
    records.append(record)
ambiguous_ids=[]
for asset_id,digests in identities.items():
    if len(digests)!=1:
        ambiguous_ids.append(asset_id)
        if (args.output/(asset_id+'.json')).exists():raise ValueError('stale asset-id report exists for ambiguous variants; choose a fresh output directory')
        continue
    digest=next(iter(digests))
    if digest in reports:
        (args.output/(asset_id+'.json')).write_text(json.dumps(reports[digest],indent=2),encoding='utf-8')
result={'scope':'External-profile skeleton/descriptor interpretation of selected extracted FAB copies; no native or runtime equivalence claim.',
        'files':len(records),'parsed':sum(r['status']=='parsed-reference-profile' for r in records),
        'asset_id_report_layout':'ID.json only when all selected variants of that ID have one exact SHA256',
        'ambiguous_variant_ids':ambiguous_ids,'records':records}
(args.output/'batch.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
