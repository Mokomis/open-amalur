"""Strict compiled_enums BXML extraction and explicitly selected AENU snapshot.

Raw text/tag/offset provenance is retained. Numeric admission accepts only
canonical signed decimal int32 text, never arbitrary UTF8 or a generic tag.
"""
from __future__ import annotations
import argparse,hashlib,json,platform,re,struct
from pathlib import Path
from amalur_bxml import parse_bytes as parse_bxml,BxmlError

ROOT=657596;CONTAINER=6975411;GROUP=633721;NAME=679773;VALUE=1066594
WEIGHTS=(0x7f,0x32b,0x63d,0x853,0xabd,0x1297,0x1597,0x1741,0x1fb5,0x2543,
 0x2821,0x2a01,0x2b97,0x300d,0x33a1,0x377f,0x3c35,0x4511,0x48e5,0x4a45,
 0x5261,0x5623,0x6217,0x64c9,0x6b41,0x6d99,0x738d,0x7859,0x7f63,0x86a5,
 0x8ce3,0x9287,0x9743,0x9c9d,0xa3ff,0xa939,0xb01b,0xb947,0xc203,0xc64f,
 0xd0cd,0xd8ad,0xdf69,0xe7e9,0xf223,0xfe2f,0x11ecd,0x13019,0x148ff,0x15bb1)

class EnumError(ValueError):pass
def sha(data):return hashlib.sha256(data).hexdigest()
def ascii_hash(name):
    raw=name.encode('ascii')
    if not raw or b'\0' in raw:raise EnumError('snapshot names must be nonempty ASCII without NUL')
    raw=raw.lower()
    return sum(WEIGHTS[i%50]*c+WEIGHTS[c%50]*(i+1) for i,c in enumerate(raw))&0xffffffff
def decimal_int32(raw):
    if not re.fullmatch(rb'(?:0|-[1-9][0-9]*|[1-9][0-9]*)',raw):return None,'not canonical signed decimal text'
    value=int(raw)
    if not -0x80000000<=value<=0x7fffffff:return None,'decimal value outside signed int32'
    return value,None

def extract_bytes(data):
    parsed=parse_bxml(data);nodes=parsed['nodes'];attributes=parsed['attributes'];values=parsed['values']
    if parsed['summary']['root_indices']!=[0] or nodes[0]['children']!=[1]:raise EnumError('expected one root and one container')
    used=set()
    def fields(index,expected):
        node=nodes[index];attrs=attributes[node['attribute_start']:node['attribute_start']+node['attribute_count']]
        keys=[(a['name_symbol_id'],a['type_tag']) for a in attrs]
        if len(keys)!=len(set(keys)) or set(keys)!=set(expected):raise EnumError(f'node{index} has unexpected enum field schema {keys}')
        result={};used.add(index)
        for attr in attrs:
            if attr['value_missing']:raise EnumError('enum field value missing')
            value=values[attr['value_index']];key=(attr['name_symbol_id'],attr['type_tag'])
            if key[1]==0 and value['bytes']!=0:raise EnumError('marker must have exact empty value')
            result[key]={'attribute_index':attr['index'],'attribute_file_offset':attr['file_offset'],
                'packed_hex':attr['packed_hex'],'symbol_id':key[0],'symbol_index':attr['name_symbol_index'],
                'type_tag':key[1],'value_index':attr['value_index'],'value_file_offset':value['file_offset'],
                'raw_hex':value['raw_hex'],'utf8':value['utf8'],'bytes':value['bytes']}
        return result
    def name(field):
        text=field['utf8']
        if not isinstance(text,str) or not text or '\0' in text:raise EnumError('name must be nonempty exact UTF8 without NUL')
        return text
    fields(0,[(ROOT,0)]);fields(1,[(CONTAINER,0)])
    groups=[];seen=set();unsupported=[]
    for gi in nodes[1]['children']:
        attrs=fields(gi,[(GROUP,0),(NAME,96)]);gname=name(attrs[NAME,96])
        if gname in seen:raise EnumError('duplicate exact group name')
        seen.add(gname);members=[];membernames=set()
        for mi in nodes[gi]['children']:
            if nodes[mi]['children']:raise EnumError('enum member has child nodes')
            item=fields(mi,[(VALUE,0),(NAME,96),(VALUE,96)]);mname=name(item[NAME,96])
            if mname in membernames:raise EnumError('duplicate exact member name within group')
            membernames.add(mname);value,error=decimal_int32(bytes.fromhex(item[VALUE,96]['raw_hex']))
            member={'name':mname,'node_index':mi,'node_file_offset':nodes[mi]['file_offset'],
                'name_field':item[NAME,96],'value_field':item[VALUE,96],'value_int32':value,'numeric_error':error}
            if error:unsupported.append({'group':gname,'member':mname,'reason':error})
            members.append(member)
        groups.append({'name':gname,'node_index':gi,'node_file_offset':nodes[gi]['file_offset'],'name_field':attrs[NAME,96],'members':members})
    if len(used)!=len(nodes):raise EnumError('uninterpreted nodes remain outside exact enum profile')
    return {'tool':'opem-amalur-compiled-enum-extractor','schema_version':1,'source_sha256':sha(data),'source_bytes':len(data),
        'complete_structural_consumption':parsed['complete_consumption'],'bxml_summary':parsed['summary'],
        'symbol_roles':{'root':ROOT,'container':CONTAINER,'group':GROUP,'name':NAME,'member_marker_and_value':VALUE},
        'type_profile':{'marker':0,'text':96,'integer_admission':'canonical ASCII signed decimal text within int32; not implied by type tag'},
        'group_count':len(groups),'member_count':sum(len(g['members']) for g in groups),'groups':groups,'unsupported_numeric_fields':unsupported,
        'limitations':['General native type96 coercions are not modeled; numeric grammar is deliberately narrower than arbitrary text.',
            'No archive mount or duplicate-name precedence is inferred. Snapshot selection is explicit.',
            'Native static space_types table corroborates Outdoor0, Interior1, City2, Dungeon3, Jail4, Use Space Type5; other groups require separate native coverage.']}

