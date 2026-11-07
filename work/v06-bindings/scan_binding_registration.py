"""Windows read-only PE binding-table discovery. Candidate data, not ABI proof."""
from pathlib import Path
import hashlib,json,platform,struct,sys
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur'
sys.path.insert(0,str(root/'tools/python-libs'))
import capstone
path=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
b=path.read_bytes();digest=hashlib.sha256(b).hexdigest();assert digest=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
pe=struct.unpack_from('<I',b,0x3c)[0];assert b[pe:pe+4]==b'PE\0\0'
count=struct.unpack_from('<H',b,pe+6)[0];opt=struct.unpack_from('<H',b,pe+20)[0];base=struct.unpack_from('<I',b,pe+24+28)[0]
sections=[]
for i in range(count):
 p=pe+24+opt+i*40;n=b[p:p+8].split(b'\0')[0].decode();vs,rva,size,offset=struct.unpack_from('<IIII',b,p+8);flags=struct.unpack_from('<I',b,p+36)[0]
 sections.append({'name':n,'va':base+rva,'size':size,'raw':offset,'virtual_size':vs,'execute':bool(flags&0x20000000)})
def locate(va,n=1):
 for s in sections:
  if s['va']<=va and va+n<=s['va']+s['size']:return s,s['raw']+va-s['va']
 return None,None
def raw(va,n):
 s,o=locate(va,n);return b[o:o+n] if s else None
def ascii(va,limit=160):
 s,o=locate(va)
 if not s:return None
 end=b.find(b'\0',o,min(o+limit,s['raw']+s['size']))
 if end<0:return None
 blob=b[o:end]
 return blob.decode('ascii') if blob and all(32<=v<127 for v in blob) else None
def executable(va):
 s,o=locate(va);return bool(s and s['execute'])
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
def dis(va,n=64):
 blob=raw(va,n)
 if blob is None:return []
 return [{'address':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in md.disasm(blob,va)]
names=['ACTOR','QUEST','GAME','TIME','WINDOW','PLAYER','SH','SL','is_space_loaded','get_stage','set_stage','get_player','get_time','delayed_function_call','find_window','set_visible','give_item_to_player','find_static_type','get_variable','set_variable','instantiate_object','uninstantiate_object','has_actor_state','set_actor_state','fast_travel','cheat_add_item','add_alert','play_ui','get_position','get_name','luaL_register']
strings={}
for name in names:
 pat=name.encode()+b'\0';hits=[];at=b.find(pat)
 while at>=0:
  for s in sections:
   if s['raw']<=at<s['raw']+s['size']:hits.append(s['va']+at-s['raw']);break
  at=b.find(pat,at+1)
 strings[name]=hits
records=[]
for name,hits in strings.items():
 for va in hits:
  refs=[];pat=struct.pack('<I',va);at=b.find(pat)
  while at>=0:
   for sec in sections:
    if sec['raw']<=at and at+4<=sec['raw']+sec['size']:
     addr=sec['va']+at-sec['raw'];r={'address':hex(addr),'section':sec['name'],'executable_section':sec['execute']}
     if sec['execute']:
      before=b[at-1] if at else 0
      if before==0x68 or 0xb8<=before<=0xbf:
       r['decoded_reference']=dis(addr-1,50)
      r['raw_context']={'address':hex(addr-24),'hex':(raw(addr-24,64) or b'').hex()}
     else:
      words=[]
      for off in range(-32,36,4):
       blob=raw(addr+off,4)
       if blob is None:continue
       value=struct.unpack('<I',blob)[0]
       words.append({'slot':hex(addr+off),'value':hex(value),'ascii':ascii(value),'executable_pointer':executable(value)})
      r['neighbor_words']=words
     refs.append(r);break
   at=b.find(pat,at+1)
  records.append({'name':name,'string_address':hex(va),'references':refs})
# Adjacent data pairs are candidates. Restrict names to Lua-like identifiers.
pairs=[]
for sec in sections:
 if sec['execute']:continue
 for pos in range(0,max(0,sec['size']-7),4):
  left,right=struct.unpack_from('<II',b,sec['raw']+pos)
  text=ascii(left) if executable(right) else None
  if text and len(text)<=100 and all(c.isalnum() or c in '_.:' for c in text):
   pairs.append({'slot':hex(sec['va']+pos),'name':text,'name_address':hex(left),'function_candidate':hex(right)})
out=root/'outputs/engine-bindings-v06';out.mkdir(exist_ok=True)
report={'target_sha256':digest,'scope':'Original PE bytes, no execution. Pointer adjacency and references are candidates; registration ABI/namespace not yet proven.','sections':sections,'targeted_records':records,'adjacent_name_code_pairs':pairs}
(out/'registration-scout.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'targeted_string_records':len(records),'adjacent_name_code_pairs':len(pairs),'names':{n:len(v) for n,v in strings.items()}},indent=2))
