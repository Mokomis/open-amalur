"""Runnable first-room original-Lua bridge checks; no game/live files."""
from pathlib import Path
import sys,json,hashlib
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'tools/python-libs'))
from lupa.lua51 import LuaRuntime,LuaError
FUNCTIONS={
 'WoS_Start_Room.on_player_moved':('WoS_Start_Room',5),
 'WoS_Start_Room.on_leave_starting_room':('WoS_Start_Room',4),
 'WoS_Start_Room.on_volume_exit':('WoS_Start_Room',11),
 'Sword_WoS_InitialWeapon.on_item_acquired':('Sword_WoS_InitialWeapon',0),
 'Sword_WoS_InitialWeapon.launch_equip_tutorial':('Sword_WoS_InitialWeapon',1),
 'Sword_WoS_InitialWeapon.on_equip_item':('Sword_WoS_InitialWeapon',2),
 'Sword_WoS_InitialWeapon.check_open_initial_door':('Sword_WoS_InitialWeapon',3),
 'Sword_WoS_InitialWeapon.open_initial_door':('Sword_WoS_InitialWeapon',4)
}
records={r['name']:r for r in json.loads((Q/'selected-script-provenance.json').read_text())}
manifest=[]
for name,(mod,index) in FUNCTIONS.items():
 p=Q/'evidence'/mod/'functions'/('function_0_'+str(index)+'.lua')
 manifest.append({'name':name,'path':p.relative_to(Q).as_posix(),'function':'0/'+str(index),'original_input_sha256':records[mod]['sha256'],'generated_function_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(Q/'opening-function-manifest.json').write_text(json.dumps({'profile':'opening-first-room-original-lua-v1','functions':manifest},indent=2))
FIXTURE=r'''
EQUIPPED=false;GATEWAY=false;STAGE=5;ENABLED=true;REJECT=false
APPLIED={};WARNINGS={}
HOST={
 player_identity=function()return "scene1:player1:g1"end,
 resolve_gor=function(n)assert(n=="MQ01_Start_Door_01");return 1790948 end,
 resolve_quest=function(n)assert(n=="MQ01");return 613083 end,
 is_equipped=function(index)assert(index==7);return EQUIPPED end,
 is_gateway_open=function(id)assert(id==1790948);return GATEWAY end,
 get_quest_stage=function(id)assert(id==613083);return STAGE end,
 tutorials_enabled=function()return ENABLED end,
 has_tutorial_fired=function(id)return false end,
 is_tutorial_active=function(id)return false end,
 warn=function(m)WARNINGS[#WARNINGS+1]=m end,
 apply_effects=function(batch,candidate,event_name)
  CANDIDATE=candidate;EVENT_NAME=event_name
  if REJECT then return false,"fixture service unavailable"end
  for _,e in ipairs(batch)do
   -- Validate every command before applying ANY. This models the required
   -- host atomic acknowledgement contract, not an implemented game service.
   assert(e.name=="ACTOR.open_gateway" or e.name=="QUEST.set_stage" or
    e.name=="tutorial_win.kill_tutorial" or e.name=="tutorial_win.launch_modal_tutorial" or
    e.name=="tutorial_win.disable_secondary_weapon" or e.name=="loot_popup.enable_compare" or
    e.name=="interfaceLibrary.autosave_request","unimplemented fixture effect "..e.name)
  end
  for _,e in ipairs(batch)do
   APPLIED[#APPLIED+1]=e
   if e.name=="ACTOR.open_gateway"then GATEWAY=true end
   if e.name=="QUEST.set_stage"then STAGE=e.args[2]end
  end
  return true
 end
}
'''
checks=0
def ck(v,msg):
 global checks
 checks+=1;assert v,msg
def conv(x):
 if hasattr(x,'items'):
  ps=list(x.items())
  if ps and all(isinstance(k,int) and k>=1 for k,_ in ps) and {k for k,_ in ps}==set(range(1,len(ps)+1)):return [conv(x[i]) for i in range(1,len(ps)+1)]
  return {str(k):conv(v) for k,v in ps}
 return x
def make():
 l=LuaRuntime(unpack_returned_tuples=True,max_memory=64*1024*1024)
 l.execute("debug.sethook(function()error('bridge test instruction budget')end,'',2000000)")
 l.execute(FIXTURE);g=l.globals();g.ACCESSORS=l.execute((Q/'opening_state_accessors.lua').read_text());g.BRIDGE=l.execute((Q/'opening_bridge.lua').read_text())
 functions=l.table()
 for row in manifest:
  raw=(Q/row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['generated_function_sha256']
  functions[row['name']]=l.execute(raw.decode())
 g.FUNCTIONS=functions
 bridge=g.BRIDGE.new(functions,g.HOST,l.table_from({'accessors':g.ACCESSORS}))
 return l,bridge
def success(r):return r is True or isinstance(r,tuple) and r[0] is True
def failure(r):return isinstance(r,tuple) and r[0] is False
l,b=make();g=l.globals()
ck(success(b.volume_exit('Tutorial_Volume_Move','scene1:player1:g1')),'pre-cinematic ignored')
ck(len(g.APPLIED)==0,'pre-cinematic no checkpoint')
ck(success(b.set_cinematic_finished(True)),'explicit cinematic completion')
ck(success(b.volume_exit('Tutorial_Volume_Move','other:g1')),'nonplayer volume ignored')
ck(len(g.APPLIED)==0,'nonplayer no checkpoint')
ck(success(b.volume_exit('UnknownVolume','scene1:player1:g1')),'unknown volume follows original ignore')
ck(success(b.volume_exit('Tutorial_Volume_Move','scene1:player1:g1')),'source movement volume exit')
ck([g.APPLIED[i].name for i in range(1,len(g.APPLIED)+1)]==['tutorial_win.kill_tutorial','tutorial_win.kill_tutorial','interfaceLibrary.autosave_request'],'movement effects ordered')
ck(g.APPLIED[1].args[1]==17524338 and g.APPLIED[2].args[1]==26339831,'movement exact tutorial IDs')
ck(g.APPLIED[3].args[1]==0,'checkpoint request exact argument')
ck(g.CANDIDATE.modules.WoS_Start_Room.player_has_moved is True and g.EVENT_NAME=='WoS_Start_Room.on_volume_exit','host receives coherent candidate snapshot without reentry')
ck(success(b.volume_exit('Tutorial_Volume_Move2','scene1:player1:g1')),'second move volume')
ck(len(g.APPLIED)==3,'checkpoint once across both source volumes')
ck(success(b.sword_acquired(7,'other:g1',1)),'nonplayer item ignored')
ck(len(b.snapshot().timers)==0,'nonplayer no timers')
ck(success(b.sword_acquired(7,'scene1:player1:g1',1)),'first actual sword pickup')
s=b.snapshot();ck(s.modules.Sword_WoS_InitialWeapon.acquired_once is True,'pickup guard persisted')
ck(s.modules.WoS_Start_Room.player_has_looted is True and s.modules.MQ01.sword_get==1,'source pickup state changes')
ck(len(s.timers)==2,'two exact source timers')
ck({s.timers[i].hash for i in [1,2]}=={151774118,165407883},'closed timer map')
ck(success(b.advance(14)),'before source15 delay');ck(not g.GATEWAY,'pickup does not open door')
ck(success(b.advance(1)),'equip hint and first door check')
ck(any(g.APPLIED[i].name=='tutorial_win.launch_modal_tutorial' and g.APPLIED[i].args[1]==49968583 for i in range(1,len(g.APPLIED)+1)),'original equip modal')
ck(not g.GATEWAY and g.STAGE==5,'still closed without equip')
ck(len(b.snapshot().timers)==1 and b.snapshot().timers[1].due_ms==30,'door repolls15 after frame clock')
g.EQUIPPED=True;ck(success(b.sword_equipped(7)),'real inventory equip event')
ck(success(b.advance(15)),'door timer after equip')
ck(g.GATEWAY is True and g.STAGE==25,'real acknowledged door/stage effects')
ck(len(b.snapshot().timers)==0,'door poll stops after successful open')
main_trace=conv(g.APPLIED)
# Rejected host side effects leave all guards/timers retryable.
l,b=make();g=l.globals();b.set_cinematic_finished(True);g.REJECT=True
r=b.volume_exit('Tutorial_Volume_Move','scene1:player1:g1');ck(failure(r),'checkpoint service reject propagated')
ck(b.snapshot().modules.WoS_Start_Room.player_has_moved is False,'movement state rollback')
g.REJECT=False;ck(success(b.volume_exit('Tutorial_Volume_Move','scene1:player1:g1')),'retry same source event after service ready')
g.REJECT=True;r=b.sword_acquired(7,'scene1:player1:g1',1);ck(failure(r),'inventory/tutorial effect reject')
ck(b.snapshot().modules.Sword_WoS_InitialWeapon.acquired_once is False and len(b.snapshot().timers)==0,'pickup guard/timers rolled back')
# Snapshot/restore, corrupt timers rejected before mutation.
l,b=make();g=l.globals();b.set_cinematic_finished(True);b.sword_acquired(7,'scene1:player1:g1',1);s=b.snapshot()
ck(success(b.restore(s)),'coherent checkpoint restores')
bad=l.eval('function(s)local t={};for k,v in pairs(s)do t[k]=v end;t.profile="bad";return t end')(s)
ck(failure(b.restore(bad)),'wrong snapshot profile rejected')
bad=b.snapshot();bad.timers[1].hash=123;ck(failure(b.restore(bad)),'unknown callback hash rejected')
ck(b.snapshot().timers[1].hash==151774118,'bad restore preserved original queue')
bad=b.snapshot();bad.modules.Sword_WoS_InitialWeapon.acquired_once=1;ck(failure(b.restore(bad)),'typed source state restore rejected')
ck(b.snapshot().modules.Sword_WoS_InitialWeapon.acquired_once is True,'bad typed restore atomic')
bad=b.snapshot();bad.modules.MQ01.sword_get=float('nan');ck(failure(b.restore(bad)),'nonfinite numeric state rejected')
# Missing/unknown stage does not silently advance the quest; due timer retained.
g.EQUIPPED=True;b.sword_equipped(7);g.HOST.get_quest_stage=l.eval('function(id)return nil end')
r=b.advance(15);ck(failure(r),'unknown quest stage fails')
ck(not g.GATEWAY,'buffered gateway effect not applied before late query failure')
ck(len(b.snapshot().timers)==1 and b.snapshot().timers[1].hash==165407883,'failed door callback retained; prior successful equip-check callback committed')
# Constructor requires an implementation for every named service.
l,b=make();g=l.globals();g.HOST.apply_effects=None
try:g.BRIDGE.new(g.FUNCTIONS,g.HOST,l.table_from({'accessors':g.ACCESSORS}))
except LuaError as e:ck('host service missing: apply_effects' in str(e),'missing effect service explicit')
else:raise AssertionError('missing service silently succeeded')
out={'passed':True,'checks':checks,'source_functions':len(manifest),'scope':'Original Lua first-room callbacks via authored explicit bridge, simulated acknowledged host services; no game/live/user-state execution','main_route_effects':main_trace,'unknowns_fail':True,'transactional_internal_state':True,'clock_policy':'Monotonic paused-game milliseconds supplied by host; newly scheduled timers run from current frame time; native scheduler/pause behavior not claimed.'}
(Q/'opening-bridge-fixture-results.json').write_text(json.dumps(out,indent=2));print(json.dumps({'passed':True,'checks':checks,'source_functions':len(manifest)}))
