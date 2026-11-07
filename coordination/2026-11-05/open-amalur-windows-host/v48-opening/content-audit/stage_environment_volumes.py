from pathlib import Path
import sys,json,struct,hashlib,xml.etree.ElementTree as E
import numpy as np
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;P=Q.parents[2];sys.path[:0]=[str(Q),str(P/'work/v19-lighting')];import content_sources as C,decode_scene_lighting as D
def sha(b):return hashlib.sha256(b).hexdigest()
def xml_value(e):
 if len(e):return {x.attrib['name']:xml_value(x) for x in e}
 t=(e.text or '').strip();typ=e.attrib.get('type')
 if typ in ['float','uint','int']:return float(t) if typ=='float' else int(t)
 if typ in ['Vector3','float4']:return list(map(float,t.split()))
 return t
def qr(q,v):
 u=np.array(q[:3]);t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
def main():
 O=Q/'candidate-first-room/environment';O.mkdir(parents=True,exist_ok=True)
 sf=Q/'inputs/patch_0.pak/1417252.space_bxml';rf=Q/'inputs/patch_0.pak/1262814.region_bxml';sr,sp=C.graph(sf);rr,rp=C.graph(rf)
 lights=D.decode_space_lights(sr);region=D.decode_region(rr);lp,ln=struct.unpack_from('<2I',sp,0x90);native_lights=sr[lp:lp+ln*108];assert len(native_lights)==113*108
 b=struct.pack('<8sII',b'OALP108\0',ln,108)+native_lights;(O/'point-lights.bin').write_bytes(b);(O/'point-lights.json').write_text(json.dumps(lights,indent=2)+'\n')
 cubes=[]
 for c in region['ambient_cubes']:
  data=b''.join(rp[off:off+256] for off in c['face_texel_offsets']);assert len(data)==1536
  name=f"ambient-cube-{c['index']}.raw";(O/name).write_bytes(data);cubes.append(dict(index=c['index'],file=name,sha256=sha(data),bytes=len(data),source_face_payload_offsets=c['face_texel_offsets'],face_order='source six face order preserved',channel_order='source packed texel bytes preserved; root uses reviewed native cube channel mapping'))
 profiles=[]
 for name in ['lighting_dgn_wellofsouls','lighting_dgn_wellofsouls_start','cin_lighting_dgn_wellofsouls']:
  f=Q/f'inputs/initial_0.pak/{name}.koalighting';raw=f.read_bytes();doc=E.fromstring(raw);obj=next(iter(doc));profiles.append(dict(name=name,source=str(f.relative_to(P)),sha256=sha(raw),dataobject=obj.attrib,fields={x.attrib['name']:xml_value(x) for x in obj}))
 luts=[]
 for tid in [1315352,1529772]:
  lut=Q/f'inputs/initial_0.pak/{tid}.dds';raw=lut.read_bytes();assert raw[16:20]==b'KEEN' and struct.unpack_from('<3H',raw,20)==(16,16,16) and raw[29]==40 and len(raw)==38+16**3*4
  name=f'color-table-{tid}.rgba16cube';(O/name).write_bytes(raw[38:])
  luts.append(dict(asset=tid,name=C.SYMS['texture'][str(tid)],file=name,dimensions=[16,16,16],source_format=40,source_payload_offset=38,source_sha256=sha(raw),rgba_payload_sha256=sha(raw[38:]),policy='sourceRGBA8volumebytes retained,noLUTinterpolation/resampling'))
 report=dict(space=1417252,region=1262814,source_spawn=[4312,2806,-314,-180],region_environment=region,authored_xml_profiles=profiles,point_lights=dict(file='point-lights.bin',magic='OALP108\\0',count=ln,stride=108,bytes=len(b),sha256=sha(b),layout='float27/record:pXYZ;4keyRGB[Midnight,Dawn,Noon,Dusk];4multipliers;4attenuationStarts;4attenuationEnds',source_file=str(sf.relative_to(P)),source_offset=lp),ambient_cubes=cubes,color_tables=luts,limits=['No openingruntimeframe oractivecinematic environment override observed; keepbase/start/cinematic XML profiles separate.','Selected MQ01/StartRoom/cinematic Lua literals contain no explicit lighting override; no automaticstartprofile selection claimed.','No outdoor Dalentarth lighting constants copied.','Ambientrawtexels preserve sourcechannel bytes; applyexistingreviewedrenderer cubemap mapping.'])
 (O/'environment-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 allv=json.loads((Q/'opening-volume-source-records.json').read_text());world=[]
 for g in allv:
  vv=[]
  for r in g['rows']:
   q=r['quaternion'];cq=(-q[0],-q[1],-q[2],q[3]);local=np.array(r['source_vertices'])[:,:3];w=qr(cq,local*np.array(r['scale']))+r['position'];cent=w.mean(0);planes=[]
   for ids in np.array(r['source_indices']).reshape(-1,3):
    a,b,c=w[ids];n=np.cross(b-a,c-a);n/=np.linalg.norm(n);d=-n@a
    if n@cent+d>0:n=-n;d=-d
    assert np.max(w@n+d)<1e-7
    planes.append([*n.tolist(),float(d)])
   spawn=np.array([4312,2806,-314]);inside=all(np.dot(pl[:3],spawn)+pl[3]<=0 for pl in planes)
   vv.append({**r,'world_vertices':w.tolist(),'world_bounds':[w.min(0).tolist(),w.max(0).tolist()],'convex_planes_outward':planes,'authored_spawn_point_inside':inside})
  world.append(dict(space=g['space'],rows=vv))
 report=dict(source_layout='SPACEroot0xd8 pointer/count,96B records:+0verticesptr/countfloat4,+8facePlaneTriplesptr/countu32,+16extra ptr/count,+24scriptID,+28nameptr,+40float4position,+56qXYZW,+72float3scale,+84flags,+88instanceID',native_evidence=['00fdc910 Spacevf3 root+d8/dc→Space+74/78','00ff04f0 Spacevf4→00fef2d0(Space+74)','00fef2d0 sourceadvance0x60/runtimeadvance0xa8','00fbdbc0 source+1cname,+18script,+54flagsbit0','00fb0f60 sourceS+48,T+28,Q+38→00adcd40'],planes_policy='Original8corners and6orientedplane triples; worlddirectconjugateTQS; no trigger radius guessed',spaces=world,limits=['Playerfeetpoint classification is diagnostic; native entering-object collision shape/tolerances/eventordering not reconstructed.','Script service agent owns actualcallbacks/state transitions.'])
 (Q/'opening-volume-world-contract.json').write_text(json.dumps(report,indent=2)+'\n')
 print('ENV',ln,'lights',len(cubes),'cubes',len(profiles),'XMLprofiles; volumeSpaces',len(world),'spawnInside',[r['name'] for g in world if g['space']==1417252 for r in g['rows'] if r['authored_spawn_point_inside']])
if __name__=='__main__':main()
