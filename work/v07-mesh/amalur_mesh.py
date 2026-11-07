"""Bounded FAB stream geometry reader; no 3ds Max code is executed or bundled.

The carrier layout was inferred from an author's original-game importer and
must be checked against the selected Re-Reckoning input. Native coordinates
and source precision are retained. No material, skeleton or animation claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path

SOURCE = 'https://lukascone.wordpress.com/2018/04/11/kingdoms-of-amalur-import-tool/'
ADMITTED_STRIDES = frozenset({20,24,44,48,52,56,60,64,68})
ASSEMBLY_BYTES = 52
MAGIC = b'OMMESH1\0'

class MeshError(ValueError):
    def __init__(self,message,offset=None):
        self.offset=offset
        super().__init__(message+(f' at file offset0x{offset:x}' if offset is not None else ''))

@dataclass(frozen=True)
class Limits:
    max_bytes: int = 256*1024*1024
    max_buffers: int = 65_536
    max_assemblies: int = 65_536
    max_vertices: int = 4_000_000
    max_indices: int = 12_000_000

class Cursor:
    def __init__(self,data):self.data=data;self.pos=0
    @property
    def remaining(self):return len(self.data)-self.pos
    def take(self,n,label):
        if n<0 or n>self.remaining:raise MeshError('truncated '+label,self.pos)
        at=self.pos;self.pos+=n;return self.data[at:self.pos]
    def u32(self,label):return struct.unpack('<I',self.take(4,label))[0]

def sha(data):return hashlib.sha256(data).hexdigest()
def bounds(positions):
    if not positions:return None
    return {'minimum':[min(v[a] for v in positions) for a in range(3)],
            'maximum':[max(v[a] for v in positions) for a in range(3)]}

def parse_bytes(data,limits=None):
    limits=limits or Limits()
    if len(data)>limits.max_bytes:raise MeshError('file exceeds byte limit',0)
    r=Cursor(data)
    mesh_count=r.u32('assembly count')
    if mesh_count>limits.max_assemblies:raise MeshError('assembly count exceeds limit',0)
    if mesh_count==0 and not r.remaining:
        vertex_count=index_count=0;empty_profile='four-byte empty stream'
    else:
        vertex_count=r.u32('vertex buffer count');index_count=r.u32('index buffer count')
        empty_profile='three-count header'
    if vertex_count>limits.max_buffers or index_count>limits.max_buffers:
        raise MeshError('buffer count exceeds limit',4)
    if vertex_count*12+index_count*4+mesh_count*ASSEMBLY_BYTES>r.remaining:
        raise MeshError('minimum table sizes exceed remaining file bytes',r.pos)
    vertex_buffers=[];index_buffers=[];assemblies=[]
    total_vertices=total_indices=0
    for i in range(vertex_count):
        at=r.pos
        unknown=r.u32('vertex header word0');stride=r.u32('vertex stride');count=r.u32('vertex count')
        if stride not in ADMITTED_STRIDES:
            raise MeshError(f'unadmitted vertex stride{stride}',at+4)
        total_vertices+=count
        if total_vertices>limits.max_vertices:raise MeshError('aggregate vertex limit exceeded',at+8)
        begin=r.pos;raw=r.take(stride*count,'vertex buffer')
        positions=[]
        opaque=bytearray()
        for j in range(count):
            position=struct.unpack_from('<fff',raw,j*stride)
            if not all(math.isfinite(v) for v in position):
                raise MeshError(f'nonfinite vertex position buffer{i} vertex{j}',begin+j*stride)
            positions.append(list(position));opaque+=raw[j*stride+12:(j+1)*stride]
        vertex_buffers.append({'index':i,'header_file_offset':at,'header_word0':unknown,
            'stride_bytes':stride,'vertex_count':count,'data_file_offset':begin,'data_bytes':len(raw),
            'data_sha256':sha(raw),'position_offset_in_vertex':0,'position_format':'float32 little-endian xyz',
            'positions':positions,'bounds':bounds(positions),'opaque_vertex_tail_bytes':stride-12,
            'opaque_vertex_tail_hex':opaque.hex()})
    for i in range(index_count):
        at=r.pos;count=r.u32('index count');total_indices+=count
        if total_indices>limits.max_indices:raise MeshError('aggregate index limit exceeded',at)
        if count%3:raise MeshError('index count is not divisible by3 for admitted triangle-list profile',at)
        begin=r.pos;raw=r.take(count*2,'index buffer')
        indices=[x[0] for x in struct.iter_unpack('<H',raw)]
        index_buffers.append({'index':i,'header_file_offset':at,'data_file_offset':begin,
            'index_count':count,'triangle_count':count//3,'index_format':'uint16 little-endian',
            'data_bytes':len(raw),'data_sha256':sha(raw),'indices':indices})
    for i in range(mesh_count):
        at=r.pos;raw=r.take(ASSEMBLY_BYTES,'mesh assembly')
        vb,unknown16,ib=struct.unpack_from('<HHI',raw)
        if vb>=vertex_count or ib>=index_count:
            raise MeshError(f'assembly{i} references absent vertex/index buffer{vb}/{ib}',at)
        indices=index_buffers[ib]['indices'];vertices=vertex_buffers[vb]['vertex_count']
        if any(index>=vertices for index in indices):
            raise MeshError(f'assembly{i} has an index outside its vertex buffer',at)
        unknown_words=list(struct.unpack_from('<11I',raw,8))
        assemblies.append({'index':i,'file_offset':at,'bytes':ASSEMBLY_BYTES,'raw_hex':raw.hex(),
            'vertex_buffer':vb,'index_buffer':ib,'unknown_u16_at2':unknown16,
            'unknown_u32_at8':unknown_words,'referenced_indices_in_range':True,
            'export_policy':'whole referenced buffers; unknown assembly words do not drive draw ranges'})
    if r.remaining:raise MeshError(f'{r.remaining} unparsed trailing bytes',r.pos)
    all_positions=[v for buffer in vertex_buffers for v in buffer['positions']]
    return {'schema_version':1,'tool':'opem-amalur-fab-stream-reader',
        'input_sha256':sha(data),'input_bytes':len(data),'bytes_consumed':r.pos,'complete_consumption':True,
        'format_profile':'original-importer stream layout, checked structurally against this input',
        'reference':{'author':'Lukas Cone','url':SOURCE,'role':'format observations; no source code included'},
        'header':{'file_offset':0,'assembly_count':mesh_count,'vertex_buffer_count':vertex_count,
                  'index_buffer_count':index_count,'empty_profile':empty_profile},
        'summary':{'assemblies':mesh_count,'vertex_buffers':vertex_count,'index_buffers':index_count,
                   'vertices':total_vertices,'indices':total_indices,'triangles_in_buffers':total_indices//3,
                   'exported_triangles':sum(index_buffers[a['index_buffer']]['triangle_count'] for a in assemblies),
                   'bounds':bounds(all_positions),'strides':sorted({b['stride_bytes'] for b in vertex_buffers})},
        'coordinate_policy':'Unchanged native xyz and units; no axis rotation, scaling or winding flip.',
        'vertex_buffers':vertex_buffers,'index_buffers':index_buffers,'assemblies':assemblies,
        'limitations':['Positions, triangle index buffers and assembly buffer references only.',
                       'Unknown assembly words, vertex fields, material slots and original render behavior remain unmodeled.',
                       'Export uses whole referenced index buffers; draw-range semantics in unknown words are not established.',
                       'No bones, weights, skinning, animation, texture bindings or world placement are inferred.',
                       'Structural validity and finite coordinates do not prove complete visual or runtime equivalence.']}

def parse_file(path,limits=None):
    path=Path(path);limits=limits or Limits()
    if path.stat().st_size>limits.max_bytes:raise MeshError('file exceeds byte limit',0)
    result=parse_bytes(path.read_bytes(),limits);result['input_file']=str(path);return result

def export_obj(mesh,path):
    lines=['# Opem Amalur geometry-only extraction; native coordinates unchanged.',
           '# Source SHA256 '+mesh['input_sha256']]
    base=1
    for assembly in mesh['assemblies']:
        vb=mesh['vertex_buffers'][assembly['vertex_buffer']]
        ib=mesh['index_buffers'][assembly['index_buffer']]
        lines.append('o assembly_'+str(assembly['index']))
        lines.extend('v '+' '.join(format(x,'.9g') for x in p) for p in vb['positions'])
        indices=ib['indices']
        for i in range(0,len(indices),3):lines.append('f '+' '.join(str(base+x) for x in indices[i:i+3]))
        base+=len(vb['positions'])
    Path(path).write_text('\n'.join(lines)+'\n',encoding='utf-8')

def export_portable(mesh,path):
    """Authored v1 interchange: magic, submesh count, then counts/xyz/u32 indices.

    Each submesh is independent. Header and every scalar are little-endian.
    Unknown native fields are retained in the accompanying JSON, not this file.
    """
    data=bytearray(MAGIC+struct.pack('<I',len(mesh['assemblies'])))
    for assembly in mesh['assemblies']:
        positions=mesh['vertex_buffers'][assembly['vertex_buffer']]['positions']
        indices=mesh['index_buffers'][assembly['index_buffer']]['indices']
        data+=struct.pack('<II',len(positions),len(indices))
        for p in positions:data+=struct.pack('<fff',*p)
        for index in indices:data+=struct.pack('<I',index)
    Path(path).write_bytes(data)
    return {'file':str(path),'bytes':len(data),'sha256':sha(data),'format':'OMMESH1 authored geometry interchange'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--obj',type=Path);parser.add_argument('--portable',type=Path)
    args=parser.parse_args();result=parse_file(args.input)
    if args.obj:args.obj.parent.mkdir(parents=True,exist_ok=True);export_obj(result,args.obj)
    if args.portable:
        args.portable.parent.mkdir(parents=True,exist_ok=True)
        result['portable_export']=export_portable(result,args.portable)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ['input_file','input_sha256','input_bytes','bytes_consumed','complete_consumption','summary']},indent=2))

if __name__=='__main__':main()
