"""Windows-only bounded test of original pure matrix arithmetic, never game startup."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,platform,math
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';o=r/('outputs/scene-v17'if'--with-workbench'in sys.argv else'outputs/scene-v16');h=r/'work/v16-host'
exe=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
raw=exe.read_bytes();digest=hashlib.sha256(raw).hexdigest();assert digest=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
sys.path[:0]=[str(r/'work/v07-bxml'),str(r/'tools/python-libs')]
from amalur_scene import transform
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM
pe=struct.unpack_from('<I',raw,0x3c)[0];sections=struct.unpack_from('<H',raw,pe+6)[0];opt=struct.unpack_from('<H',raw,pe+20)[0];table=pe+24+opt
def at(va,n):
 for i in range(sections):
  size,start,rawsize,offset=struct.unpack_from('<4I',raw,table+40*i+8)
  if start<=va-0x400000 and va-0x400000+n<=start+rawsize:return raw[offset+va-0x400000-start:offset+va-0x400000-start+n]
 raise ValueError('Unmapped native span')
code=at(0xac3a70,0xac443a-0xac3a70);decoder=Cs(CS_ARCH_X86,CS_MODE_32);decoder.detail=True;ins=list(decoder.disasm(code,0xac3a70))
assert ins[-1].mnemonic=='ret' and all(i.mnemonic!='call' for i in ins)
for i in ins:
 if i.mnemonic.startswith('j'):assert 0xac3a70<=int(i.op_str,16)<0xac443a
placements=json.loads((r/'outputs/scene-v07/placements.json').read_text())['placements']
if '--with-workbench'in sys.argv:
 obj=next(x for x in json.loads((r/'outputs/scene-v12/scene-objects.json').read_text())['objects']if x['instance_id']==524875)
 placements.append(dict(index=len(placements),fab_id=695560,position_xyz=obj['position_xyz'],quaternion_xyzw=obj['quaternion_xyzw'],scale_xyz=obj['scale_xyz'],flags_u32=obj['flags'],raw_hex=(b'\0'*4+bytes.fromhex(obj['raw_hex'])[8:53]).hex(),source_instance_id=obj['instance_id']))
input_path=o/'native-matrix-inputs.bin';output_path=o/'native-matrix-outputs.bin'
fixups=[]
for i in ins:
 for operand in i.operands:
  if operand.type==X86_OP_MEM and not operand.mem.base and not operand.mem.index:
   assert i.disp_size==4 and len(at(operand.mem.disp,8))==8
   fixups.append(i.address-0xac3a70+i.disp_offset)
input_path.write_bytes(struct.pack('<II',len(placements),len(fixups))+b''.join(struct.pack('<I',x)for x in fixups)+b''.join(bytes.fromhex(p['raw_hex'])[4:49]for p in placements))
run=subprocess.run([str(h/'native-matrix-probe.exe'),str(exe),str(input_path),str(output_path)],capture_output=True,timeout=10)
assert run.returncode==0,dict(exit=run.returncode,stderr=run.stderr.decode(errors='replace'))
data=output_path.read_bytes();assert struct.unpack_from('<I',data)[0]==len(placements)and len(data)==4+64*len(placements)
rows=[]
for i,p in enumerate(placements):
 matrix=struct.unpack_from('<16f',data,4+64*i);q=p['quaternion_xyzw'];conjugated=dict(p,quaternion_xyzw=[-q[0],-q[1],-q[2],q[3]])
 errors=[]
 for profile in [p,conjugated]:
  error=0
  for v in [(0,0,0),(100,0,0),(0,100,0),(0,0,100),(31,-57,89)]:
   # Native writes translation at bytes0x30/34/38; row-vector matrix layout.
   actual=[sum(v[k]*matrix[k*4+j]for k in range(3))+matrix[12+j]for j in range(3)]
   expected=transform(v,profile);error=max(error,max(abs(a-b)for a,b in zip(actual,expected)))
  errors.append(error)
 rows.append(dict(index=i,fab_id=p['fab_id'],direct_error=errors[0],conjugated_error=errors[1],native_matrix=list(matrix),flags=p['flags_u32']))
report=dict(native_executable_sha256=digest,routine='0xac3a70',routine_bytes=len(code),routine_sha256=hashlib.sha256(code).hexdigest(),routine_calls=0,scope='Standalone original arithmetic routine with unchanged source transforms; no game launch/native visual equivalence claim',matrix_storage='row-vector homogeneous; translation at0x30/34/38',rows=rows,max_direct_error=max(x['direct_error']for x in rows),max_conjugated_error=max(x['conjugated_error']for x in rows))
(o/'native-prop-matrix-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items()if k!='rows'}))
assert report['max_conjugated_error']<.002
