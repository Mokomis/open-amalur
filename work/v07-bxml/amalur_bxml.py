"""Read Amalur's observed BXML table carrier without guessing value semantics.

This implementation preserves raw data, validates the graph iteratively, and
never writes game files. The table-layout hypothesis is independently encoded
from format observations in the external converter listed in SOURCE_REFERENCE.
Real-file validation is recorded separately; parsing is not engine execution.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path

SOURCE_REFERENCE = {
    'repository': 'https://github.com/ZucchiniZap/AmalurBxmlConverter',
    'commit': '3c2829fb4d8e88830e77bd8aede5e2d128bc259e',
    'file': 'BxmlEngine.cs',
    'role': 'External table-layout hypothesis, not native behavior evidence',
}

class BxmlError(ValueError):
    def __init__(self, message: str, offset: int | None = None):
        self.offset = offset
        super().__init__(message + (f' at file offset 0x{offset:x}' if offset is not None else ''))

@dataclass(frozen=True)
class Limits:
    max_file_bytes: int = 128 * 1024 * 1024
    max_nodes: int = 500_000
    max_attributes: int = 2_000_000
    max_symbols: int = 1_000_000
    max_values: int = 1_000_000
    max_value_bytes: int = 32 * 1024 * 1024

class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
    @property
    def remaining(self): return len(self.data) - self.pos
    def take(self, length: int, label: str):
        if length < 0 or length > self.remaining:
            raise BxmlError(f'truncated or invalid {label} length {length}', self.pos)
        start = self.pos
        self.pos += length
        return self.data[start:self.pos]
    def u32(self, label: str): return struct.unpack('<I', self.take(4, label))[0]
    def count(self, label: str, maximum: int, width: int):
        offset = self.pos
        number = self.u32(label)
        if number > maximum or number > self.remaining // width:
            raise BxmlError(f'{label} {number} exceeds configured or remaining-byte bounds', offset)
        return number

def raw_value(data: bytes):
    try:
        text = data.decode('utf-8', errors='strict')
    except UnicodeDecodeError:
        text = None
    return {'bytes': len(data), 'raw_hex': data.hex(), 'utf8': text}

def load_symbols(paths: list[Path]):
    """Return exact uint32→all declared names, retaining conflicting declarations."""
    names: dict[int, set[str]] = {}
    sources = []
    declarations = []
    for path in sorted(set(paths)):
        data = path.read_bytes()
        text = data.decode('utf-8-sig', errors='strict')
        accepted = 0
        for row_number, row in enumerate(csv.reader(text.splitlines()), 1):
            if not row or not any(row): continue
            if row_number == 1 and row[0].strip().lower() in {'id', 'symbolid', 'symbol_id'}: continue
            if len(row) < 2:
                raise BxmlError(f'symbol CSV {path} row {row_number} has fewer than2 fields')
            try:
                key = int(row[0].strip(), 10)
            except ValueError as exc:
                raise BxmlError(f'symbol CSV {path} row {row_number} invalid decimal ID') from exc
            if not 0 <= key <= 0xffffffff:
                raise BxmlError(f'symbol CSV {path} row {row_number} ID outside uint32')
            # Unquoted commas occur in the reference's format; do not silently drop them.
            name = ','.join(row[1:])
            names.setdefault(key, set()).add(name)
            declarations.append({'id': key, 'name': name, 'source': str(path), 'row': row_number})
            accepted += 1
        sources.append({'file': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'declarations': accepted})
    return {key: sorted(values) for key, values in names.items()}, {
        'sources': sources, 'ids': len(names), 'declarations': len(declarations),
        'conflicts': [{'id': key, 'names': sorted(values)} for key, values in sorted(names.items()) if len(values) > 1],
    }

def validate_graph(nodes, attributes):
    n, a = len(nodes), len(attributes)
    attribute_owners = [-1] * a
    child_owners = [-1] * n
    roots = []
    for node in nodes:
        i = node['index']
        for field in ('parent', 'first_child', 'next_sibling'):
            value = node[field]
            if value != -1 and not 0 <= value < n:
                raise BxmlError(f'node {i} {field} index {value} is invalid', node['file_offset'])
            if value == i:
                raise BxmlError(f'node {i} self-reference in {field}', node['file_offset'])
        start, count = node['attribute_start'], node['attribute_count']
        if start < 0 or count < 0 or start > a or count > a - start:
            raise BxmlError(f'node {i} attribute range is invalid', node['file_offset'] + 12)
        for index in range(start, start + count):
            if attribute_owners[index] != -1:
                raise BxmlError(f'attribute {index} belongs to multiple nodes', attributes[index]['file_offset'])
            attribute_owners[index] = i
        if node['parent'] == -1: roots.append(i)
        if node['next_sibling'] != -1 and nodes[node['next_sibling']]['parent'] != node['parent']:
            raise BxmlError(f'node {i} sibling has a different parent', node['file_offset'] + 8)
    for owner in nodes:
        current = owner['first_child']
        local_seen = set()
        children = []
        while current != -1:
            if current in local_seen:
                raise BxmlError(f'child sibling cycle under node {owner["index"]}', owner['file_offset'])
            local_seen.add(current)
            child = nodes[current]
            if child['parent'] != owner['index']:
                raise BxmlError(f'node {current} parent disagrees with child chain', child['file_offset'])
            if child_owners[current] != -1:
                raise BxmlError(f'node {current} occurs in multiple child chains', child['file_offset'])
            child_owners[current] = owner['index']
            children.append(current)
            current = child['next_sibling']
        owner['children'] = children
    for i, owner in enumerate(child_owners):
        if nodes[i]['parent'] != -1 and owner == -1:
            raise BxmlError(f'node {i} is absent from its parent child chain', nodes[i]['file_offset'])
    if any(x == -1 for x in attribute_owners):
        raise BxmlError('unowned attributes outside node ranges')
    # A child/parent cycle can satisfy local ownership checks; reachability from
    # roots rejects it without recursion or a depth-dependent Python failure.
    reached = set()
    pending = roots.copy()
    maximum_depth = 0
    for i in roots: nodes[i]['depth'] = 0
    while pending:
        current = pending.pop()
        if current in reached: raise BxmlError('node appears more than once in rooted traversal')
        reached.add(current)
        depth = nodes[current]['depth']
        maximum_depth = max(maximum_depth, depth)
        for child in nodes[current]['children']:
            nodes[child]['depth'] = depth + 1
            pending.append(child)
    if len(reached) != n: raise BxmlError('node graph contains a parent cycle or unreachable component')
    # Top-level siblings are permitted as a forest but must remain acyclic.
    finished = set()
    for root in roots:
        current = root
        chain = set()
        while current != -1 and current not in finished:
            if current in chain: raise BxmlError('root sibling cycle')
            chain.add(current)
            current = nodes[current]['next_sibling']
        finished.update(chain)
    for index, owner in enumerate(attribute_owners): attributes[index]['owner_node'] = owner
    return {'root_indices': roots, 'root_count': len(roots), 'maximum_depth': maximum_depth,
            'all_nodes_reachable': True, 'all_attributes_owned_once': True}

def parse_bytes(data: bytes, symbols: dict[int, list[str]] | None = None, limits: Limits | None = None):
    limits = limits or Limits()
    symbols = symbols or {}
    if len(data) > limits.max_file_bytes: raise BxmlError('file exceeds configured byte limit', 0)
    r = Reader(data)
    sections = []
    start = r.pos
    node_count = r.count('node count', limits.max_nodes, 20)
    nodes = []
    for i in range(node_count):
        offset = r.pos
        parent, child, sibling, count, first = struct.unpack('<iiiii', r.take(20, 'node'))
        nodes.append({'index': i, 'file_offset': offset, 'parent': parent, 'first_child': child,
                      'next_sibling': sibling, 'attribute_count': count, 'attribute_start': first})
    sections.append({'kind': 'nodes', 'file_offset': start, 'bytes': r.pos-start, 'count': node_count})
    start = r.pos
    attribute_count = r.count('attribute count', limits.max_attributes, 4)
    attributes = []
    for i in range(attribute_count):
        offset = r.pos
        packed = r.u32('attribute word')
        attributes.append({'index': i, 'file_offset': offset, 'packed_hex': f'{packed:08x}',
                           'name_symbol_index': packed & 0xfff, 'value_index': (packed >> 12) & 0xfff,
                           'type_tag': packed >> 24})
    sections.append({'kind': 'attributes', 'file_offset': start, 'bytes': r.pos-start, 'count': attribute_count})
    start = r.pos
    symbol_count = r.count('local symbol count', limits.max_symbols, 4)
    local_symbols = []
    for i in range(symbol_count):
        offset = r.pos
        value = r.u32('local symbol ID')
        declared_names = symbols.get(value, [])
        local_symbols.append({'index': i, 'file_offset': offset, 'id': value, 'id_hex': f'{value:08x}',
                              'names': declared_names, 'name': declared_names[0] if len(declared_names)==1 else None})
    sections.append({'kind': 'local_symbols', 'file_offset': start, 'bytes': r.pos-start, 'count': symbol_count})
    start = r.pos
    value_count = r.count('value count', limits.max_values, 4)
    values = []
    for i in range(value_count):
        offset = r.pos
        length = r.u32('value byte count')
        if length > limits.max_value_bytes: raise BxmlError('value exceeds configured byte limit', offset)
        payload_offset = r.pos
        payload = r.take(length, 'value')
        values.append({'index': i, 'length_file_offset': offset, 'file_offset': payload_offset, **raw_value(payload)})
    sections.append({'kind': 'values', 'file_offset': start, 'bytes': r.pos-start, 'count': value_count})
    trailer = {'file_offset': r.pos, 'bytes': r.remaining, 'raw_hex': r.data[r.pos:].hex()}
    if r.remaining == 4 and r.data[r.pos:] == b'\0'*4:
        r.take(4, 'zero trailer'); trailer['profile'] = 'one zero uint32'
    elif not r.remaining: trailer['profile'] = 'no trailer'
    else: raise BxmlError(f'unrecognized trailing section ({r.remaining} bytes)', r.pos)
    for attribute in attributes:
        name, value = attribute['name_symbol_index'], attribute['value_index']
        if name != 0xfff and name >= len(local_symbols):
            raise BxmlError(f'attribute {attribute["index"]} symbol index out of range', attribute['file_offset'])
        if value != 0xfff and value >= len(values):
            raise BxmlError(f'attribute {attribute["index"]} value index out of range', attribute['file_offset'])
        attribute['name_symbol_id'] = None if name == 0xfff else local_symbols[name]['id']
        attribute['name'] = None if name == 0xfff else local_symbols[name]['name']
        attribute['name_candidates'] = [] if name == 0xfff else local_symbols[name]['names']
        attribute['value_missing'] = value == 0xfff
    graph = validate_graph(nodes, attributes)
    return {'schema_version': 1, 'tool': 'opem-amalur-bxml-reader',
            'input_sha256': hashlib.sha256(data).hexdigest(), 'input_bytes': len(data),
            'bytes_consumed': r.pos, 'complete_consumption': r.remaining == 0,
            'byte_order': 'little', 'source_reference': SOURCE_REFERENCE,
            'sections': sections, 'trailer': trailer,
            'summary': {'nodes': node_count, 'attributes': attribute_count,
                        'local_symbols': symbol_count, 'values': value_count,
                        'type_tags': sorted({a['type_tag'] for a in attributes}), **graph},
            'nodes': nodes, 'attributes': attributes, 'local_symbols': local_symbols, 'values': values,
            'limitations': ['Table structure and literal byte values only; type tags are not assigned engine meanings.',
                            'Symbol labels come from explicitly supplied dictionaries; conflicts remain ambiguous.',
                            'A parsed numeric/string value is not automatically an asset reference.',
                            'Complete structural consumption does not establish scene or game runtime behavior.']}

def parse_file(path: Path, symbols=None, limits=None, offset=0, length=None):
    limits = limits or Limits()
    if path.stat().st_size > limits.max_file_bytes: raise BxmlError('file exceeds configured byte limit', 0)
    data = path.read_bytes()
    if length is None: length = len(data) - offset
    if offset < 0 or length < 0 or offset > len(data) or length > len(data)-offset:
        raise BxmlError('selected BXML span exceeds source file', offset)
    try:
        result = parse_bytes(data[offset:offset+length], symbols, limits)
    except BxmlError as exc:
        if exc.offset is not None:
            raise BxmlError('selected BXML span: '+str(exc), offset+exc.offset) from exc
        raise
    result['section_sha256'] = result['input_sha256']
    result['section_bytes'] = length
    result['input_sha256'] = hashlib.sha256(data).hexdigest()
    result['input_bytes'] = len(data)
    result['source_span'] = {'file_offset': offset, 'bytes': length, 'whole_file': offset==0 and length==len(data)}
    result['consumption_scope'] = 'selected BXML span only'
    for records in ['nodes','attributes','local_symbols','values','sections']:
        for record in result[records]:
            for key in ['file_offset','length_file_offset']:
                if key in record: record[key] += offset
    result['trailer']['file_offset'] += offset
    result['input_file'] = str(path)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--symbols', action='append', default=[], type=Path)
    parser.add_argument('--offset', type=lambda s:int(s,0), default=0,
                        help='explicit byte offset of BXML section; no signature scan')
    parser.add_argument('--length', type=lambda s:int(s,0),
                        help='explicit BXML byte length; defaults to rest of file')
    args = parser.parse_args()
    dictionaries = []
    for path in args.symbols:
        dictionaries.extend(sorted(path.rglob('*.csv')) if path.is_dir() else [path])
    labels, provenance = load_symbols(dictionaries)
    result = parse_file(args.input, labels, offset=args.offset, length=args.length)
    result['symbol_dictionaries'] = provenance
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ['input_file','input_sha256','input_bytes','bytes_consumed','complete_consumption','summary','trailer']}, indent=2))

if __name__ == '__main__': main()
