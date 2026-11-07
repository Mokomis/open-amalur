import sys,json,struct,math,collections
from pathlib import Path
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2]
sys.path[:0]=[str(R/"work/v07-mesh"),str(O)]
import amalur_mesh as M,amalur_fab as F,asset_source as A
cat=json.loads((O/"appearance-source-catalogue.json").read_text())
D=O/"models";D.mkdir(exist_ok=True)
def sn(v):return max(-1.,v/32767.)
def make(m):
 sid=m["fab"];fb=(R/m["path"]).read_bytes();stream=Path(m["stream"])
 if not stream.exists():return dict(fab=sid,error="missingstream")
 sb=stream.read_bytes();f=F.parse_bytes(fb);mesh=M.parse_bytes(sb)
 if len(mesh["assemblies"])!=len(f.get("mesh_descriptors",[])):return dict(fab=sid,error="descriptorassemblymismatch")
 chunks=[];bone=bytearray();remap=bytearray();asm=bytearray();rawv=bytearray();verts=bytearray();vbd=bytearray();idx=bytearray();ibd=bytearray()
 for b in f["bones"]:
  bone+=struct.pack("<iI",b["parent_raw_i16"],b["name_hash_u32"])+bytes.fromhex(b["raw_hex"])+bytes(8)
 unsupported=[];layouts=[]
 for vb in mesh["vertex_buffers"]:
  stride=vb["stride_bytes"];typ=vb["header_word0"];n=vb["vertex_count"];at=vb["data_file_offset"];raw=sb[at:at+vb["data_bytes"]]
  rawat=len(rawv);rawv+=raw;viewat=len(verts);flags=0
  # Native layout witnesses v49: only declared supported profiles.
  weighted=stride in [56,60,64,68]
  supported=weighted or stride==48
  if supported:
   flags=1|2|4|8 # P UV0 N T B (P implicit)
   if weighted:flags|=16
   if stride in [48,60,68]:flags|=32
   if stride in [64,68]:flags|=64
   for vi in range(n):
    r=raw[vi*stride:(vi+1)*stride];p=struct.unpack_from("<3f",r);j=r[12:16] if weighted else bytes(4)
    w=tuple(sn(x) for x in struct.unpack_from("<3h",r,16)) if weighted else (0.,0.,0.)
    uv=struct.unpack_from("<2f",r,24 if weighted else 12);uv1=struct.unpack_from("<2f",r,32) if stride in [64,68] else (0.,0.)
    no=40 if stride in [64,68] else 32 if weighted else 20
    ntb=[tuple(sn(x) for x in struct.unpack_from("<3h",r,no+k*8)) for k in range(3)]
    rgba=r[64:68] if stride==68 else r[56:60] if stride==60 else r[44:48] if stride==48 else bytes(4)
    v=struct.pack("<3f",*p)+j+struct.pack("<3f4f9f",*w,*uv,*uv1,*ntb[0],*ntb[1],*ntb[2])+rgba+struct.pack("<III",flags,vi,0)
    assert len(v)==96;verts+=v
  else:unsupported.append(dict(vertex_buffer=vb["index"],type=typ,stride=stride,vertices=n))
  vbd+=struct.pack("<8I",rawat,len(raw),stride,n,viewat,n*96 if supported else 0,typ,flags)
  layouts.append(dict(vb=vb["index"],type=typ,stride=stride,count=n,supported=supported,flags=flags))
 for ib in mesh["index_buffers"]:
  ibd+=struct.pack("<4I",len(idx),ib["index_count"],ib["data_file_offset"],ib["data_bytes"])
  idx+=struct.pack("<"+"I"*ib["index_count"],*ib["indices"])
 for a,d,e in zip(mesh["assemblies"],f.get("mesh_descriptors",[]),m["elements"]):
  decl=e["tail_words"][6]
  expected={56:17,60:22,64:25,68:26}
  st=mesh["vertex_buffers"][a["vertex_buffer"]]["stride_bytes"]
  assert st not in expected or expected[st]==decl,(sid,a["index"],st,decl)
  first=len(remap)//52
  for r in d["remaps"]:remap+=bytes.fromhex(r["trs"]["raw_hex"])+struct.pack("<i",r["bone_index"])
  mask=sum(1<<g["group"] for g in m["groups"] if a["index"] in g["element_indices"])
  vb=mesh["vertex_buffers"][a["vertex_buffer"]]
  ints=[a["vertex_buffer"],a["index_buffer"],e["native_material_id"],d["bone_index"]&0xffffffff,first,len(d["remaps"]),mask,1 if e["tail_flag"]&4 else 0,a["file_offset"],d["file_offset"],vb["header_word0"],e["tail_words"][6],e["tail_flag"],e["tail_words"][4],e["tail_words"][5],0]
  floats=[*e["center"],e["radius"],e["distance_min"],e["distance_max"],*d["position_xyz_uninterpreted"],*d["unknown_four_floats"],*d["unknown_two_floats"],0]
  assert len(floats)==16;asm+=struct.pack("<16I16f",*ints,*floats)
 maps=bytearray();pairs=bytearray()
 for block in f.get("definition",{}).get("unknown_blocks",[]):
  at=block["file_offset"];cnt=block["count"];end=at+4+cnt*12;mount,slot,flag=struct.unpack_from("<IIB",fb,end)
  maps+=struct.pack("<8I",len(pairs)//12,cnt,mount,slot,flag,at,0,0);pairs+=fb[at+4:end]
 chunks=[(b"BONE",bone,len(f["bones"]),64),(b"ASMB",asm,len(mesh["assemblies"]),128),(b"VBUF",vbd,len(mesh["vertex_buffers"]),32),(b"IBUF",ibd,len(mesh["index_buffers"]),16),(b"RAWV",rawv,len(rawv),1),(b"VERT",verts,len(verts)//96,96),(b"INDX",idx,len(idx)//4,4),(b"RMAP",remap,len(remap)//52,52),(b"CMAP",maps,len(maps)//32,32),(b"CPAI",pairs,len(pairs)//12,12)]
 header=32+16*len(chunks);payload=bytearray();directory=bytearray()
 for tag,data,count,stride in chunks:
  directory+=struct.pack("<4sIII",tag,header+len(payload),count,stride);payload+=data
 out=struct.pack("<8s6I",b"OAAM001\0",1,sid,header+len(payload),len(chunks),32,0)+directory+payload
 dst=D/f"{sid}.oaam";dst.write_bytes(out)
 maxpalette=max([len(d["remaps"]) or 1 for d in f.get("mesh_descriptors",[])],default=0)
 return dict(fab=sid,path=str(dst.relative_to(O)),sha256=A.H(out),bytes=len(out),bones=len(f["bones"]),assemblies=len(mesh["assemblies"]),max_palette=maxpalette,layouts=layouts,unsupported=unsupported,source_fab_sha256=A.H(fb),source_stream_sha256=A.H(sb),group_metadata=m["groups"],remap_count=len(remap)//52)
rows=[]
for m in cat["models"]:
 try:rows.append(make(m))
 except Exception as e:rows.append(dict(fab=m["fab"],error=repr(e)))
receipt=dict(schema=1,models=rows,total_bytes=sum(r.get("bytes",0) for r in rows),errors=[r for r in rows if "error"in r],max_bones=max([r.get("bones",0) for r in rows]),max_palette=max([r.get("max_palette",0) for r in rows]),layout_counts=dict(collections.Counter(str((l["type"],l["stride"],l["supported"])) for r in rows for l in r.get("layouts",[]))))
(O/"model-build-receipt.json").write_text(json.dumps(receipt,indent=2))
print(json.dumps({k:v for k,v in receipt.items() if k!="models"},indent=2))
