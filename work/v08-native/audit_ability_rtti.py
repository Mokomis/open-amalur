"""Windows-only read-only original PE evidence for ability category/init names."""
import hashlib,json,platform,re,struct
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur';target=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
b=target.read_bytes();sha=hashlib.sha256(b).hexdigest();assert sha=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
pe=struct.unpack_from('<I',b,0x3c)[0];count=struct.unpack_from('<H',b,pe+6)[0];opt=struct.unpack_from('<H',b,pe+20)[0];base=struct.unpack_from('<I',b,pe+52)[0];sections=[]
for index in range(count):
    p=pe+24+opt+index*40;vs,rva,size,offset=struct.unpack_from('<IIII',b,p+8);flags=struct.unpack_from('<I',b,p+36)[0];sections.append((base+rva,size,offset,bool(flags&0x20000000)))
def va(offset):
    for start,size,file_offset,execute in sections:
        if file_offset<=offset<file_offset+size:return start+offset-file_offset
def raw(address,length):
    for start,size,offset,execute in sections:
        if start<=address and address+length<=start+size:return b[offset+address-start:offset+address-start+length]
    raise ValueError(hex(address))
def executable(address):return any(execute and start<=address<start+size for start,size,offset,execute in sections)
def refs(value):
    needle=struct.pack('<I',value);position=b.find(needle);found=[]
    while position>=0 and len(found)<100:
        address=va(position)
        if address is not None:found.append(address)
        position=b.find(needle,position+1)
    return found
rows=[]
for match in re.finditer(rb'\.\?A[UV][ -~]{1,180}?\x00',b):
    name=match.group()[:-1].decode('ascii')
    if not (re.search(r'AssetCategoryMgrProxy.*@V(?:Player)?Ability@',name) or re.search(r'(?:Player)?AbilityMgr@',name)):continue
    address=va(match.start())
    if address is None:continue
    descriptor=address-8;tables=[]
    for reference in refs(descriptor):
        locator=reference-12
        if locator%4:continue
        try:fields=struct.unpack('<5I',raw(locator,20))
        except ValueError:continue
        if fields[0] or fields[1]>4096:continue
        for pointer in refs(locator):
            if pointer%4:continue
            vtable=pointer+4
            try:slots=struct.unpack('<52I',raw(vtable,208))
            except ValueError:continue
            tables.append({'locator':hex(locator),'object_offset':fields[1],'vtable':hex(vtable),
                           'slots':[hex(value) for value in slots],
                           'basename_getter_candidate':hex(slots[18]),'hash_policy_reader_candidate':hex(slots[51]),
                           'basename_getter_is_executable':executable(slots[18]),'hash_reader_is_executable':executable(slots[51])})
    rows.append({'rtti_name':name,'type_descriptor':hex(descriptor),'vtables':tables})
names=[]
for literal in [b'ability',b'player_ability',b'playerability',b'Might_SkillfulDefense']:
    needle=literal+b'\0';position=b.find(needle)
    while position>=0:
        address=va(position)
        if address is not None and (position==0 or b[position-1]==0):names.append({'literal':literal.decode(),'address':hex(address),'pointer_references':[hex(value) for value in refs(address)]})
        position=b.find(needle,position+1)
report={'target_sha256':sha,'scope':'Original PE bytes only; RTTI chain and vtable candidates. No target execution. Slot18/51 meaning uses prior generic loader evidence and requires focused getter confirmation.',
        'rtti':rows,'exact_nul_terminated_strings':names}
out=root/'outputs/scene-v08/audit';out.mkdir(parents=True,exist_ok=True);(out/'ability-rtti.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
