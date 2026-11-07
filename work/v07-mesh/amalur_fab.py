"""Defensive FAB skeleton/descriptor reader for a bounded external format profile.

This is an independent reader of the serialized layout described in the 2018
importer reference, not a copy of that implementation. Its matrix interpretation
is an explicit reconstruction assumption until corroborated with native code.
No Max coordinate rotation or unit scaling is applied.
"""
from __future__ import annotations
import argparse, hashlib, json, math, struct
from dataclasses import dataclass
from pathlib import Path

class FabError(ValueError):
    def __init__(self,message,offset):
        self.offset=offset
        super().__init__(f'file offset0x{offset:x}: {message}')

@dataclass(frozen=True)
class Limits:
    max_file_bytes:int=64*1024*1024
    max_bones:int=8192
    max_meshes:int=65536
    max_unknown_entries:int=1_000_000
    max_remaps_per_mesh:int=8192
    max_total_remaps:int=1_000_000

class Reader:
    def __init__(self,data,limits):self.data=data;self.limits=limits;self.pos=0;self.spans=[]
    def range(self,offset,count,label):
        if offset<0 or count<0 or offset>len(self.data) or count>len(self.data)-offset:
            raise FabError(f'{label} exceeds file bounds',max(offset,0))
    def take(self,count,label):
        self.range(self.pos,count,label);start=self.pos;self.pos+=count
        self.spans.append((start,self.pos,label));return self.data[start:self.pos]
    def seek(self,offset):self.range(offset,0,'seek');self.pos=offset
    def u32(self,label):return struct.unpack('<I',self.take(4,label))[0]
    def i32(self,label):return struct.unpack('<i',self.take(4,label))[0]
    def i16(self,label):return struct.unpack('<h',self.take(2,label))[0]
    def count(self,label,maximum,stride=1):
        at=self.pos;n=self.u32(label)
        if n>maximum:raise FabError(f'{label} exceeds configured count limit',at)
        self.range(self.pos,n*stride,label);return n
    def floats(self,n,label):
        at=self.pos;values=list(struct.unpack('<'+'f'*n,self.take(n*4,label)))
        if not all(math.isfinite(v) for v in values):raise FabError(f'nonfinite {label}',at)
        return values

def multiply(a,b):
    """Row-major storage, column-vector convention: parent @ local."""
    return [sum(a[row*4+k]*b[k*4+col] for k in range(4)) for row in range(4) for col in range(4)]

def transform_point(matrix,point):
    if len(matrix)!=16 or len(point)!=3 or not all(math.isfinite(v) for v in [*matrix,*point]):
        raise ValueError('finite4x4 matrix and3D point required')
    return [sum(matrix[row*4+k]*point[k] for k in range(3))+matrix[row*4+3] for row in range(3)]

def trs_matrix(quaternion,position,scale):
    """Unit XYZW quaternion, raw component values; no normalization or axes edit."""
    x,y,z,w=quaternion
    norm2=sum(v*v for v in quaternion)
    if abs(norm2-1)>1e-3:
        return None, f'quaternion norm-squared{norm2:.9g} outside admitted unit domain'
    rotation=[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),
              2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),
              2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]
    matrix=[]
    for row in range(3):
        matrix.extend(rotation[row*3+col]*scale[col] for col in range(3));matrix.append(position[row])
    matrix.extend([0.0,0.0,0.0,1.0])
    return matrix,None

def read_trs(r,label):
    offset=r.pos;values=r.floats(12,label);q=values[:4];p=values[4:8];s=values[8:12]
    matrix,error=trs_matrix(q,p[:3],s[:3])
    return {'file_offset':offset,'raw_hex':r.data[offset:offset+48].hex(),
            'quaternion_xyzw':q,'position_xyzw':p,'scale_xyzw':s,
            'local_matrix_row_major':matrix,'transform_error':error}

