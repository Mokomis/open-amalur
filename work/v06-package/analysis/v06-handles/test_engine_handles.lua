-- Arguments: carrier factory and module. No native execution claim.
local new_carrier,module=...
local carrier=new_carrier();local handles=module.new(carrier)
local checks={}
local function check(name,f) f();checks[#checks+1]=name end
local function fails(f,pattern)
  local ok,err=pcall(f);assert(not ok and tostring(err):match(pattern),tostring(err))
end
check('quest full-width key roundtrip',function()
  for _,key in ipairs{0,1,2147483647,2147483648,4294967295} do
    local token=handles.from_key('quest',key);local info=handles.inspect(token)
    assert(info.kind=='quest' and info.key_u32==key and info.domain_u32==0x390)
    assert(info.native_tag==11 and info.native_low_u32==0x39b)
    assert(handles.quest_key(token)==key)
    local lo,hi=handles.to_words(token);assert(lo==0x39b and hi==key)
    assert(rawequal(handles.from_words(lo,hi),token))
  end
end)
check('space full-width key roundtrip',function()
  local token=handles.from_key('space',4294967295);local info=handles.inspect(token)
  assert(info.kind=='space' and info.canonical_hex=='ffffffff0000032b')
  assert(handles.space_key(token)==4294967295)
end)
check('domain retained and cannot silently cross',function()
  local quest=handles.from_key('quest',123);local space=handles.from_key('space',123)
  assert(not rawequal(quest,space))
  fails(function() handles.space_key(quest) end,'space handle')
  fails(function() handles.quest_key(space) end,'quest handle')
end)
check('unknown domain transport remains exact',function()
  local token=handles.from_words(0xfffffffB,0xffffffff);local info=handles.inspect(token)
  assert(info.kind==nil and info.domain_u32==0xfffffff0 and info.canonical_hex=='fffffffffffffffb')
  fails(function() handles.quest_key(token) end,'quest handle')
  fails(function() handles.from_key('actor',1) end,'Unconfirmed')
end)
check('ordinary values are not opaque handles',function()
  for _,value in ipairs{0,1,4294967295,'000000010000039b',false,{},function() end} do
    fails(function() handles.inspect(value) end,'token from this realm')
  end
  fails(function() handles.inspect(nil) end,'token from this realm')
end)
check('foreign realm is rejected',function()
  local foreign=new_carrier().from_hex('0000000100000390')
  fails(function() handles.quest_key(foreign) end,'token from this realm')
end)
check('invalid words and keys are rejected',function()
  for _,value in ipairs{-1,4294967296,0.5,math.huge,-math.huge,0/0,true,'1'} do
    fails(function() handles.from_key('quest',value) end,'unsigned 32')
    fails(function() handles.from_words(0x39b,value) end,'unsigned 32')
  end
  fails(function() handles.from_key('quest',nil) end,'unsigned 32')
  fails(function() handles.from_words(0x390,1) end,'retain type11')
end)
check('original serialized nibble is not invented',function()
  local a=carrier.from_hex('1234567800000390');local b=carrier.from_hex('123456780000039f')
  assert(rawequal(a,b) and handles.inspect(a).canonical_hex=='123456780000039b')
  assert(handles.inspect(a).serialized_hex==nil)
end)
check('adapter snapshots cannot switch realms',function()
  local own=new_carrier();local local_handles=module.new(own);local t=local_handles.from_key('space',7)
  own.from_hex=function() error('mutated') end;own.is=function() return false end;own.hex=function() return 'bad' end
  assert(local_handles.space_key(t)==7 and rawequal(local_handles.from_key('space',7),t))
end)
check('word ordering is explicit and exact',function()
  local token=handles.from_words(0x1234567b,0x89abcdef);local lo,hi=handles.to_words(token)
  assert(lo==0x1234567b and hi==0x89abcdef)
  assert(carrier.hex(token)=='89abcdef1234567b')
end)
return checks
