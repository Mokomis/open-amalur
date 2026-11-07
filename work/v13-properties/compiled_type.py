"""Read the native compiled Type carrier, never the compact SimType stream.

Layout evidence: pinned koa.exe Type::reader 0x1001070, factory 0xfa3d20,
interaction resolver 0xf0c960 and custom-interaction resolver 0xf0d3b0.
This is static layout evidence; it does not establish runtime parity.
"""
from __future__ import annotations

import struct
from amalur_blob import parse_bytes, BlobError

EXE_SHA256 = '16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'


class CompiledTypeError(ValueError):
    pass


def decode_compiled_type(data: bytes, component_names: dict[int, str]):
    """Decode confirmed references; retain all other words without inventing fields.

    On-disk keys are retained before the native a70b80 handle conversion.
    component_names comes from the native factory/RTTI map, not a guessed enum.
    """
    try:
        carrier = parse_bytes(data)
    except BlobError as exc:
        raise CompiledTypeError(
            'Compiled carrier required; compact SimType conversion is unresolved: ' + str(exc)
        ) from exc
    end = 8 + carrier['header']['payload_bytes']
    if end < 8 + 48:
        raise CompiledTypeError('Compiled Type root is shorter than 48 bytes')
    slots = {x['slot_payload_offset'] for x in carrier['slots']}

    def word(at):
        if at < 8 or at > end - 4:
            raise CompiledTypeError('uint32 outside carrier payload')
        return struct.unpack_from('<I', data, at)[0]

    def array(slot, count, stride, cap):
        if count > cap:
            raise CompiledTypeError('Array exceeds admitted count limit')
        ptr = word(slot)
        if count:
            if slot - 8 not in slots:
                raise CompiledTypeError('Nonempty pointer lacks native relocation slot')
            if ptr < 8 or ptr > end or count * stride > end - ptr:
                raise CompiledTypeError('Array exceeds carrier payload')
        return ptr

    dependencies_count = word(8 + 0x18)
    dependencies = array(8 + 0x14, dependencies_count, 4, 100_000)
    count = word(8 + 0x28)
    offsets = array(8 + 0x2c, count, 4, 4096)
    base = array(8 + 0x24, 1 if count else 0, 4, 1)
    parts = []
    for i in range(count):
        relative = word(offsets + i * 4)
        at = base + relative
        kind = word(at)
        if not 0 <= kind <= 42 or kind not in component_names:
            raise CompiledTypeError('Unmapped native component kind')
        part = dict(index=i, kind=kind, native_name=component_names[kind],
                    payload_offset=at - 8,
                    preview_hex=data[at:min(at + 32, end)].hex(),
                    fields_status='opaque except confirmed reference fields')
        if kind == 34:
            n = word(at + 8)
            refs = array(at + 4, n, 4, 100_000)
            part['reference_keys_u32'] = [word(refs + j * 4) for j in range(n)]
            part['fields_status'] = 'native resolver walks pointer+4/count+8; reference roles unconfirmed'
        elif kind == 22:
            part['reference_key_u32'] = word(at + 4)
            part['fields_status'] = 'native resolver converts key+4; reference role unconfirmed'
        parts.append(part)
    return dict(format='native-compiled-Type-carrier', input_sha256=carrier['input_sha256'],
                input_bytes=len(data), native_executable_sha256=EXE_SHA256,
                header_words_u32=[word(8 + i * 4) for i in range(12)],
                parent_key_u32=word(8 + 0x20), script_key_u32=word(8 + 0x10),
                dependency_keys_u32=[word(dependencies + i * 4) for i in range(dependencies_count)],
                components=parts, component_count=count,
                limitations=['Static native layout only; no original-game runtime validation.',
                             'Does not decode or convert compact .simtype_bxml members.',
                             'Script parameters, property names and gameplay behavior remain unresolved.'])
