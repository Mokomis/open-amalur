"""Windows-only measured-shell sidecar assembler with explicit bounded bindings.
No texture slot, archive variant or UV layout is guessed from names/filenames.
Unselected materials/layouts remain the existing diagnostic vertex colors.
"""
import argparse,hashlib,json,math,platform,struct,sys
from pathlib import Path
from keen_texture import decode as decode_texture
from material_package import encode,FALLBACK,MAX_BYTES

def sha(b):return hashlib.sha256(b).hexdigest()
def read(path,maximum):
    p=Path(path)
    if p.stat().st_size>maximum:raise ValueError('Input byte bound exceeded: '+str(p))
    return p.read_bytes()
def json_read(path,maximum=128*1024*1024):return json.loads(read(path,maximum).decode('utf-8-sig'))
def require_evidence(item):
    if not isinstance(item.get('evidence'),list) or not item['evidence'] or any(not isinstance(s,str) or not s for s in item['evidence']):raise ValueError('Explicit nonempty evidence/assumption notes required')

def main():
    assert platform.system()=='Windows','fresh native artifact work runs on Windows'
    root=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(root/'work/v07-bxml'))
    from amalur_blob import parse_bytes as parse_blob
    from amalur_shell import render_pose
    ap=argparse.ArgumentParser();ap.add_argument('--scene-bin',required=True,type=Path);ap.add_argument('--combined-report',required=True,type=Path)
    ap.add_argument('--shell-bin',required=True,type=Path);ap.add_argument('--shell-report',required=True,type=Path)
    ap.add_argument('--profile',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--report',required=True,type=Path)
    args=ap.parse_args();scene=read(args.scene_bin,64*1024*1024);shell=read(args.shell_bin,64*1024*1024)
    combined=json_read(args.combined_report);shell_report=json_read(args.shell_report);profile=json_read(args.profile,1024*1024)
    if profile.get('schema_version')!=1 or not isinstance(profile.get('scope'),str) or not profile['scope']:raise ValueError('Explicit material profile version/scope required')
    if sha(scene)!=combined['scene_sha256'] or sha(shell)!=shell_report['scene_sha256']:raise ValueError('Scene receipt identity mismatch')
    if scene[:8]!=b'OMSC07\0\0' or shell[:8]!=b'OMSC07\0\0':raise ValueError('Expected unchanged measured scene geometry')
    count=struct.unpack_from('<I',scene,8)[0];shell_count=struct.unpack_from('<I',shell,8)[0]
    if len(scene)!=36+36*count or len(shell)!=36+36*shell_count:raise ValueError('Scene length mismatch')
    segments=[s for s in combined['inputs'] if s['sha256']==sha(shell)]
    if len(segments)!=1 or segments[0]['vertices']!=shell_count:raise ValueError('Shell identity absent/ambiguous in combined scene')
    base=segments[0]['first_output_vertex']
    if type(base)is not int or base<0 or base+shell_count>count or scene[36+base*36:36+(base+shell_count)*36]!=shell[36:]:raise ValueError('Combined scene shell vertex range differs byte-for-byte')
    layouts={}
    for item in profile['uv_layouts']:
        require_evidence(item);key=(item['header_word0'],item['stride_bytes']);offset=item['uv_offset']
        if key in layouts or any(type(v)is not int for v in (*key,offset)) or not 20<=key[1]<=128 or offset<12 or offset%4 or offset+8>key[1]:raise ValueError('Invalid/duplicate explicit UV profile')
        layouts[key]=item
    if not 1<=len(layouts)<=16 or not 1<=len(profile['materials'])<=256:raise ValueError('Profile size bound exceeded')
    textures=[];bindings={};texture_receipts=[];texture_dedupe={}
    for binding in profile['materials']:
        require_evidence(binding);material=binding['material_id'];slot=binding['texture_slot'];tid=binding['texture_id']
        if type(material)is not int or not 0<material<=0xffffffff or material in bindings or type(slot)is not int or not 0<=slot<=255 or type(tid)is not int or not 0<tid<=0xffffffff:raise ValueError('Invalid/duplicate explicit material binding')
        data=read(binding['material_file'],1024*1024)
        if sha(data)!=binding['material_sha256']:raise ValueError('Material SHA mismatch')
        blob=parse_blob(data);slots={s['slot_payload_offset'] for s in blob['slots']}
        if slots!={0,8} or len(data)<40:raise ValueError('Different material carrier layout')
        pp,pc,tp,tc,shader=struct.unpack_from('<5I',data,8)
        if pc>4096 or tc>256 or pp!=40 or tp!=pp+pc*24 or tp+tc*8!=8+blob['header']['payload_bytes'] or shader!=binding['shader_id']:raise ValueError('Material array/shader identity mismatch')
        matches=[struct.unpack_from('<II',data,tp+i*8) for i in range(tc) if struct.unpack_from('<I',data,tp+i*8+4)[0]==slot]
        if matches!=[(tid,slot)]:raise ValueError('Texture slot does not uniquely match explicit binding')
        raw=read(binding['texture_file'],32*1024*1024)
        if sha(raw)!=binding['texture_sha256']:raise ValueError('Texture SHA mismatch')
        level=binding.get('decode_level',0);key=(sha(raw),level)
        if key not in texture_dedupe:
            rgba,receipt=decode_texture(raw,level)
            if receipt['asset_id']!=tid:raise ValueError('Texture embedded asset ID mismatch')
            if receipt['alpha_min']!=255:raise ValueError('Selected opaque preview texture has nonopaque alpha; requires separate material proof')
            texture_dedupe[key]=len(textures);textures.append({'width':receipt['decoded_width'],'height':receipt['decoded_height'],'rgba':rgba})
            texture_receipts.append(dict(receipt,texture_index=len(textures)-1,input_file=binding['texture_file']))
        bindings[material]={'texture_index':texture_dedupe[key],'binding':binding}
    models={r['fab_id']:r for r in shell_report['model_inputs']};cache={};uvs=[(0.,0.)]*count;draws=[];coverage=[];cursor=0
    def add_draw(first,n,texture):
        if not n:return
        if draws and draws[-1]['texture_index']==texture and draws[-1]['first_vertex']+draws[-1]['vertex_count']==first:draws[-1]['vertex_count']+=n
        else:draws.append({'first_vertex':first,'vertex_count':n,'texture_index':texture})
    add_draw(0,base,FALLBACK)
    for record in shell_report['admitted_records']:
        first=record['first_output_vertex'];n=record['output_vertices'];material=record['material_id_candidate'];reason='material is not explicitly selected';texture=FALLBACK
        if first!=cursor or n<=0 or n%3 or first+n>shell_count:raise ValueError('Shell receipt coverage/order invalid')
        if material in bindings:
            model=models[record['fab_id']]
            if record['fab_id'] not in cache:
                mb=read(model['mesh_json'],128*1024*1024);fb=read(model['fab_json'],128*1024*1024);raw=read(model['native_mesh_file'],256*1024*1024)
                if sha(mb)!=model['mesh_json_sha256'] or sha(fb)!=model['fab_json_sha256'] or sha(raw)!=model['native_mesh_sha256']:raise ValueError('Original selected geometry identity mismatch')
                cache[record['fab_id']]=(json.loads(mb),json.loads(fb),raw)
            mesh,fab,raw=cache[record['fab_id']];assembly=mesh['assemblies'][record['assembly']];vb=mesh['vertex_buffers'][assembly['vertex_buffer']];indices=mesh['index_buffers'][assembly['index_buffer']]['indices']
            layout=layouts.get((vb['header_word0'],vb['stride_bytes']))
            if layout is None:reason='vertex layout is not explicitly selected'
            else:
                if len(indices)!=n:raise ValueError('Selected assembly expanded vertex count differs')
                offset=layout['uv_offset'];start=vb['data_file_offset'];stride=vb['stride_bytes'];center=fab['mesh_descriptors'][record['assembly']]['position_xyz_uninterpreted']
                if start<0 or vb['vertex_count']*stride>len(raw)-start:raise ValueError('Vertex span exceeds selected raw buffer')
                for j,index in enumerate(indices):
                    if type(index)is not int or not 0<=index<vb['vertex_count']:raise ValueError('Vertex index invalid')
                    uv=struct.unpack_from('<ff',raw,start+index*stride+offset)
                    if not all(math.isfinite(x) for x in uv):raise ValueError('Nonfinite explicitly selected UV')
                    point=render_pose(vb['positions'][index],record,center)
                    if struct.pack('<3f',*point)!=shell[36+(first+j)*36:48+(first+j)*36]:raise ValueError('UV index does not match exact baked shell position')
                    uvs[base+first+j]=uv
                texture=bindings[material]['texture_index'];reason='explicit selected material/texture/UV profile';
        add_draw(base+first,n,texture);coverage.append({'render_index':record['render_index'],'fab_id':record['fab_id'],'assembly':record['assembly'],'material_id_candidate':material,'first_vertex':base+first,'vertices':n,'texture_index':texture,'reason':reason});cursor+=n
    if cursor!=shell_count:raise ValueError('Shell records do not cover measured shell')
    add_draw(base+shell_count,count-base-shell_count,FALLBACK)
    binary,receipt=encode(scene,uvs,draws,textures)
    if not receipt['textured_vertices']:raise ValueError('No explicitly selected texture binding reached scene geometry')
    if args.output.exists() or args.report.exists():raise ValueError('Use fresh output paths; prior packages are preserved')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(binary)
    receipt.update(profile=profile,profile_sha256=sha(args.profile.read_bytes()),source_shell_sha256=sha(shell),combined_report_sha256=sha(args.combined_report.read_bytes()),
        textures=texture_receipts,draw_ranges=draws,shell_record_coverage=coverage,
        limitations=['Explicit single-base-color preview; no native complete shader/material/lighting equivalence.',
                    'Unselected materials, UV layouts and prop ranges retain diagnostic colors.',
                    'UV and texture source rows unchanged; no Max 1-v flip. Opaque linear-repeat host sampler policy.'])
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(receipt,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['profile','textures','draw_ranges','shell_record_coverage']},indent=2))
if __name__=='__main__':main()