def flattened(report):return {(g['name'],m['name']):m['value_field']['raw_hex'] for g in report['groups'] for m in g['members']}
def compare(base,other):
    left=flattened(base);right=flattened(other)
    return {'added_in_other':[{'group':g,'member':m,'raw_value_hex':right[g,m]} for g,m in sorted(right.keys()-left.keys())],
        'missing_in_other':[{'group':g,'member':m,'raw_value_hex':left[g,m]} for g,m in sorted(left.keys()-right.keys())],
        'changed_in_other':[{'group':g,'member':m,'base_raw_hex':left[g,m],'other_raw_hex':right[g,m]} for g,m in sorted(left.keys()&right.keys()) if left[g,m]!=right[g,m]],
        'added_groups':sorted({g['name'] for g in other['groups']}-{g['name'] for g in base['groups']}),
        'missing_groups':sorted({g['name'] for g in base['groups']}-{g['name'] for g in other['groups']})}

def snapshot(report):
    if report['unsupported_numeric_fields']:raise EnumError('snapshot contains unsupported numeric fields')
    rows=[];groups={};pairs=set()
    for group in report['groups']:
        gh=ascii_hash(group['name'])
        if gh in groups:raise EnumError('group hash collision or case alias; no implicit merge')
        groups[gh]=group['name']
        for member in group['members']:
            mh=ascii_hash(member['name']);key=(gh,mh)
            if key in pairs:raise EnumError('member hash collision or case alias; no implicit overwrite')
            pairs.add(key);rows.append((gh,mh,member['value_int32']&0xffffffff))
    if len(rows)>65536:raise EnumError('snapshot record budget exceeded')
    rows.sort();data=b'AENU'+struct.pack('<II',1,len(rows))+b''.join(struct.pack('<III',*r) for r in rows)
    return data,{'format':'AENU v1','header_bytes':12,'record_bytes':12,'records':len(rows),'bytes':len(data),
        'sha256':sha(data),'value_encoding':'signed int32 two-complement bits in uint32LE',
        'hash_profile':'native00af08b0 seed0,50weights at01721040, ASCII lowercase, uint32 wrap',
        'hash_weights_sha256':sha(struct.pack('<50I',*WEIGHTS)),'selected_source_sha256':report['source_sha256']}

def main():
    if platform.system()!='Windows':raise SystemExit('Target extraction is restricted to the selected Windows workflow')
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input_dir',type=Path);ap.add_argument('--select',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--snapshot',type=Path);args=ap.parse_args()
    paths=sorted(p for p in args.input_dir.glob('compiled_enums*') if p.is_file())
    selected=args.select.resolve()
    if selected not in {p.resolve() for p in paths}:raise EnumError('selected source is not among explicitly inventoried variants')
    reports=[]
    for path in paths:
        result=extract_bytes(path.read_bytes());result['input_file']=str(path);reports.append(result)
    base=next(r for r in reports if Path(r['input_file']).resolve()==selected)
    args.output.mkdir(parents=True,exist_ok=True)
    for report in reports:(args.output/(Path(report['input_file']).name+'.enums.json')).write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    diff={'selected_source_file':str(selected),'selected_source_sha256':base['source_sha256'],
        'distinct_content_hashes':sorted({r['source_sha256'] for r in reports}),
        'variants':[{'file':r['input_file'],'sha256':r['source_sha256'],'group_count':r['group_count'],'member_count':r['member_count'],
                    'unsupported_numeric_fields':r['unsupported_numeric_fields'],'diff_from_selected':compare(base,r)} for r in reports]}
    if args.snapshot:
        data,receipt=snapshot(base);args.snapshot.parent.mkdir(parents=True,exist_ok=True);args.snapshot.write_bytes(data)
        diff['snapshot']=dict(receipt,path=str(args.snapshot))
    (args.output/'enum-variant-diff.json').write_text(json.dumps(diff,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'selected_sha256':base['source_sha256'],'groups':base['group_count'],'members':base['member_count'],
        'distinct_variants':len(diff['distinct_content_hashes']),'unsupported_values':base['unsupported_numeric_fields'],'snapshot':diff.get('snapshot')},indent=2))

if __name__=='__main__':main()