def compose_bones(bones):
    complete=set()
    for start in range(len(bones)):
        if start in complete:continue
        path=[];active=set();current=start
        while current not in complete:
            if current in active:raise FabError('bone parent cycle',bones[current]['parent_file_offset'])
            active.add(current);path.append(current)
            parent=bones[current]['parent_index']
            if parent is None:break
            current=parent
        for index in reversed(path):
            bone=bones[index];local=bone['local_matrix_row_major'];parent=bone['parent_index']
            error=bone['transform_error']
            if parent is None:world=local
            elif local is None or bones[parent]['world_matrix_row_major'] is None:
                world=None;error=error or 'parent transform lies outside admitted domain'
            else:world=multiply(bones[parent]['world_matrix_row_major'],local)
            if world is not None and not all(math.isfinite(v) for v in world):
                world=None;error='composed transform is nonfinite'
            bone['world_matrix_row_major']=world;bone['world_transform_error']=error;complete.add(index)

def coverage(data_length,spans):
    intervals=[]
    for start,end,_ in sorted(spans):
        if start==end:continue
        if intervals and start<=intervals[-1][1]:intervals[-1][1]=max(end,intervals[-1][1])
        else:intervals.append([start,end])
    gaps=[];cursor=0
    for start,end in intervals:
        if start>cursor:gaps.append({'file_offset':cursor,'bytes':start-cursor})
        cursor=end
    if cursor<data_length:gaps.append({'file_offset':cursor,'bytes':data_length-cursor})
    return {'read_ranges':intervals,'uninterpreted_ranges':gaps,'bytes_read':sum(b-a for a,b in intervals)}

