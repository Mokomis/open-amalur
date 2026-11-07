"""Stage source-authored region Space graph and portal rectangles. No live writes."""
from pathlib import Path
import hashlib,json,struct,math,re
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent;O=Q/'candidate-world';O.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def find(name):return next(P/'work/v20-inputs'/a/name for a in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (P/'work/v20-inputs'/a/name).exists())
f=find('431608.region_bxml');raw=f.read_bytes();b=raw[8:8+struct.unpack_from('<I',raw)[0]]
ptr,n=struct.unpack_from('<2I',b,0x14);region_ids=list(struct.unpack_from('<%dI'%n,raw,ptr))
p0,n0=struct.unpack_from('<2I',b,0xc0);p1,n1=struct.unpack_from('<2I',b,0xc8);assert n0==n1==27
src=json.loads((P/'work/v45-foliage-coverage/expanded-leaf-attributes/source-provenance.json').read_text())
ids=sorted(set(region_ids)|{s['space'] for s in src});initial=431638
assert re.search(r'SPACE, REGION, DOOR\s*=\s*431638', (P/'work/v20-char/build_town.py').read_text())
assert initial in ids
edges=[];proof=[]
for i in range(n0):
 a=raw[p0+164*i:p0+164*(i+1)];v=raw[p1+164*i:p1+164*(i+1)];pid,sid,other=struct.unpack_from('<3I',a,152)
 assert (sid,other,pid)==struct.unpack_from('<3I',v,104)
 assert a[:48]==v[:48] and a[144:152]==v[96:104]
 center=struct.unpack_from('<3f',v,116);normal=struct.unpack_from('<3f',v,128);right=struct.unpack_from('<3f',v,140);up=struct.unpack_from('<3f',v,152)
 assert all(math.isfinite(z) for x in [center,normal,right,up] for z in x)
 assert sid in ids and other in ids and sid!=other
 assert abs(sum(z*z for z in normal)-1)<.001
 assert abs(math.sqrt(sum(z*z for z in right))-.5*struct.unpack_from('<f',v,96)[0])<.1
 assert abs(math.sqrt(sum(z*z for z in up))-.5*struct.unpack_from('<f',v,100)[0])<.1
 edges.append(struct.pack('<3I12f',sid,other,pid,*center,*normal,*right,*up))
 proof.append(dict(row=i,source_primary_payload_offset=p0-8+164*i,source_companion_payload_offset=p1-8+164*i,portal=pid,space_a=sid,space_b=other,center=center,normal=normal,right=right,up=up,primary_source_record_hex=a.hex(),companion_source_record_hex=v.hex()))
blob=struct.pack('<8s6I',b'OACAN01\0',len(ids),len(edges),initial,1,431608,0)+struct.pack('<%dI'%len(ids),*ids)+b''.join(edges)
assert len(blob)==32+4*len(ids)+60*len(edges)
(O/'canopy-visibility.bin').write_bytes(blob)
admitted={431646}|{other if sid==431646 else sid for sid,other,_ in [struct.unpack_from('<3I',e) for e in edges] if sid==431646 or other==431646}
rt=json.loads((Q/'runtime/registered-collections.json').read_text());assert set(rt['registered_static_spaces'])=={0}|admitted
report=dict(status='Source graph candidate; native one-hop default proven viaff08f0→fdce90(depth1)→fef1c0/fdcf20',source=str(f.relative_to(P)),source_sha256=sha(raw),source_initial_space=initial,source_initial_space_evidence='build_town.py source scene SPACE=431638; exact legacy save is still at its shop-door spawn',native_current_space=rt['cameras'][0]['space_id'],native_registered_spaces=rt['registered_static_spaces'],source_graph_neighbors_at_bridge=sorted(admitted),native_default_graph_hops=1,nodes=ids,portals=proof,sha256=sha(blob),bytes=len(blob),limits=['Graph traversal and asset identity are native-proven; custom controller finite-portal crossing is an explicit reconstruction policy.','Reference fixture must supply actual cameraSpace431646 because its eye is overridden while hidden player stays at source spawn.','No nearest-position classification or capture-specific tree/source whitelist.','Additional embedded Space IDs retained as nodes; source RegionLink destinations/other regions are not traversed by this scene graph.'])
(Q/'graph-stage.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='portals'},indent=2))
