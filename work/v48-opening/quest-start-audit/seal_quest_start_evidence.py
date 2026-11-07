"""Seals targeted retained-source/native evidence; no original file mutation or runtime/game invocation."""
from pathlib import Path
import json,struct,hashlib,sys,subprocess
sys.dont_write_bytecode=True
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def dump(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2),encoding='utf-8')
def native(file,address):
 q=P/'work/v30-engine/decomp'/file;s=q.read_text();a=s.find('// '+address+' ');assert a>=0;b=s.find('\n// ',a+4);text=s[a:b if b>=0 else None]
 target=O/'native'/('fn-'+address+'.c.txt');target.parent.mkdir(exist_ok=True);target.write_text(text)
 return dict(address=address,source=str(q.relative_to(P)),source_sha256=H(q.read_bytes()),excerpt=str(target.relative_to(O)),excerpt_sha256=H(target.read_bytes()))
functions=[
 ('BHG_Asset.c','00ff1f00'),('BHG_Quest.c','00ff1b00'),
 ('unnamed_00fa.c','00faeea0'),('unnamed_00e6.c','00e65610'),('unnamed_00e6.c','00e65a60'),
 ('unnamed_00ff.c','00ff0310'),('unnamed_00fe.c','00fefe00'),
 ('unnamed_00e6.c','00e68ea0'),('unnamed_00e6.c','00e65320'),
 ('unnamed_00fd.c','00fda620'),('unnamed_00fd.c','00fd9a00'),
 ('unnamed_00aa.c','00aadd20'),('BHG_LuaParameter.c','00aa18e0'),
 ('unnamed_0103.c','0103a510'),('unnamed_0103.c','0103a5f0')]
natives=[native(f,a) for f,a in functions]
tool=P/'tools/android/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-objdump.exe'
ranges=[('quest-start-this-pointer','0xfda620','0xfda772'),('window-platform','0xb513e0','0xb51462'),('setup-new-game-flag','0xe25710','0xe2572c')]
for name,a,b in ranges:
 r=subprocess.run([str(tool),'--disassemble','--start-address='+a,'--stop-address='+b,str(P/'work/v30-engine/koa.exe')],capture_output=True,text=True)
 assert r.returncode==0
 (O/'native'/(name+'.asm.txt')).write_text(r.stdout)
dump('native-provenance.json',dict(executable_sha256=H((P/'work/v30-engine/koa.exe').read_bytes()),decomp=natives,
 static_disassembly_ranges=ranges,disassembler=str(tool.relative_to(P)),instructions='Read-only disassembly of existing executable; no native code executed.'))

selection=[
 ('main_menu',13493,'661b3f507fab09e74af81e0f3e75f0848b8fba158e626c8c73ae61dad3955305',[1,12,37]),
 ('main_menu_packed',13493,'ecb1b62eb141a28e9f3183636e651b33a45b70deb4fa74358408bff681216072',[1,12,36]),
 ('loading_screen',13488,'4dcd7f6a290a0f1aec308554d0252947b3359a56ea544118a1486ca82e10282f',[0,3]),
 ('loading_screen_packed',13488,'0bc6b26f578b76646e30e528de10260446f9fcc00e846f1f906a6902d418f3f9',[0,3]),
 ('character_gen_manager',417426,'d1963a864dd8246f799032b3b843a271a5d20b08fc8223ab54f3bd4d0f55ff32',[17]),
 ('MQ01',613082,'4f615429c46748631f2f525649e1450c4174e012deade93c11f60f5ff59758c4',[0,57])]
