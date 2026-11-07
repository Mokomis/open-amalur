"""Bounded Windows-only diagnostic views of unsupported batch wrappers."""
import hashlib
import json
import platform
import struct
from pathlib import Path

assert platform.system() == 'Windows'
root = Path.home() / 'Documents' / 'Opem Amalur'
out = root / 'outputs' / 'remaining-v05'
out.mkdir(exist_ok=True)
inventory = json.loads((root / 'outputs/initial-corpus-v04/inventory.json').read_text())
names = [r['file'] for r in inventory['records'] if 'parse_error' in r]
assert len(names) == 12
records = []
for name in names:
    path = root / 'work/initial-script-corpus-v04' / name
    with path.open('rb') as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    assert len(raw) <= 16 * 1024 * 1024
    def view(start, length):
        block = raw[start:start+length]
        return {'offset': start, 'bytes': len(block), 'hex': block.hex(),
                'ascii': ''.join(chr(b) if 32 <= b < 127 else '.' for b in block)}
    magic = []
    cursor = 0
    while True:
        at = raw.find(b'\x1bLua', cursor)
        if at < 0:break
        magic.append(at);cursor=at+4
        assert len(magic) <= 10000
    first = struct.unpack_from('<I',raw)[0]
    words = [struct.unpack_from('<I',raw,i)[0] for i in range(0,min(len(raw)-3,128),4)]
    records.append({'file':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                    'first_u32_le':first,'first_32_words_le':words,'head':view(0,512),
                    'first_field_end':view(max(0,first-32),128) if first < len(raw) else None,
                    'lua_magic_count':len(magic),'lua_magic_offsets':magic,
                    'chunk_prefixes':[view(max(0,p-96),128) for p in magic[:64]],
                    'tail':view(max(0,len(raw)-128),128)})
(out/'batch-wrapper-probe.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print(json.dumps([{k:r[k] for k in ('file','bytes','sha256','first_u32_le','lua_magic_count','lua_magic_offsets')} for r in records],indent=2))
