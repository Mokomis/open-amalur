"""Execute selected recovered Lua5.1 function bodies against explicit recording services.
This is branch/argument validation, not native gameplay or an engine implementation.
Unknown calls remain errors. No game process, saves, or live assets are used.
"""
from pathlib import Path
import sys,json,hashlib
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'tools/python-libs'))
from lupa.lua51 import LuaRuntime,LuaError
records={r['name']:r for r in json.loads((Q/'selected-script-provenance.json').read_text())}
results=[];checks=0
BASE=r'''
effects={}
function emit(name,...) effects[#effects+1]={name,...} end
function bind_state(name,s)
 local t={}
 for k,_ in pairs(s) do
  local key=k
  t["get_"..key]=function() return s[key] end
  t["set_"..key]=function(v) s[key]=v;emit("state",name,key,v) end
 end
 _G[name]=t;return t
end
PLAYER_ID=1;EQUIPPED=false;GATEWAY_OPEN=false;QUEST_STAGE=20;TUTORIALS_ENABLED=true
function get_player()return PLAYER_ID end
function QUEST_ID(n)assert(n=="MQ01");return 613083 end
function GOR_ID(n)return n end
TIME={delayed_function_call=function(...)emit("TIME.delayed_function_call",...)end}
QUEST={
 get_stage=function(q)assert(q==613083);return QUEST_STAGE end,
 set_stage=function(q,s)assert(q==613083);QUEST_STAGE=s;emit("QUEST.set_stage",q,s)end
}
PLAYER={is_equipped=function(i)return EQUIPPED end}
ACTOR={
 is_gateway_open=function(id)return GATEWAY_OPEN end,
 open_gateway=function(id)GATEWAY_OPEN=true;emit("ACTOR.open_gateway",id)end,
 unlock_object=function(id)emit("ACTOR.unlock_object",id)end,
 start_npc_to_npc_dialog=function(...)emit("ACTOR.start_npc_to_npc_dialog",...)end,
 start_player_ambient_dialog=function(...)emit("ACTOR.start_player_ambient_dialog",...)end
}
tutorial_win={
 get_tutorials_enabled=function()return TUTORIALS_ENABLED end,
 has_tutorial_fired=function(id)return false end,
 kill_tutorial=function(...)emit("tutorial_win.kill_tutorial",...)end,
 disable_secondary_weapon=function(...)emit("tutorial_win.disable_secondary_weapon",...)end,
 launch_modal_tutorial=function(...)emit("tutorial_win.launch_modal_tutorial",...)end,
 launch_tutorial=function(...)emit("tutorial_win.launch_tutorial",...)end
}
loot_popup={enable_compare=function()emit("loot_popup.enable_compare")end}
interfaceLibrary={autosave=function(...)emit("interfaceLibrary.autosave",...)end}
GAME={set_post_cinematic_player_loc_and_rot=function(...)emit("GAME.set_post_cinematic_player_loc_and_rot",...)end}
function DIALOG_ID(n)return n end
function SH(n)return n end
WOS_STATE={player_has_moved=false,player_has_looted=false,player_has_equipped=false,gave_player_equip_command=false}
SWORD_STATE={acquired_once=false,equipped_once=false,looked_at_target=false,attacked_once=false}
CINE_STATE={cinematic_finished=false}
MQ_STATE={sword_get=0}
COMBAT_STATE={event_started=false}
bind_state("WoS_Start_Room",WOS_STATE)
bind_state("Sword_WoS_InitialWeapon",SWORD_STATE)
bind_state("cinematic_post_char_gen_2",CINE_STATE)
bind_state("MQ01",MQ_STATE)
bind_state("WoS_FirstCombatRoom",COMBAT_STATE)
M_EQUIP_TUTORIAL_DELAY=15;M_DOOR_CHECKING_DELAY=15;M_DELAY_UNTIL_MOVE_HINT=5000
'''
def converted(v):
 if hasattr(v,'items'):
  pairs=list(v.items())
  if all(isinstance(k,(int,float)) and k>=1 and int(k)==k for k,_ in pairs):
   return [converted(v[i]) for i in range(1,len(pairs)+1)]
  return {str(k):converted(x) for k,x in pairs}
 return v
