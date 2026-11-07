"""Index the compiled batch actually consumed by koa.exe's Type loader.

Native evidence: a969b0 reads u32 count and count*8 directory bytes;
a996f0 advances the data cursor by each member length and creates 24-byte
IOBundleStreamingRequestProxy objects. This is distinct from compact sources.
"""
from dataclasses import dataclass
import hashlib
import struct


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class CatalogLimits:
    max_bytes: int = 64 * 1024 * 1024
    max_members: int = 32768
    max_member_bytes: int = 4 * 1024 * 1024


def index_batch(data: bytes, limits: CatalogLimits | None = None):
    limits = limits or CatalogLimits()
    if len(data) > limits.max_bytes or len(data) < 4:
        raise CatalogError('Batch length outside admitted bounds')
    count = struct.unpack_from('<I', data)[0]
    if not 1 <= count <= limits.max_members or count > (len(data) - 4) // 8:
        raise CatalogError('Batch directory count outside admitted bounds')
    cursor = 4 + count * 8
    members = {}
    for i in range(count):
        key, size = struct.unpack_from('<II', data, 4 + i * 8)
        if key in members:
            raise CatalogError('Duplicate batch resource identifier')
        if size < 8 or size > limits.max_member_bytes or size > len(data) - cursor:
            raise CatalogError('Member length outside admitted bounds')
        members[key] = dict(resource_id=key, index=i, offset=cursor, bytes=size)
        cursor += size
    if cursor != len(data):
        raise CatalogError('Member lengths do not consume the batch exactly')
    return dict(format='native-compiled-Type-batch', input_bytes=len(data),
                input_sha256=hashlib.sha256(data).hexdigest(), count=count,
                directory_bytes=4 + count * 8, members=members)


def member_bytes(data: bytes, member):
    offset, size = member['offset'], member['bytes']
    if offset < 4 or size < 8 or offset > len(data) or size > len(data) - offset:
        raise CatalogError('Member span outside input')
    return data[offset:offset + size]


def decode_type(data: bytes, component_names):
    """Add native-confirmed property copies without guessing gameplay names."""
    from compiled_type import decode_compiled_type, CompiledTypeError
    result = decode_compiled_type(data, component_names)
    result['type_flags_u32'] = result['header_words_u32'][7]
    result['native_inheritance_guard_set'] = bool(result['type_flags_u32'] & 0x10)
    payload_end = 8 + struct.unpack_from('<I', data)[0]
    for part in result['components']:
        if part['kind'] != 34:
            continue
        start = 8 + part['payload_offset']
        if start + 0x29 > payload_end:
            raise CompiledTypeError('Interaction blueprint properties exceed payload')
        # f746a0 initializes PartInteraction from its blueprint. f74700 copies
        # the same native instance fields. Numeric gameplay roles are unproven.
        mappings = [(0x0c, 0x24, 12), (0x18, 0x30, 4), (0x1c, 0x34, 4),
                    (0x20, 0x38, 4), (0x24, 0x3c, 4), (0x28, 0x40, 1)]
        part['native_property_copies'] = [
            dict(blueprint_offset=source, native_instance_offset=target,
                 bytes=size, raw_hex=data[start + source:start + source + size].hex())
            for source, target, size in mappings
        ]
        part['property_evidence'] = dict(function='0xf746a0', copy_function='0xf74700',
                                        status='Native byte-copy layout confirmed; gameplay field names unassigned')
    return result
