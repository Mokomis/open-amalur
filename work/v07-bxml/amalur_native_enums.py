"""Bounded read-only export of the selected executable's97 static enum groups."""
from __future__ import annotations
import argparse,json,platform,struct
from pathlib import Path
from amalur_enums import EnumError,extract_bytes,sha,snapshot

TARGET_SHA256='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
TABLE_START=0x1770cb8;GROUP_COUNT=97

def extract_native(data):
    if sha(data)!=TARGET_SHA256:raise EnumError('native enum table profile requires the verified executable SHA256')
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if data[:2]!=b'MZ' or data[pe:pe+4]!=b'PE\0\0':raise EnumError('target is not PE')
    count=struct.unpack_from('<H',data,pe+6)[0];size=struct.unpack_from('<H',data,pe+20)[0];optional=pe+24
    if struct.unpack_from('<H',data,optional)[0]!=0x10b or not 1<=count<=96:raise EnumError('unexpected PE32 profile')
    base=struct.unpack_from('<I',data,optional+28)[0];sections=[]
    for i in range(count):
        at=optional+size+40*i;virtual_size,rva,rawsize,raw=struct.unpack_from('<4I',data,at+8)
        if raw+rawsize>len(data):raise EnumError('PE section exceeds source file')
        sections.append((base+rva,base+rva+rawsize,raw))
    def span(address,length):
        matches=[raw+address-start for start,end,raw in sections if start<=address and length<=end-address]
        if len(matches)!=1:raise EnumError('native enum span lacks unique file-backed PE mapping')
        offset=matches[0];return offset,data[offset:offset+length]
    def name(address):
        result=bytearray();offset,_=span(address,1)
        for i in range(512):
            _,raw=span(address+i,1);value=raw[0]
            if value==0:
                if not result:raise EnumError('empty native enum name')
                return result.decode('ascii'),{'address':hex(address),'file_offset':offset,'raw_hex_with_nul':(result+b'\0').hex()}
            if not 32<=value<127:raise EnumError('native enum name outside printable ASCII profile')
            result.append(value)
        raise EnumError('native enum name exceeds bounded profile')
    groups=[];seen=set();total=0
    for index in range(GROUP_COUNT):
        address=TABLE_START+index*12;offset,raw=span(address,12);name_pointer,count,members_pointer=struct.unpack('<III',raw)
        if not 1<=count<=1000:raise EnumError('native group count outside admitted profile')
        group_name,source=name(name_pointer)
        if group_name in seen:raise EnumError('duplicate native group name')
        seen.add(group_name);members=[];membernames=set()
        for i in range(count):
            at=members_pointer+i*8;member_offset,member_raw=span(at,8);pointer,value=struct.unpack('<Ii',member_raw)
            member_name,field=name(pointer)
            if member_name in membernames:raise EnumError('duplicate native member name')
            membernames.add(member_name);members.append({'name':member_name,'value_int32':value,
                'native_record':{'address':hex(at),'file_offset':member_offset,'raw_hex':member_raw.hex()},'name_field':field})
        total+=count
        groups.append({'name':group_name,'name_field':source,'members':members,
            'native_descriptor':{'index':index,'address':hex(address),'file_offset':offset,'raw_hex':raw.hex(),'member_count':count,'member_table_address':hex(members_pointer)}})
    return {'tool':'opem-amalur-native-enum-extractor','schema_version':1,'source_sha256':sha(data),'source_bytes':len(data),
        'table_start':hex(TABLE_START),'table_end':hex(TABLE_START+GROUP_COUNT*12),'group_count':len(groups),'member_count':total,
        'groups':groups,'unsupported_numeric_fields':[],
        'limitations':['Static executable data only; registration coverage must be corroborated by its native caller.',
            'No BXML values are merged into the selected native descriptor table.',
            'Names and signed int32 values are read directly from mapped source bytes; export hash lookup remains ASCII only.']}

def compare_to_bxml(native,bxml):
    left={(g['name'],m['name']):m['value_int32'] for g in native['groups'] for m in g['members']}
    right={(g['name'],m['name']):m['value_int32'] for g in bxml['groups'] for m in g['members']}
    return {'native_only':[{'group':g,'member':m,'native_value':left[g,m]} for g,m in sorted(left.keys()-right.keys())],
        'bxml_only':[{'group':g,'member':m,'bxml_value':right[g,m]} for g,m in sorted(right.keys()-left.keys())],
        'different_values':[{'group':g,'member':m,'native_value':left[g,m],'bxml_value':right[g,m]} for g,m in sorted(left.keys()&right.keys()) if left[g,m]!=right[g,m]],
        'equal_values':sum(left[k]==right[k] for k in left.keys()&right.keys()),
        'native_only_groups':sorted({g['name'] for g in native['groups']}-{g['name'] for g in bxml['groups']}),
        'bxml_only_groups':sorted({g['name'] for g in bxml['groups']}-{g['name'] for g in native['groups']})}

def main():
    if platform.system()!='Windows':raise SystemExit('Native extraction runs on the selected Windows host only')
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('executable',type=Path)
    ap.add_argument('--bxml-dir',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--snapshot',type=Path)
    args=ap.parse_args();report=extract_native(args.executable.read_bytes());report['input_file']=str(args.executable)
    report['bxml_comparisons']=[]
    for path in sorted(args.bxml_dir.glob('compiled_enums*')):
        if not path.is_file():continue
        other=extract_bytes(path.read_bytes());comparison=compare_to_bxml(report,other)
        report['bxml_comparisons'].append({'file':str(path),'source_sha256':other['source_sha256'],'diff':comparison})
    if args.snapshot:
        data,receipt=snapshot(report);args.snapshot.parent.mkdir(parents=True,exist_ok=True);args.snapshot.write_bytes(data)
        report['snapshot']=dict(receipt,path=str(args.snapshot),source_kind='original executable static descriptor table')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'groups':report['group_count'],'members':report['member_count'],'source_sha256':report['source_sha256'],
        'comparisons':[{'file':r['file'],'equal_values':r['diff']['equal_values'],'native_only':len(r['diff']['native_only']),
                        'bxml_only':len(r['diff']['bxml_only']),'different_values':len(r['diff']['different_values'])} for r in report['bxml_comparisons']],
        'snapshot':report.get('snapshot')},indent=2))

if __name__=='__main__':main()
