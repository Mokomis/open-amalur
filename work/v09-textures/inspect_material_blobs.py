"""Windows-only selected material blob layout diagnostic; no slot semantics inferred."""
import argparse,hashlib,json,platform,struct,sys
from pathlib import Path

def main():
    assert platform.system()=='Windows'
    root=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(root/'work/v07-bxml'))
    from amalur_blob import parse_bytes
    ap=argparse.ArgumentParser();ap.add_argument('--input-root',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    paths=sorted(args.input_root.glob('*.mat_bxml'))
    if not 1<=len(paths)<=256:raise ValueError('Selected material file count bound exceeded')
    reports=[]
    for path in paths:
        if path.stat().st_size>1024*1024:raise ValueError('Material diagnostic byte bound exceeded')
        data=path.read_bytes();blob=parse_bytes(data)
        item={'file':str(path),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'status':'unadmitted'}
        try:
            slots={r['slot_payload_offset'] for r in blob['slots']}
            if slots!={0,8} or len(data)<40:raise ValueError('Different selected material relocation/header shape')
            params,pc,textures,tc,shader=struct.unpack_from('<5I',data,8);end=8+blob['header']['payload_bytes']
            if pc>4096 or tc>256 or params!=40 or textures!=params+pc*24 or textures+tc*8!=end:raise ValueError('Different material parameter/texture span shape')
            item.update(status='observed_shape',shader_id_candidate=shader,root_unknown_words=list(struct.unpack_from('<3I',data,28)),
                parameters=[{'file_offset':params+i*24,'raw_hex':data[params+i*24:params+(i+1)*24].hex(),
                             'value_hex':data[params+i*24:params+i*24+16].hex(),'tail_words':list(struct.unpack_from('<II',data,params+i*24+16))} for i in range(pc)],
                textures=[{'file_offset':textures+i*8,'asset_id_candidate':struct.unpack_from('<I',data,textures+i*8)[0],
                           'slot_candidate':struct.unpack_from('<I',data,textures+i*8+4)[0]} for i in range(tc)])
        except ValueError as error:item['reason']=str(error)
        reports.append(item)
    output={'scope':'Strict observed selected-material compiled carrier shape; array record meanings, material association, shader and texture slots require native confirmation.',
            'materials':reports,'accepted_shape':sum(r['status']=='observed_shape' for r in reports),'requested':len(paths)}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in output.items() if k!='materials'}))
if __name__=='__main__':main()
