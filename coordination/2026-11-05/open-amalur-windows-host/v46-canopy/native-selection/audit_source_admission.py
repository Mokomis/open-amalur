from pathlib import Path
import collections, hashlib, json, struct
P = Path(r'C:\Users\rwill\Documents\Opem Amalur')
Q = P / 'work/v46-canopy/native-selection'
S = json.loads((P/'work/v20-inputs/symbols.json').read_text())
f = P/'work/v20-inputs/patch_0.pak/431608.region_bxml'
raw = f.read_bytes()
b = raw[8:8+struct.unpack_from('<I',raw)[0]]
ap,n = struct.unpack_from('<2I',b,0xc0)
bp,bn = struct.unpack_from('<2I',b,0xc8)
assert n == bn == 27
edges = []
adj = collections.defaultdict(set)
for i in range(n):
    a = raw[ap+164*i:ap+164*(i+1)]
    render = raw[bp+164*i:bp+164*(i+1)]
    u,v = struct.unpack_from('<2I',a,0x9c)
    ur,vr = struct.unpack_from('<2I',render,0x9c)
    # The render portal record is a distinct layout; topology uses source A only.
    assert str(u) in S['simspace'] and str(v) in S['simspace']
    adj[u].add(v)
    adj[v].add(u)
    edges.append(dict(edge=i,from_space=u,to_space=v,from_name=S['simspace'][str(u)],to_name=S['simspace'][str(v)],source_file_offset=ap+164*i,render_file_offset=bp+164*i,source_sha256=hashlib.sha256(a).hexdigest(),render_sha256=hashlib.sha256(render).hexdigest(),initial_records_identical=a==render,source_hex=a.hex(),render_hex=render.hex()))
def bfs(current,depth):
    seen = {current}
    todo = [(current,depth)]
    while todo:
        sid,d = todo.pop(0)
        if d <= 0:
            continue
        for other in sorted(adj[sid]):
            if other not in seen:
                seen.add(other)
                todo.append((other,d-1))
    return sorted(seen)
allowed = bfs(431646,1)
assert allowed == [431646,431650]
meta = json.loads((P/'work/v45-foliage-coverage/native-leaf-authored-ranges/authored-range-metadata.json').read_text())
rows = meta['rows']
checks = []
for c in meta['native_space_leaf_checks']:
    selected = [rows[x['source_instance']] for x in c['source_matches']]
    ids = sorted({x['space'] for x in selected})
    checks.append(dict(native_draw=c['native_draw'],source_instances=[x['source_instance'] for x in selected],source_spaces=ids,admitted=bool(ids) and all(sid in allowed for sid in ids)))
assert len(checks)==33 and all(x['admitted'] for x in checks)
assert rows[198]['space']==431642 and 431642 not in allowed
counts = collections.Counter()
for r in rows:
    counts[r['space']] += r['triangles']
profiles = {}
for sid in sorted(adj):
    profiles[str(sid)] = dict(space=sid,name=S['simspace'][str(sid)],neighbors=sorted(adj[sid]),ordinary_native_depth=1,admitted_space_ids=[0]+bfs(sid,1))
proof = dict(source_region=431608,source=str(f.relative_to(P)),source_sha256=hashlib.sha256(raw).hexdigest(),native_reader='fcb620->fc4a70(root+c0)',source_slot=0xc0,render_slot=0xc8,stride=164,endpoint_offsets=[156,160],source_portals=n,graph_nodes=len(adj),native_initial_request='ff08f0->fdce90 depth1; push1@ff0933/call@ff0940',native_recursion='fef1c0 iffdepth>0 ->fdcf20(current,depth-1); allincidentOTHERendpoints',direction='undirected',reference_current_space=431646,reference_admitted_space_ids=[0]+allowed,reference_native_positive_checks=checks,reference_native_positive_count=33,reference_extra_source198_admitted=False,reference_retained_SPACE_leaf_triangles=sum(counts[s] for s in allowed),dense_SPACE_leaf_triangles=sum(counts.values()),source_space_triangle_counts=dict(counts),edges=edges,profiles=profiles,limits=['CameraSpaceisexplicitpersistentidentity,notnearestposition. Customportalrectanglecrossingpolicy needs separate label/validation.','Onehopisordinaryloadingrequestbudget; transientpending/staleresource retention isnotmodeledhere.','Per-viewportal/frustum/PVScontext canfurtherrestrictloadedspaces; graphprovescollectionadmission,notallfinalpixelcoverage.'])
(Q/'source-space-admission-proof.json').write_text(json.dumps(proof,indent=2))
print({k:proof[k] for k in ['source_portals','graph_nodes','reference_admitted_space_ids','reference_native_positive_count','reference_extra_source198_admitted','reference_retained_SPACE_leaf_triangles','dense_SPACE_leaf_triangles']})
print('NORTH',profiles['431638'])
print('LIVE', (P/'work/v46-canopy/runtime/registered-collections.json').read_text()[:2800])