USE_ADAPTER='--accessor-adapter' in sys.argv
if USE_ADAPTER:
 start=BASE.index('function bind_state(name,s)')
 end=BASE.index('PLAYER_ID=',start)
 BASE=BASE[:start]+r'''function bind_state(name,s)
 local t={module_state=s};_G[name]=t
 ACCESSOR.install(t,function(message)emit("warning",message)end)
 for field,_ in pairs(s) do
  local key=field;local setter=t["set_"..key]
  t["set_"..key]=function(v)setter(v);emit("state",name,key,v)end
 end
 return t
end
'''+BASE[end:]
def new():
 l=LuaRuntime(unpack_returned_tuples=True,max_memory=64*1024*1024)
 if USE_ADAPTER:l.globals().ACCESSOR=l.execute((Q/'opening_state_accessors.lua').read_text())
 l.execute(BASE)
 # Bounded source-fixture execution only; engine calls are all Lua functions.
 l.execute("debug.sethook(function() error('fixture instruction budget') end,'',2000000)")
 return l
def fn(l,mod,index):
 p=Q/'evidence'/mod/'functions'/('function_0_'+str(index)+'.lua')
 s=p.read_text();assert records[mod]['sha256'] in s
 return l.execute(s)
def check(ok,why):
 global checks
 checks+=1
 assert ok,why
def effects(l):return converted(l.globals().effects)
def clear(l):l.execute('effects={}')
def setup_sword(l):
 l.globals().open_initial_door=fn(l,'Sword_WoS_InitialWeapon',4)
 l.globals().check_open_initial_door=fn(l,'Sword_WoS_InitialWeapon',3)
 return fn(l,'Sword_WoS_InitialWeapon',0),fn(l,'Sword_WoS_InitialWeapon',2)
# Exact post-char-gen placement.
l=new();fn(l,'cinematic_post_char_gen_2',0)()
check(effects(l)==[['GAME.set_post_cinematic_player_loc_and_rot',4312,2806,-314,-180]],'source cinematic location arguments')
check(l.globals().m_is_ready is True,'cinematic-ready set')
results.append({'scenario':'post-char-gen location','effects':effects(l)})
# First movement cannot checkpoint before cinematic completion and is once-only.
l=new();f=fn(l,'WoS_Start_Room',5);f();check(not effects(l),'no movement checkpoint before cinematic finished')
l.execute('CINE_STATE.cinematic_finished=true');f();e=effects(l)
check(e==[['state','WoS_Start_Room','player_has_moved',True],['tutorial_win.kill_tutorial',17524338],['tutorial_win.kill_tutorial',26339831],['interfaceLibrary.autosave',0]],'first movement exact effects')
clear(l);f();check(not effects(l),'first movement guard survives subsequent invocation')
results.append({'scenario':'first real movement after cinematic','effects':e})
# Door poll retains 15ms callback and passes original item argument after pickup.
l=new();acquire,equip=setup_sword(l);acquire(7,2,1);check(not effects(l),'nonplayer acquisition rejected')
l.execute('EQUIPPED=true');acquire(7,1,1);check(not effects(l),'already equipped acquisition path rejected')
l.execute('EQUIPPED=false');acquire(7,1,1);e=effects(l)
check(['TIME.delayed_function_call',151774118,15,7] in e,'equip prompt delay/item forwarding')
check(['TIME.delayed_function_call',165407883,15] in e,'door poll exact delay/hash')
check(l.globals().SWORD_STATE.acquired_once is True,'acquired_once set')
check(l.globals().WOS_STATE.player_has_looted is True,'looted state set')
check(['tutorial_win.disable_secondary_weapon',True] in e,'secondary lock request')
check(l.globals().QUEST_STAGE==20 and not l.globals().GATEWAY_OPEN,'pickup alone does not open gate')
clear(l);acquire(7,1,1);check(not effects(l),'repeated acquisition is idempotent')
equip(7);check(l.globals().SWORD_STATE.equipped_once is True,'equipped once state')
check(l.globals().WOS_STATE.player_has_equipped is True,'startroom equip state')
clear(l);l.globals().check_open_initial_door();e2=effects(l)
check(['ACTOR.open_gateway','MQ01_Start_Door_01'] in e2,'equipped door')
check(['QUEST.set_stage',613083,25] in e2,'stage20 ->25')
clear(l);l.globals().check_open_initial_door();check(not effects(l),'already-open gateway suppresses duplicate effects')
results.append({'scenario':'pickup then equip then door timer','pickup_effects':e,'door_effects':e2})
# Exact stage boundary and tutorial option behavior.
for stage in [-1,0,5,20,21,25,100]:
 for eq,enabled in [(False,True),(True,True),(False,False)]:
  l=new();setup_sword(l);l.globals().QUEST_STAGE=stage;l.globals().TUTORIALS_ENABLED=enabled;l.globals().SWORD_STATE.equipped_once=eq
  l.globals().check_open_initial_door();e=effects(l);opened=eq or not enabled
  check(l.globals().GATEWAY_OPEN==opened,'tutorial option/ever-equipped door predicate')
  check(l.globals().QUEST_STAGE==(25 if opened and stage<=20 else stage),'stage boundary never regresses later stage')
  if not opened:check(e==[['TIME.delayed_function_call',165407883,15]],'locked door only reschedules')
