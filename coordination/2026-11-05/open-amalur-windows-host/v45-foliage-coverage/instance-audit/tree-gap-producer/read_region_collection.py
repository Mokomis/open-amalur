"""Read all four authored FabInstanceCollection groups from a region BXML.

This is source deserialization, independent of a captured camera or pose list.
Offsets are the shipped Region schema; Space's corresponding table is0x18
bytes earlier. Full reference/physics/render records remain in the result.
"""
from pathlib import Path
import hashlib,json,struct
import numpy as np

def read_region_collection(path,symbols=None):
    path = Path(path)
    raw = path.read_bytes()
    size = struct.unpack_from('<I',raw)[0]
    graph = raw[8:8+size]
    def array(slot,stride):
        pointer,count = struct.unpack_from('<II',graph,slot)
        assert pointer >= 8 and pointer+count*stride <= len(raw)
        return pointer,[raw[pointer+i*stride:pointer+(i+1)*stride] for i in range(count)]
    result = []
    for group,(refs,physics,renders) in enumerate([(0x140,0x160,0x168),(0x148,0x170,0x178),(0x150,0x180,0x188),(0x158,0x190,0x198)]):
        rp,reference = array(refs,16)
        pp,bounds = array(physics,80)
        vp,visual = array(renders,84)
        assert len(reference) == len(bounds) == len(visual)
        for i,(ref,ph,rr) in enumerate(zip(reference,bounds,visual)):
            fab = struct.unpack_from('<I',ref,8)[0]
            material,assembly = struct.unpack_from('<II',rr,64)
            translation = struct.unpack_from('<3f',rr,16)
            quat = np.array(struct.unpack_from('<4f',rr,32))
            scale = np.array(struct.unpack_from('<3f',rr,48))
            v = np.diag(scale)
            u = -quat[:3]
            t = 2*np.cross(u,v)
            basis = v+quat[3]*t+np.cross(u,t)
            result.append(dict(source_index=len(result),group=group,record=i,fab=fab,name=symbols.get('fab',{}).get(str(fab),'?') if symbols else '?',material=material,assembly=assembly,translation=translation,quaternion=quat.tolist(),scale=scale.tolist(),basis=basis.tolist(),distance_squared_fields=list(struct.unpack_from('<2f',ph,64)),physics_flags=struct.unpack_from('<I',ph,72)[0],physics_collection_ordinal=struct.unpack_from('<I',ph,76)[0],ref_slot=hex(refs),render_slot=hex(renders),ref_file_offset=rp+i*16,physics_file_offset=pp+i*80,render_file_offset=vp+i*84,source=str(path),source_sha256=hashlib.sha256(raw).hexdigest(),reference_record_hex=ref.hex(),physics_record_hex=ph.hex(),render_record_hex=rr.hex()))
    return result

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('--symbols',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    symbols = json.loads(args.symbols.read_text()) if args.symbols else None
    rows = read_region_collection(args.source,symbols)
    args.output.write_text(json.dumps(rows,indent=2))
    print('Authored regional collection records:',len(rows))
