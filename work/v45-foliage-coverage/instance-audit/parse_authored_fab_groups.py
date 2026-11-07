"""Read native serialized FAB elements/groups without modifying source assets.

Layout witnesses:00d400d0,00d196c0,00cccc50,00ccd0b0.
Unknown fields remain raw; this does not implement runtime LOD selection.
"""
from pathlib import Path
import hashlib,json,struct

def parse_fab_groups(path):
    b = Path(path).read_bytes()
    start = struct.unpack_from('<I',b)[0]
    p = start
    def take(n):
        nonlocal p
        assert n >= 0 and p+n <= len(b)
        v = b[p:p+n]
        p += n
        return v
    def u():
        return struct.unpack('<I',take(4))[0]
    base = u()
    hash_count = u()
    hashes = list(struct.unpack('<'+'I'*hash_count,take(4*hash_count)))
    child_count = u()
    for _ in range(child_count):
        take(u()*12)
        take(9)
    take(u()*4)
    take(u()*2)
    count = u()
    assert count < 256
    elements = []
    for i in range(count):
        st = p
        sphere = struct.unpack('<5f',take(20))
        limits = struct.unpack('<2f',take(8))
        subdraw_count = u()
        subdraw_hex = take(subdraw_count*52).hex()
        tail = take(37)
        words = struct.unpack_from('<9I',tail)
        elements.append(dict(element=i,file_offset=st,center=list(sphere[:3]),radius=sphere[4],distance_min=limits[0],distance_max=limits[1],subdraw_count=subdraw_count,subdraw_hex=subdraw_hex,native_material_id=words[3],tail_words=words,tail_flag=tail[36],tail_hex=tail.hex()))
    groups = []
    for i in range(9):
        st = p
        n = u()
        assert n < 256
        indices = list(take(n))
        n = u()
        assert n < 256
        second = list(take(n))
        threshold,flag = struct.unpack('<fB',take(5))
        assert all(v < count for v in indices)
        groups.append(dict(group=i,file_offset=st,element_indices=indices,second_list=second,threshold=threshold,flag=flag))
    return dict(fab=int(Path(path).name.split('.')[0]),source=str(path),sha256=hashlib.sha256(b).hexdigest(),serialized_start=start,base_word=base,hash_keys=hashes,elements=elements,groups=groups,groups_end=p,remaining_bytes=len(b)-p)

if __name__ == '__main__':
    q = Path(__file__).resolve().parent
    result = [parse_fab_groups(p) for p in sorted((q/'inputs/DATA_0.pak').glob('*.fab_bxml'))]
    (q/'authored-fab-groups.json').write_text(json.dumps(result,indent=2))
    print('Decoded',len(result),'FAB metadata files')