results.append({'scenario':'door boundary matrix','stages':[-1,0,5,20,21,25,100],'option_equipped_combinations':3})
# Prompt still appears before stage25 OR when explicit prior tutorial has not fired.
l=new();fn(l,'Sword_WoS_InitialWeapon',1)(7)
check(['tutorial_win.launch_modal_tutorial',49968583] in effects(l),'equip prompt tutorial exact ID')
check(l.globals().WOS_STATE.gave_player_equip_command is True,'equip command flag')
# Callback only reacts to entering player, then schedules one combat check150ms.
l=new();f=fn(l,'WoS_FirstCombatRoom',0);f(0,2,0,0,0);check(not effects(l),'nonplayer volume entry rejected')
f(0,1,0,0,0);e=effects(l);check(e==[['state','WoS_FirstCombatRoom','event_started',True],['TIME.delayed_function_call',59489868,150]],'first combat entry exact effects')
clear(l);f(0,1,0,0,0);check(not effects(l),'first combat entry once')
results.append({'scenario':'first combat volume entry','effects':e})
# Do not provide fake engine success: required unknown service must fail.
l=new();setup_sword(l);l.execute('SWORD_STATE.equipped_once=true;ACTOR.is_gateway_open=nil')
try:l.globals().check_open_initial_door()
except LuaError as e:check('Unmodeled Amalur callable domain' in str(e),'missing service must explicitly fail')
else:raise AssertionError('missing gateway service falsely succeeded')

