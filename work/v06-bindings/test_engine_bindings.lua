-- Run with the same Lua 5.1 realm and uint64 carrier as the recovered scripts.
local bridge, registry, carrier = ...
local function pack(...) return {n=select('#', ...), ...} end
local function fails_with(fn, fragment)
  local ok, err = pcall(fn)
  assert(not ok and tostring(err):find(fragment, 1, true), tostring(err))
end
local checks, args, called = 0, nil, 0
local marker = {}
local token = carrier.from_hex('0102030400000390')
local provider = {QUEST={get_stage=function(...)
  called=called+1; args=pack(...); return nil, token, 7, nil
end, set_stage=function() error(marker, 0) end}}
local global_before = rawget(_G, 'QUEST')
local env = bridge.new(registry, provider)
assert(rawget(_G, 'QUEST') == global_before)
assert(getmetatable(env)==nil and getmetatable(env.QUEST)==nil)
assert(called==0); checks=checks+1
local results=pack(env.QUEST.get_stage(token, nil, 3, nil))
assert(args.n==4 and args[1]==token and args[2]==nil and args[3]==3 and args[4]==nil)
assert(results.n==4 and results[1]==nil and results[2]==token and results[3]==7 and results[4]==nil)
assert(carrier.hex(results[2])=='010203040000039b'); checks=checks+1
fails_with(function() env.QUEST.get_num_stages(token) end, 'unimplemented Amalur engine binding: QUEST.get_num_stages')
assert(called==1); checks=checks+1
local ok, err=pcall(env.QUEST.set_stage, token, 1)
assert(not ok and rawequal(err, marker)); checks=checks+1
provider.QUEST.get_stage=function() error('mutated provider used') end
env.QUEST.get_stage(token)
assert(called==2); checks=checks+1
local env2=bridge.new(registry, {})
assert(env2~=env and env2.QUEST~=env.QUEST)
fails_with(function() env2.QUEST.get_stage(token) end, 'unimplemented Amalur engine binding')
assert(provider.QUEST.get_num_stages==nil); checks=checks+1
fails_with(function() bridge.new(registry, {QUEST={not_registered=function() end}}) end, 'unregistered binding')
fails_with(function() bridge.new(registry, {NOT_REGISTERED={}}) end, 'unregistered namespace')
fails_with(function() bridge.new(registry, {QUEST={get_stage=7}}) end, 'must supply a function')
fails_with(function() bridge.new(registry, setmetatable({}, {})) end, 'must be a plain table')
checks=checks+1
return {passed=checks, native_behavior_claim=false, scope='Provider plumbing only: nil counts, token identity, missing implementation, error propagation, snapshots, realm isolation, invalid providers'}
