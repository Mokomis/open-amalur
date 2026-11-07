"""Decode only explicitly supplied extracted-stream directories on Windows."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
assert platform.system()=='Windows', 'Fresh target decoding runs on Windows'
from amalur_mesh import MeshError, export_obj, export_portable, parse_file

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-root',action='append',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--ids',nargs='+')
    parser.add_argument('--prefer-last',action='store_true',help='Explicit analyst root precedence; not inferred game load order')
    parser.add_argument('--obj',action='store_true')
    args=parser.parse_args()
    suffix='.fab_visual_data_streamable_bin'
    wanted=set(args.ids) if args.ids else None
    candidates={}
    for root in args.input_root:
        if not root.is_dir():raise ValueError('missing input root '+str(root))
        for path in sorted(root.glob('*'+suffix)):
            key=path.name[:-len(suffix)]
            if wanted is not None and key not in wanted:continue
            candidates.setdefault(key,[]).append(path)
    args.output.mkdir(parents=True,exist_ok=True)
    records=[]
    for key,paths in sorted(candidates.items()):
        provenance=[{'path':str(path),'sha256':digest(path),'bytes':path.stat().st_size} for path in paths]
        row={'asset_id_text':key,'candidate_inputs':provenance}
        try:
            if len({r['sha256'] for r in provenance})>1 and not args.prefer_last:
                raise ValueError('conflicting extracted variants require explicit --prefer-last or one selected root')
            chosen=paths[-1] if args.prefer_last else paths[0]
            source=parse_file(chosen)
            dest=args.output/key;dest.mkdir(exist_ok=True)
            mesh=dest/'native-mesh.json';portable=dest/'mesh.ommesh'
            source['portable_export']=export_portable(source,portable)
            mesh.write_text(json.dumps(source,indent=2)+'\n',encoding='utf-8')
            if args.obj:export_obj(source,dest/'mesh.obj')
            row.update(status='decoded',selected_input=str(chosen),input_sha256=source['input_sha256'],
                       summary=source['summary'],mesh_json=str(mesh),mesh_json_sha256=digest(mesh),
                       portable=source['portable_export'])
        except (MeshError,ValueError,OSError) as exc:row.update(status='unresolved',reason=str(exc))
        records.append(row)
    for key in sorted((wanted or set())-set(candidates)):
        records.append({'asset_id_text':key,'status':'unresolved','reason':'no stream in supplied input directories','candidate_inputs':[]})
    success=[r for r in records if r['status']=='decoded']
    report={'scope':'Selected extracted geometry streams only; no world placement, skeleton, material or complete render claim.',
            'input_roots':[str(p) for p in args.input_root],
            'variant_policy':'last supplied root wins by explicit analyst choice' if args.prefer_last else 'conflicting variants rejected',
            'selected_asset_ids':sorted(wanted) if wanted else None,
            'decoded':len(success),'unresolved':len(records)-len(success),
            'unique_mesh_vertices':sum(r['summary']['vertices'] for r in success),
            'unique_mesh_triangles':sum(r['summary']['triangles_in_buffers'] for r in success),
            'records':records}
    (args.output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items() if key!='records'},indent=2))
    if report['unresolved']:raise SystemExit(1)

if __name__=='__main__':main()
