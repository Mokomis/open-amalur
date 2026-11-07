-- Portable host integration: exact nil count, type11 realm, native math domain,
-- and explicit failures for unimplemented engine services. No gameplay claim.
assert(getmetatable(_G)==nil and getmetatable(QUEST)==nil and getmetatable(GAME)==nil)
assert(io==nil and os==nil and debug==nil and package==nil and coroutine==nil)
local carrier,handles=__amalur_uint64,__amalur_handles
local token=handles.from_key('quest',4294967295)
assert(carrier.hex(token)=='ffffffff0000039b')
assert(handles.quest_key(token)==4294967295)
assert(token==carrier.from_hex('ffffffff00000390'))
assert(math.abs(-2147483648)==-2147483648)
assert(math.sqrt(2147395600)==-1)
assert(math.pow(65537,2)==131073)
local ok,message=pcall(QUEST.get_stage,token)
assert(not ok and tostring(message):find('unimplemented Amalur engine binding: QUEST.get_stage',1,true))
local marker={}
local failed,original=pcall(function()error(marker)end)
assert(not failed and rawequal(original,marker))
local a,b,c,d=pcall(function()return nil,7,nil end)
assert(a and b==nil and c==7 and d==nil)
local x,y,z=xpcall(function()return 7,nil end,function(e)return e end)
assert(x and y==7 and z==nil)
local failed,transformed=xpcall(function()error('original')end,function(e)return 'transformed' end)
assert(not failed and transformed=='transformed')
return nil,token,7,false,nil
