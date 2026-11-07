"""Windows-only bounded UV layout diagnostic; does not claim native declaration proof."""
import argparse,collections,csv,hashlib,json,math,platform,struct
from pathlib import Path
# Independently recorded layout observations from original-game importer.
# No importer source is executed, translated, or distributed by this helper.
UV0_OFFSETS={44:12,48:12,52:12,56:24,60:24,64:24,68:24}
UV1_OFFSETS={52:20,64:32,68:32}
def sha(b):return hashlib.sha256(b).hexdigest()
def candidate_uvs(raw,buffer,channel=0):
    stride=buffer['stride_bytes'];count=buffer['vertex_count'];start=buffer['data_file_offset']
    offset=(UV0_OFFSETS if channel==0 else UV1_OFFSETS).get(stride)
    if offset is None:return None
    if start<0 or count<0 or count>4000000 or start+stride*count>len(raw):raise ValueError('Vertex span outside native input')
    values=[struct.unpack_from('<ff',raw,start+i*stride+offset) for i in range(count)]
    return values

def main():
    assert platform.system()=='Windows','native artifact diagnostics run on Windows'
    ap=argparse.ArgumentParser();ap.add_argument('--shell-report',type=Path,required=True)
    ap.add_argument('--material-names',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();report=json.loads(args.shell_report.read_text(encoding='utf-8-sig'))
    records=report['admitted_records'];models=report['model_inputs']
    if len(records)>256 or len(models)>256:raise ValueError('Selected scene bound exceeded')
    names={int(r['id']):r['value'] for r in csv.DictReader(args.material_names.open(encoding='utf-8-sig'))}
    buffers=[];models_by_id={};total=0
    for model in models:
        mesh_path=Path(model['mesh_json']);raw_path=Path(model['native_mesh_file'])
        if mesh_path.stat().st_size>128*1024*1024 or raw_path.stat().st_size>256*1024*1024:raise ValueError('Input exceeds byte bound')
        mesh_bytes=mesh_path.read_bytes();raw=raw_path.read_bytes();total+=len(raw)
        if total>512*1024*1024:raise ValueError('Aggregate native input bound exceeded')
        if sha(mesh_bytes)!=model['mesh_json_sha256'] or sha(raw)!=model['native_mesh_sha256']:raise ValueError('Input SHA differs from measured shell provenance')
        mesh=json.loads(mesh_bytes);models_by_id[model['fab_id']]=mesh
        selected={mesh['assemblies'][r['assembly']]['vertex_buffer'] for r in records if r['fab_id']==model['fab_id']}
        for index in sorted(selected):
            vb=mesh['vertex_buffers'][index];item={k:vb[k] for k in ['index','header_word0','stride_bytes','vertex_count','data_file_offset','data_bytes','data_sha256']}
            item['fab_id']=model['fab_id'];item['native_file']=str(raw_path);item['channels']=[]
            for channel in (0,1):
                uvs=candidate_uvs(raw,vb,channel)
                if uvs is None:continue
                bad=[i for i,uv in enumerate(uvs) if not all(math.isfinite(v) for v in uv)]
                if bad:
                    offset=(UV0_OFFSETS if channel==0 else UV1_OFFSETS)[vb['stride_bytes']]
                    item['channels'].append({'channel':channel,'offset':offset,'status':'nonfinite_candidate_rejected','nonfinite_count':len(bad),
                        'failures':[{'vertex':i,'file_offset':vb['data_file_offset']+i*vb['stride_bytes']+offset,
                                     'raw_hex':raw[vb['data_file_offset']+i*vb['stride_bytes']+offset:vb['data_file_offset']+i*vb['stride_bytes']+offset+8].hex()} for i in bad[:8]]})
                    continue
                item['channels'].append({'status':'finite_candidate_not_native_proven','channel':channel,'offset':(UV0_OFFSETS if channel==0 else UV1_OFFSETS)[vb['stride_bytes']],
                    'format':'float32 little-endian pair','count':len(uvs),
                    'minimum':[min(p[a] for p in uvs) for a in range(2)] if uvs else None,
                    'maximum':[max(p[a] for p in uvs) for a in range(2)] if uvs else None,
                    'sample':uvs[:8], 'packed_uv_sha256':sha(b''.join(struct.pack('<ff',*p) for p in uvs))})
            buffers.append(item)
    materials=[]
    for material,count in sorted(collections.Counter(r['material_id_candidate'] for r in records).items()):
        material_records=[r for r in records if r['material_id_candidate']==material]
        materials.append({'candidate_id':material,'external_csv_name':names.get(material),'records':count,
            'sample_bindings':[{'fab_id':r['fab_id'],'assembly':r['assembly'],'render_index':r['render_index'],'first_output_vertex':r['first_output_vertex'],'output_vertices':r['output_vertices']} for r in material_records[:4]]})
    output={'scope':'Candidate UV fields from external original-game importer layout, finite-data check only; native declaration and material association remain pending.',
        'source_shell_sha256':sha(args.shell_report.read_bytes()),'geometry_sha256':report['scene_sha256'],
        'native_input_bytes':total,'selected_records':len(records),'selected_buffers':len(buffers),
        'uv_policy':'Native UV floats unchanged. No 1-v Max conversion, normalization, clamping, or implicit UV fallback.',
        'buffers':buffers,'materials':materials}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in output.items() if k not in ['buffers','materials']}))
if __name__=='__main__':main()
