"""Windows-only bounded static RTTI/vtable/getter audit; never executes koa.exe."""
import hashlib
import json
import platform
import re
import struct
import sys
from pathlib import Path

assert platform.system() == 'Windows', 'Run on the authorized Windows analysis machine'
root = Path.home() / 'Documents/Opem Amalur'
sys.path.insert(0, str(root / 'tools/python-libs'))
import capstone

target = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
data = target.read_bytes()
digest = hashlib.sha256(data).hexdigest()
assert digest == '16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
pe = struct.unpack_from('<I', data, 0x3c)[0]
assert data[pe:pe+4] == b'PE\0\0'
count, opt = struct.unpack_from('<H', data, pe+6)[0], struct.unpack_from('<H', data, pe+20)[0]
base = struct.unpack_from('<I', data, pe+52)[0]
sections = []
for index in range(count):
    pos = pe + 24 + opt + index*40
    _, rva, size, offset = struct.unpack_from('<IIII', data, pos+8)
    flags = struct.unpack_from('<I', data, pos+36)[0]
    sections.append((base+rva, size, offset, bool(flags & 0x20000000)))

def address(offset):
    for start, size, file_offset, _ in sections:
        if file_offset <= offset < file_offset+size:
            return start+offset-file_offset

def raw(addr, size):
    for start, length, offset, _ in sections:
        if start <= addr and addr+size <= start+length:
            return data[offset+addr-start:offset+addr-start+size]
    raise ValueError(hex(addr))

def words(addr, count):
    return struct.unpack('<'+'I'*count, raw(addr, count*4))

def executable(addr):
    return any(execute and start <= addr < start+size for start, size, _, execute in sections)

reference_cache = {}
def refs(value):
    if value in reference_cache:
        return reference_cache[value]
    needle, found, pos = struct.pack('<I', value), [], 0
    while True:
        pos = data.find(needle, pos)
        if pos < 0:
            break
        va = address(pos)
        if va is not None and va % 4 == 0:
            found.append(va)
            if len(found) > 128:
                raise ValueError('More than 128 aligned references: '+hex(value))
        pos += 1
    reference_cache[value] = found
    return found

names = {}
for match in re.finditer(rb'\.\?A[UV][ -~]{1,400}?\x00', data):
    va = address(match.start())
    if va is not None:
        names[va-8] = match.group()[:-1].decode('ascii')

def category(name):
    match = re.search(r'AssetCategoryMgrProxy@\$0([A-P]+|[0-9])@', name)
    if not match:
        return None
    token = match.group(1)
    if token.isdigit():
        return int(token)+1
    value = 0
    for ch in token:
        value = value*16 + ord(ch)-ord('A')
    return value

decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
decoder.detail = True
def getter(addr):
    result = {'address':hex(addr), 'instructions':[], 'pushed_ascii_literals':[], 'calls':[]}
    if not executable(addr):
        result['status'] = 'not executable'
        return result
    try:
        code = raw(addr, 128)
    except ValueError:
        result['status'] = 'not fully file-backed'
        return result
    ended, straight = False, True
    for ins in decoder.disasm(code, addr):
        result['instructions'].append({'address':hex(ins.address), 'bytes':ins.bytes.hex(), 'mnemonic':ins.mnemonic, 'operands':ins.op_str})
        if ins.mnemonic == 'push' and len(ins.operands) == 1 and ins.operands[0].type == capstone.x86.X86_OP_IMM:
            ptr = ins.operands[0].imm & 0xffffffff
            try:
                literal = raw(ptr, 96).split(b'\0', 1)[0]
                if re.fullmatch(rb'[A-Z][A-Z0-9_]{0,63}', literal):
                    result['pushed_ascii_literals'].append({'address':hex(ptr), 'literal':literal.decode()})
            except ValueError:
                pass
        if ins.mnemonic == 'call':
            result['calls'].append(ins.op_str)
        if ins.mnemonic.startswith('j') or ins.mnemonic.startswith('loop'):
            straight = False
            break
        if ins.mnemonic.startswith('ret'):
            ended = True
            break
        if ins.mnemonic in ('int3', 'ud2'):
            break
    # Only classify the already REA-confirmed simple wrapper shape. Preserve all bytes
    # for review; other forms stay unresolved instead of guessed.
    literals = result['pushed_ascii_literals']
    if ended and straight and result['calls'] == ['0xaf4d70'] and len(literals) == 1:
        result['status'] = 'single straight-line af4d70 wrapper with one uppercase literal'
        result['basename_literal'] = literals[0]['literal']
    else:
        result['status'] = 'requires focused native review'
    return result

rows = []
for td, name in sorted(names.items()):
    if not re.fullmatch(r'\.\?AV[A-Za-z0-9_]*Mgr@BHG@@', name):
        continue
    tables = []
    for reference in refs(td):
        locator = reference-12
        try:
            signature, offset, cd_offset, owner, hierarchy = words(locator, 5)
            if signature != 0 or owner != td or offset > 4096 or cd_offset > 4096:
                continue
            hs, attributes, base_count, base_array = words(hierarchy, 4)
            if hs != 0 or not 1 <= base_count <= 128:
                continue
            inherited = []
            for descriptor in words(base_array, base_count):
                base_td = words(descriptor, 1)[0]
                base_name = names.get(base_td, '')
                cat = category(base_name)
                if cat is not None:
                    inherited.append({'type_descriptor':hex(base_td), 'name':base_name, 'category':cat})
            if not inherited:
                continue
            for pointer in refs(locator):
                vtable = pointer+4
                slots = words(vtable, 52)
                if not executable(slots[0]):
                    continue
                tables.append({'locator':hex(locator), 'object_offset':offset, 'hierarchy':hex(hierarchy), 'asset_category_bases':inherited,
                               'vtable':hex(vtable), 'slots':[hex(x) for x in slots], 'basename_getter':getter(slots[18])})
        except ValueError:
            continue
    if tables:
        rows.append({'name':name, 'type_descriptor':hex(td), 'vtables':tables})
    assert len(rows) <= 512, 'Unexpectedly broad manager result'

report = {'target_sha256':digest, 'scope':'Original PE bytes only, no execution. MSVC RTTI inheritance links concrete manager to template category. Slot18 meaning comes from REA a732d0. Getter classifier is restricted to straight-line af4d70 wrappers; unresolved getters require REA.', 'managers':rows}
out = root / 'outputs/scene-v08/audit'
out.mkdir(parents=True, exist_ok=True)
(out/'asset-manager-basenames.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
for row in rows:
    for table in row['vtables']:
        print(json.dumps({'manager':row['name'], 'vtable':table['vtable'], 'categories':[x['category'] for x in table['asset_category_bases']], 'getter':table['basename_getter']['address'], 'basename':table['basename_getter'].get('basename_literal'), 'status':table['basename_getter']['status']}))