scripts=[]
for label,asset,h,indices in selection:
 d=P/'outputs/initial-corpus-drafts-v05/scripts'/h;m=json.loads((d/'metadata.json').read_text());j=json.loads((d/'ir.json').read_text())['root_function']
 target=O/'scripts'/label;target.mkdir(parents=True,exist_ok=True);(target/'metadata.json').write_bytes((d/'metadata.json').read_bytes())
 root=j['instructions'];root_hits=[]
 for i,instruction in enumerate(root):
  if any(s in instruction.get('constant_lua','') for s in ['m_gamestart_quest','m_CHEAT_START_SPACE']):
   root_hits += root[max(0,i-5):i+2]
 (target/'root-reference-instructions.json').write_text(json.dumps(root_hits,indent=2))
 names={};last=None
 for i in root:
  if i.get('kind')=='closure':last=i['child_index']
  elif i.get('kind')=='setglobal' and last is not None:names[last]=i.get('constant_lua');last=None
 for idx in indices:
  f=j['children'][idx];q=d/'functions'/('function_0_'+str(idx)+'.lua');out=target/q.name;out.write_bytes(q.read_bytes())
  compact=[{k:v for k,v in i.items() if k in ['pc','file_offset','word_hex','name','A','B','C','kind','constant_lua','left_operand','right_operand','successors']} for i in f['instructions']]
  dump(str((target/(q.stem+'.ir.json')).relative_to(O)),compact)
  scripts.append(dict(module=label,asset_id=asset,input_sha256=h,function_path=f['path'],function_name=names[idx],original_metadata=m,
   code_file=str(out.relative_to(O)),code_sha256=H(out.read_bytes()),instruction_count=len(f['instructions']),body_emittable=f.get('body_emittable')))
dump('script-provenance.json',scripts)
quest_defs=[]
for arch in ['initial_0.pak','patch_0.pak']:
 q=P/'work/v48-opening/script-audit/archive-source/inputs'/arch/'613083.quest_bxml';b=q.read_bytes();ptr,n=struct.unpack_from('<II',b,8+0x1c);ids=[struct.unpack_from('<I',b,ptr+56*i)[0] for i in range(n)]
 assert ids[0]==5 and 25 not in ids and len(ids)==len(set(ids))
 out=O/'source'/arch/q.name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b)
 quest_defs.append(dict(archive=arch,source=str(q.relative_to(P)),sha256=H(b),bytes=len(b),script_id=struct.unpack_from('<I',b,8+0x14)[0],stage_pointer_file_offset=8+0x1c,stage_data_file_offset=ptr,stage_record_bytes=56,authored_stage_ids=ids,
 native_runtime_prefix_stage_id=0,default_current_stage_index=-1))
dump('quest-definition-provenance.json',quest_defs)
sys.path.insert(0,str(P/'work/v44-native-fidelity/water-research/static-material-followup/hash-params'));import hash_name
assert hash_name.hash_name('win32')==585298
dump('source-start-contract.json',dict(
 quest_asset_id=613083,quest_script_asset_id=613082,space_asset_id=1417252,
 source_normal_start_chain=[
  'main_menu13493 root m_gamestart_quest=QUEST_ID(MQ01)',
  'main_menu.start_new_game: win32 platform585298 branch -> start_game_at_quest(m_gamestart_quest)',
  'start_game_at_quest -> QUEST.get_quest_script_module -> enter_space(module.m_CHEAT_START_SPACE,module.cheat_start_quest)',
  'enter_space -> loading_screen.create_loading_screen(space,callback)',
  'loading_screen.init(space,callback) DEFAULT branch validates type(callback)==function and stores m_cheat_func',
  'character_gen_manager417426.finish_character_gen: only after !m_wait_for_load and m_ready_for_finish gates -> loading_screen.m_cheat_func()',
  'MQ01.cheat_start_quest: QUEST.start_quest(MQ01); QUEST.set_stage(MQ01,5); set_game_start(true); Passive.set_disable_aggressive_mode(true); destiny_manager.lock_destiny(); destiny_manager.lock_fateweaver()'],
 stages=[
  dict(state='reference absent or asset unavailable to nonblocking query',get_stage=-1,native_bits='ffffffff',host_limit='An unmapped host quest is still unavailable; native sentinel is not permission to invent a source instance.'),
  dict(state='source-constructed loaded unstarted Quest',current_stage_index=-1,get_stage=-1,set_stage_25='No mutation/no activation; set_stage Lua binding returns no values.'),
  dict(state='successful source start_quest',current_stage_index=0,get_stage=0,meaning='Runtime synthesized stageID0, distinct from first authored5.'),
  dict(state='source creator-finish callback executes successful start then set5',current_stage_index=1,get_stage=5,meaning='Grounded normal-source stage after that callback, NOT constructor or automatic cinematic skip.'),
  dict(state='active MQ01 stage5 then set_stage25',get_stage_after=5,meaning='25 is absent BOTH exact definitions. Native exact-ID lookup returns unchanged, no stage activation/callbacks. Door opening is a separate effect.')],
 constructor_does_not_start=True,set_stage_does_not_start_unstarted=True,stage25_not_defined=True,
 mq01_on_start_stage5=dict(function_path='0/57',instruction_count=1,body='RETURN; no source Lua effects'),
 host_services_required=['start_quest/get_stage/set_stage with loaded-vs-unstarted/active semantics','set_game_start(true)','Passive disable-aggressive flag','destiny/fateweaver locks','native stage callbacks/condition/event effects where used'],
 explicit_limits=['No current user save/state observed or modified. Source startup proof is not proof the present dev skip ran creator completion.',
  'Original menu/loading/creator paths are statically reconstructed; guarded emitter equality domains are not broadened. Full creator/menu runtime execution is not claimed.',
  'Standalone main_menu matches current native win32-hash585298. Older packed menu compares platform enum3; preserve that variant difference, do not claim both platform guards are identical.',
  'Do not set5 on arbitrary host create/cinematic skipped/movement events. Trigger only the authorized counterpart of source successful creator finish.',
  'Known get_stage(-1) is an actual initialized-unstarted state; preserve missing/unsupported stage as unavailable separately.',
  'This audit stages no runtime or full native quest-manager emulator.'],
 platform=dict(native_enum=10,native_name='win32',native_hash=585298,hash_algorithm_source='00af09a0 tested helper',native_window_binding='00b513e0 -> 0103a510 ->0103a5f0 ->00af4d40')))