def parse_bytes(data:bytes,limits:Limits|None=None):
    limits=limits or Limits()
    if len(data)>limits.max_file_bytes:raise FabError('file exceeds configured byte limit',0)
    r=Reader(data,limits);r.range(0,24,'FAB header')
    header={'first_word':r.u32('first header word'),'magic':r.u32('magic'),
            'descriptor_section_offset':r.u32('descriptor section offset'),
            'unknown_word12':r.u32('header12'),'unknown_word16':r.u32('header16'),
            'bone_count':r.u32('bone count')}
    if header['magic']!=0x45533033:raise FabError('unsupported FAB skeleton magic',4)
    n=header['bone_count']
    if n>limits.max_bones:raise FabError('bone count exceeds configured limit',20)
    result={'input_sha256':hashlib.sha256(data).hexdigest(),'file_bytes':len(data),
            'profile':'external-2018-FAB-skeleton-layout','native_layout_confirmed':False,
            'matrix_convention':'row-major4x4 storage, column vectors, XYZW unit quaternion; world=parent@local; no axis/unit correction',
            'header':header,'bones':[],'mesh_descriptors':[],
            'limitations':['Observed reference profile requires real-file and native verification.',
                          'Mesh descriptor position and remap matrix roles are preserved, not assumed as extra transforms.',
                          'Static bind application requires independently identified unskinned geometry.',
                          'Skinning, inverse-bind interpretation, animation and full FAB semantics are not implemented.']}
    if not n:
        result.update(status='unsupported-no-skeleton',mesh_count=None,
                      unsupported_reason='Reference does not establish descriptor layout for a zero-bone FAB.',coverage=coverage(len(data),r.spans))
        return result
    header['unknown_word24']=r.u32('header24');pointers={}
    for name in ['transforms','parents','name_hashes','unknown40','unknown44','unknown48']:
        at=r.pos;relative=r.i32(name+' relative offset');absolute=at+relative
        r.range(absolute,0,name+' target');pointers[name]={'field_file_offset':at,'relative_i32':relative,'file_offset':absolute}
    header['relative_offsets']=pointers
    r.range(pointers['transforms']['file_offset'],n*48,'bone transform array')
    r.range(pointers['parents']['file_offset'],n*2,'bone parent array')
    r.range(pointers['name_hashes']['file_offset'],n*4,'bone name-hash array')
    r.seek(pointers['name_hashes']['file_offset']);hashes=[r.u32('bone name hash') for _ in range(n)]
    r.seek(pointers['transforms']['file_offset']);bones=[]
    for index in range(n):bones.append({'index':index,'name_hash_u32':hashes[index],**read_trs(r,'bone TRS')})
    r.seek(pointers['parents']['file_offset'])
    for index,bone in enumerate(bones):
        at=r.pos;parent=r.i16('bone parent');bone['parent_raw_i16']=parent;bone['parent_file_offset']=at
        if parent==-1 or parent==index:bone['parent_index']=None;bone['root_form']='minus-one' if parent==-1 else 'self-index'
        elif 0<=parent<n:bone['parent_index']=parent;bone['root_form']=None
        else:raise FabError('bone parent index outside admitted range',at)
    compose_bones(bones);result['bones']=bones
    r.seek(header['descriptor_section_offset']);definition={'file_offset':r.pos,'unknown_hash_u32':r.u32('descriptor section hash')}
    count=r.count('unknown u32 list count',limits.max_unknown_entries,4)
    definition['unknown_u32_list']={'count':count,'file_offset':r.pos};r.take(count*4,'unknown u32 list')
    count=r.count('unknown block count',limits.max_unknown_entries,13);groups=[]
    for _ in range(count):
        at=r.pos;entries=r.count('unknown vector block count',limits.max_unknown_entries,12)
        r.take(entries*12+9,'unknown vector block and9-byte trailer');groups.append({'file_offset':at,'count':entries,'record_bytes':entries*12+13})
    definition['unknown_blocks']=groups
    for key,stride in [('unknown_u32_list2',4),('unknown_u16_list',2)]:
        count=r.count(key+' count',limits.max_unknown_entries,stride);definition[key]={'count':count,'file_offset':r.pos};r.take(count*stride,key)
    count=r.count('mesh descriptor count',limits.max_meshes,69);result['mesh_count']=count;definition['mesh_descriptors_offset']=r.pos
    descriptors=[];total_remaps=0
    for index in range(count):
        start=r.pos;position=r.floats(3,'mesh position');unknown=r.floats(4,'mesh unknown floats')
        remap_count=r.count('mesh remap count',limits.max_remaps_per_mesh,52);total_remaps+=remap_count
        if total_remaps>limits.max_total_remaps:raise FabError('total remap count exceeds configured limit',r.pos-4)
        remaps=[]
        for _ in range(remap_count):
            transform=read_trs(r,'remap TRS');at=r.pos;bone_id=r.i32('remap bone index')
            if bone_id < -1 or bone_id>=n:raise FabError('remap bone index outside admitted range',at)
            remaps.append({'bone_index':bone_id,'bone_index_file_offset':at,'trs':transform})
        unknown2=r.floats(2,'mesh unknown pair');at=r.pos;bone_id=r.i32('mesh bone index')
        if bone_id < -1 or bone_id>=n:raise FabError('mesh bone index outside admitted range',at)
        tail=r.take(25,'mesh descriptor tail')
        matrix=bones[bone_id]['world_matrix_row_major'] if bone_id>=0 else None
        reason='mesh has no mapped bone' if bone_id<0 else bones[bone_id]['world_transform_error']
        descriptors.append({'index':index,'file_offset':start,'byte_length':r.pos-start,
                            'position_xyz_uninterpreted':position,'unknown_four_floats':unknown,'remaps':remaps,
                            'unknown_two_floats':unknown2,'bone_index':bone_id,'bone_index_file_offset':at,
                            'tail25_hex':tail.hex(),'static_bind_candidate':matrix,
                            'static_bind_candidate_error':reason})
    definition['parsed_end_offset']=r.pos;result['definition']=definition;result['mesh_descriptors']=descriptors
    result['status']='parsed-reference-profile';result['coverage']=coverage(len(data),r.spans)
    return result

def parse_file(path,limits:Limits|None=None):
    path=Path(path);limits=limits or Limits()
    if path.stat().st_size>limits.max_file_bytes:raise FabError('file exceeds configured byte limit',0)
    result=parse_bytes(path.read_bytes(),limits);result['input_path']=str(path);return result

def static_bind_matrix(report,mesh_index,*,vertices_are_unskinned=False):
    if not vertices_are_unskinned:raise ValueError('caller must independently establish unskinned geometry')
    if report['status']!='parsed-reference-profile':raise ValueError(report.get('unsupported_reason','FAB not admitted'))
    if not 0<=mesh_index<len(report['mesh_descriptors']):raise ValueError('mesh index outside parsed descriptors')
    descriptor=report['mesh_descriptors'][mesh_index]
    if descriptor['static_bind_candidate'] is None:raise ValueError(descriptor['static_bind_candidate_error'])
    return list(descriptor['static_bind_candidate'])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('input',type=Path);parser.add_argument('--output',type=Path);args=parser.parse_args()
    report=parse_file(args.input)
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in {'bones','mesh_descriptors','coverage','definition'}},indent=2))
if __name__=='__main__':main()
