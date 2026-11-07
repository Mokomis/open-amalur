"""Windows-only bounded binding namespace discovery from original PE bytes."""
import argparse,hashlib,json,platform,re,struct
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur'
parser=argparse.ArgumentParser()
parser.add_argument('--namespace',required=True)
parser.add_argument('--method',action='append',default=[])
parser.add_argument('--rtti',required=True)
parser.add_argument('--label',required=True)
args=parser.parse_args()
assert re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}',args.namespace)
assert 1<=len(args.method)<=8 and all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}',name) for name in args.method)
assert re.fullmatch(r'[A-Za-z0-9_]{1,64}',args.rtti)
assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',args.label)
b=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe').read_bytes()
sha=hashlib.sha256(b).hexdigest()
assert sha=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
pe=struct.unpack_from('<I',b,0x3c)[0];assert b[pe:pe+4]==b'PE\0\0'
base=struct.unpack_from('<I',b,pe+52)[0];opt=struct.unpack_from('<H',b,pe+20)[0];sections=[]
for index in range(struct.unpack_from('<H',b,pe+6)[0]):
    p=pe+24+opt+index*40;_,rva,size,offset=struct.unpack_from('<IIII',b,p+8)
    sections.append((base+rva,size,offset,bool(struct.unpack_from('<I',b,p+36)[0]&0x20000000)))
def va(offset):
    for start,size,off,_ in sections:
        if off<=offset<off+size:return start+offset-off
def raw(addr,length):
    for start,size,off,_ in sections:
        if start<=addr and addr+length<=start+size:return b[off+addr-start:off+addr-start+length]
    raise ValueError(hex(addr))
def exe(addr):return any(flag and start<=addr<start+size for start,size,_,flag in sections)
def refs(value):
    needle=struct.pack('<I',value);pos=0;found=[]
    while True:
        pos=b.find(needle,pos)
        if pos<0:break
        addr=va(pos)
        if addr is not None:
            row={'address':hex(addr),'executable_section':exe(addr)}
            try:row['window_address']=hex(addr-16);row['window_hex']=raw(addr-16,64).hex()
            except ValueError:pass
            found.append(row)
            if len(found)>64:raise ValueError('More than64 references for '+hex(value))
        pos+=1
    return found
strings=[]
for literal in [args.namespace.encode('ascii')]+[name.encode('ascii') for name in args.method]:
    position=0;occurrences=0
    while True:
        position=b.find(literal+b'\0',position)
        if position<0:break
        addr=va(position)
        if addr is not None:
            strings.append({'literal':literal.decode(),'address':hex(addr),'references':refs(addr)})
            occurrences+=1;assert occurrences<=16
        position+=1
rtti=[]
for match in re.finditer(rb'\.\?A[UV][ -~]{1,400}?\0',b):
    name=match.group()[:-1].decode('ascii')
    if args.rtti.lower() not in name.lower():continue
    addr=va(match.start())
    if addr is None:continue
    td=addr-8;tables=[]
    for ref in refs(td):
        locator=int(ref['address'],0)-12
        if locator%4:continue
        try:
            fields=struct.unpack('<5I',raw(locator,20))
            if fields[0] or fields[1]>4096 or fields[3]!=td:continue
            for ptr in refs(locator):
                pointer=int(ptr['address'],0)
                if pointer%4:continue
                table=pointer+4;slots=struct.unpack('<6I',raw(table,24))
                if not exe(slots[0]):continue
                tables.append({'locator':hex(locator),'object_offset':fields[1],'vtable':hex(table),'first_six_slots':[hex(x) for x in slots]})
        except ValueError:continue
    rtti.append({'name':name,'type_descriptor':hex(td),'vtables':tables})
    assert len(rtti)<=64
report={'target_sha256':sha,'scope':'Read-only bounded original PE literal/reference/RTTI discovery. Raw pointer hits and vtables are candidates requiring native xref/owner confirmation. No service behavior inferred.','namespace':args.namespace,'rtti_filter':args.rtti,'strings':strings,'owner_rtti':rtti}
out=root/'outputs/scene-v08/audit';out.mkdir(parents=True,exist_ok=True)
(out/(args.label+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