# Static consistency checks for the complete source route, not a simulated gameplay run.
checks=[]
def ck(name,c):assert c,name;checks.append(name)
lookup={(x['module'],x['function_path']):x for x in scripts}
for variant,path in [('main_menu','0/37'),('main_menu_packed','0/36')]:
 s=(O/lookup[(variant,path)]['code_file']).read_text()
 ck(variant+' normalNewGame route','"start_game_at_quest"' in s and '"m_gamestart_quest"' in s and ('585298' in s if variant=='main_menu' else True))
for variant in ['main_menu','main_menu_packed']:
 s=(O/lookup[(variant,'0/12')]['code_file']).read_text();ck(variant+' passes source callback','"cheat_start_quest"' in s and '"m_CHEAT_START_SPACE"' in s and '"enter_space"' in s)
for variant in ['loading_screen','loading_screen_packed']:
 s=(O/lookup[(variant,'0/3')]['code_file']).read_text();ck(variant+' stores function callback','["m_cheat_func"] = __r[1].value' in s and '"type"' in s)
s=(O/lookup[('character_gen_manager','0/17')]['code_file']).read_text()
ck('creator finish guarded source callback','"m_wait_for_load"' in s and '"m_ready_for_finish"' in s and s.count('"m_cheat_func"')==2)
s=(O/lookup[('MQ01','0/0')]['code_file']).read_text()
ck('MQ source call order',s.find('"start_quest"')<s.find('"set_stage"')<s.find('"set_game_start"'))
s=(O/'native/fn-00fefe00.c.txt').read_text();ck('native unstarted set guard','if (-1 < *(int *)(param_1 + 0x78))' in s)
s=(O/'native/fn-00fd9a00.c.txt').read_text();ck('native successful start setsindex0','*(undefined4 *)(param_1 + 0x78) = 0;' in s)
s=(O/'native/fn-00faeea0.c.txt').read_text();ck('native absent/unstarted sentinel','return 0xffffffff;' in s)
dump('validation.json',dict(result='PASS',static_consistency_checks=len(checks),checks=checks,quest_source_versions_preserved=True,gameplay_executed=False,native_executed=False))
print('SEALED INPUTS',len(scripts),'functions',len(natives),'native excerpts',len(checks),'checks','stages',quest_defs[0]['authored_stage_ids'])