# First combat distance/forced-call branches. Explicit fixtures simulate reads
# and record actual requested mutations, without implementing a game actor.
combat_setup=r"""
NEAR_ENEMIES=0;FIRED=false;UI_CONFIG=283690;PRIMARY_SIM=0;ACTIVE_SIM=0
M_COMBAT_HIT_DISTANCE=400;M_COMBAT_DISTANCE_HEARTBEAT=125
standardLibrary={num_enemies_in_radius=function(p,d)assert(p==1 and d==400);return NEAR_ENEMIES end}
function FACTION_ID(n)return n end
function SIMTYPE_KEY(n)assert(string.lower(n)=="sword_wos_initialweapon");return 1360571 end
function get_ui_config()return UI_CONFIG end
factionsLibrary={set_faction_hostile=function(...)emit("factionsLibrary.set_faction_hostile",...)end}
tutorial_win.has_tutorial_fired=function(id)assert(id==25608663);return FIRED end
PLAYER.get_equipped_object_from_equip_type_and_slot=function(k,s)assert(k=="Weapon" and s==0);return 100 end
PLAYER.get_item_index=function(id)assert(id==1360571);return 7 end
PLAYER.equip=function(...)emit("PLAYER.equip",...)end
ACTOR.get_actor_sim_type=function(o)if o==100 then return PRIMARY_SIM end;assert(o==200);return ACTIVE_SIM end
PlayerInput={get_player_active_weapon=function()return 200 end,switch_pc_weapon_mode=function()emit("PlayerInput.switch_pc_weapon_mode")end}
"""
for near,force,fired,enabled,ui,primary,active in [
 (0,False,False,True,283690,0,0),
 (0,True,False,True,283690,0,0),
 (1,False,False,True,283690,1360571,1360571),
 (1,False,True,True,283690,0,0),
 (1,False,False,False,283690,0,0),
 (1,False,False,True,0,0,0)]:
 l=new();l.execute(combat_setup);g=l.globals();g.NEAR_ENEMIES=near;g.FIRED=fired;g.TUTORIALS_ENABLED=enabled;g.UI_CONFIG=ui;g.PRIMARY_SIM=primary;g.ACTIVE_SIM=active
 fn(l,'WoS_FirstCombatRoom',1)(force);e=effects(l)
 if fired:check(not e,'already-fired combat prompt no reschedule')
 elif not(near>0 or force):check(e==[['TIME.delayed_function_call',59489868,125]],'no nearby enemy polls125')
 else:
  check(['factionsLibrary.set_faction_hostile','Player','Quest_MQ01_Rats'] in e,'source rat faction hostility')
  check((['tutorial_win.launch_modal_tutorial',25608663] in e)==enabled,'tutorial options stop prompt after hostility')
  check((['PLAYER.equip',7,0] in e)==(enabled and primary!=1360571),'source sword equip enforcement')
  check((['PlayerInput.switch_pc_weapon_mode'] in e)==(enabled and ui==283690 and active!=1360571),'PC weapon switch only')
 results.append({'scenario':'first combat check','inputs':dict(near=near,force=force,fired=fired,enabled=enabled,ui=ui,primary=primary,active=active),'effects':e})
# Original movement popup scheduling uses a500ms retry until cinematic-finished.
for finished in [False,True]:
 l=new();l.globals().CINE_STATE.cinematic_finished=finished;fn(l,'WoS_Start_Room',2)();e=effects(l)
 expected=[['TIME.delayed_function_call',44109305,2000,613083,'new'],['TIME.delayed_function_call',47850951,5000]] if finished else [['TIME.delayed_function_call',84278937,500]]
 check(e==expected,'exact cinematic-finished timer branches')
 results.append({'scenario':'movement-popup gate','cinematic_finished':finished,'effects':e})
# A missing late service does not roll back source guards: host must preflight
# services or supply transactional host policy before accepting gameplay events.
l=new();acquire,equip=setup_sword(l);l.execute('TIME.delayed_function_call=nil')
try:acquire(7,1,1)
except LuaError:
 check(l.globals().SWORD_STATE.acquired_once is True,'source guard remains changed after late service failure')
else:raise AssertionError('missing timer service falsely succeeded')
results.append({'scenario':'missing-service partial-state evidence','guard_changed_before_error':True,'requirement':'host readiness/preflight or explicit rollback policy'})

out={'passed':True,'checks':checks,'lua_version':'5.1','scope':'Original recovered function bodies with explicit recording fixtures; not native runtime equivalence or production services','unknown_engine_calls_fail':True,'source_functions':{k:records[k]['sha256'] for k in ['cinematic_post_char_gen_2','WoS_Start_Room','Sword_WoS_InitialWeapon','WoS_FirstCombatRoom']},'scenarios':results}
(Q/('original-function-accessor-results.json' if USE_ADAPTER else 'original-function-fixture-results.json')).write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'passed':True,'checks':checks,'scenarios':len(results)}))
