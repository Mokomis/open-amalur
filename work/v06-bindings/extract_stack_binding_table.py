"""Extract straight-line stack binding descriptors with actual ESP accounting.

Only the two observed name constructors and verified stack probe have known stack effects. Extraction
stops at the first other call after descriptor initialization; unrecognized
branches/stack writes also stop. Names are paired with the callback at +12,
never the closest callback assignment in disassembly.
"""
import argparse,hashlib,json,platform,struct,sys
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur';sys.path.insert(0,str(root/'tools/python-libs'))
import capstone
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('start',type=lambda s:int(s,0));p.add_argument('size',type=lambda s:int(s,0));args=p.parse_args()
assert args.size<=0x10000 and args.size>0
assert all(c.isalnum() or c in '-_' for c in args.label)
b=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe').read_bytes();sha=hashlib.sha256(b).hexdigest();assert sha=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
pe=struct.unpack_from('<I',b,0x3c)[0];base=struct.unpack_from('<I',b,pe+52)[0];opt=struct.unpack_from('<H',b,pe+20)[0];sects=[]
for n in range(struct.unpack_from('<H',b,pe+6)[0]):
 at=pe+24+opt+40*n;vsz,rva,sz,off=struct.unpack_from('<IIII',b,at+8);fl=struct.unpack_from('<I',b,at+36)[0];sects.append((base+rva,sz,off,bool(fl&0x20000000)))
def raw(va,n):
 for start,size,off,exe in sects:
  if start<=va and va+n<=start+size:return b[off+va-start:off+va-start+n]
 return None
def text(va):
 if not isinstance(va,int):return None
 rawdata=raw(va,160)
 if rawdata is None:return None
 data=rawdata.split(b'\0',1)[0]
 return data.decode('ascii') if data and len(data)<160 and all(32<=c<127 for c in data) else None
def executable(va):return isinstance(va,int) and any(start<=va<start+size and exe for start,size,off,exe in sects)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
sp=0;stack={};regs={};names=[];instructions=[];stop=None;modeled_helpers=[]
X=capstone.x86
for ins in md.disasm(raw(args.start,args.size),args.start):
 ops=ins.operands;record={'address':hex(ins.address),'bytes':ins.bytes.hex(),'mnemonic':ins.mnemonic,'operands':ins.op_str,'sp':sp};instructions.append(record)
 def address(op):
  return sp+op.mem.disp if op.type==X.X86_OP_MEM and op.mem.base==X.X86_REG_ESP and op.mem.index==0 else None
 def val(op):
  if op.type==X.X86_OP_IMM:return op.imm&0xffffffff
  if op.type==X.X86_OP_REG:return regs.get(op.reg)
  a=address(op);return stack.get(a,{}).get('value') if a is not None else None
 if ins.mnemonic=='push':
  value=val(ops[0]);sp-=4;stack[sp]={'value':value,'instruction':hex(ins.address)}
 elif ins.mnemonic=='pop':
  if ops[0].type==X.X86_OP_REG:regs[ops[0].reg]=stack.get(sp,{}).get('value')
  sp+=4
 elif ins.mnemonic in ('sub','add') and ops[0].type==X.X86_OP_REG and ops[0].reg==X.X86_REG_ESP and ops[1].type==X.X86_OP_IMM:
  sp+=ops[1].imm*(1 if ins.mnemonic=='add' else -1)
 elif ins.mnemonic=='lea' and ops[0].type==X.X86_OP_REG:
  a=address(ops[1]);regs[ops[0].reg]=('stack',a) if a is not None else None
 elif ins.mnemonic=='mov':
  a=address(ops[0]);value=val(ops[1])
  if ops[0].type==X.X86_OP_REG:
   if ops[0].reg==X.X86_REG_ESP:stop='unmodeled ESP assignment';break
   regs[ops[0].reg]=value
  elif a is not None:stack[a]={'value':value,'instruction':hex(ins.address)}
 elif ins.mnemonic=='xor' and len(ops)==2 and ops[0].type==ops[1].type==X.X86_OP_REG and ops[0].reg==ops[1].reg:regs[ops[0].reg]=0
 elif ins.mnemonic=='call':
  target=ops[0].imm if ops[0].type==X.X86_OP_IMM else None
  if target==0x11bea60 and not names:
   # Original helper copies the return address to (entry ESP - EAX), restores
   # ECX, then RET. Relative to caller ESP, net effect is subtract original EAX.
   # Page touches and unsigned-underflow guard do not change ordinary frames.
   probe=bytes.fromhex('518d4c24042bc81bc0f7d023c88bc42500f0ffff3bc8720a8bc159948b00890424c32d001000008500ebe9')
   amount=regs.get(X.X86_REG_EAX)
   if raw(target,len(probe))!=probe or not isinstance(amount,int) or not 0<amount<=0x100000:
    stop='stack probe bytes/size not established';break
   sp-=amount;regs[X.X86_REG_EAX]=None
   modeled_helpers.append({'call':hex(ins.address),'helper':hex(target),'effect':'ESP subtract original EAX; ECX preserved; EAX invalidated','allocation_bytes':amount,'helper_hex':probe.hex()})
   continue
  if target not in (0xaf4d70,0xaf4d40):stop='unmodeled call '+ins.op_str;break
  this=regs.get(X.X86_REG_ECX);nameptr=stack.get(sp,{}).get('value');name=text(nameptr)
  if not isinstance(this,tuple) or this[0]!='stack' or not name:stop='constructor operands not statically established';break
  names.append({'name':name,'name_address':hex(nameptr),'name_object_stack_offset':this[1],'constructor_call':hex(ins.address),'constructor':hex(target)})
  sp+=16 if target==0xaf4d70 else 4
  regs[X.X86_REG_EAX]=this;regs[X.X86_REG_ECX]=None;regs[X.X86_REG_EDX]=None
 elif ins.mnemonic.startswith('j') or ins.mnemonic.startswith('ret') or ins.mnemonic=='int3':stop='control-flow boundary '+ins.mnemonic;break
 # Other instructions in prologue such as cookie XOR don't affect tracked stack.
for item in names:
 slot=item['name_object_stack_offset']+12;record=stack.get(slot,{})
 item.update(callback_stack_offset=slot,callback=hex(record['value']) if executable(record.get('value')) else None,callback_store=record.get('instruction'))
report={'target_sha256':sha,'entry':hex(args.start),'bounded_bytes':args.size,'stop_reason':stop,'stop_address':instructions[-1]['address'] if instructions else None,'descriptors':names,'instructions':instructions,'modeled_helpers':modeled_helpers,
 'scope':'Straight-line initializer extraction with exact stack accounting. Descriptor+12 callback layout corroborated from constructor code; namespace and registration consumer require independent trace.'}
out=root/'outputs/engine-bindings-v06'/(args.label+'.json');out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('instructions','scope')},indent=2))
