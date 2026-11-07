-- Exact type11 marshaling for native-confirmed QUEST and GAME space handles.
-- This module does not implement engine queries, object lookup, or coercion.
-- All values below are separate exact 32-bit words; no 64-bit Lua number exists.
local type, error = type, error
local sub, match = string.sub, string.match
local digits='0123456789abcdef'
local domains={quest=0x390,space=0x320}
local names={[0x390]='quest',[0x320]='space'}
local function u32(value)
  if type(value)~='number' or value~=value or value<0 or value>4294967295 or value%1~=0 then
    error('Amalur handle word must be an exact unsigned 32-bit integer',3)
  end
  return value==0 and 0 or value
end
local function encode(value)
  value=u32(value)
  local out=''
  for i=1,8 do local digit=value%16;out=sub(digits,digit+1,digit+1)..out;value=(value-digit)/16 end
  return out
end
local function decode(raw)
  local value=0
  for i=1,8 do
    local c=sub(raw,i,i);local digit
    for n=1,16 do if sub(digits,n,n)==c then digit=n-1;break end end
    if digit==nil then error('Invalid canonical Amalur handle hex',3) end
    value=value*16+digit
  end
  return value
end
local module={}
function module.new(carrier)
  if type(carrier)~='table' or type(carrier.from_hex)~='function' or type(carrier.is)~='function' or type(carrier.hex)~='function' then
    error('A shared Amalur type11 carrier is required',2)
  end
  -- Capture the carrier methods so later table mutation cannot switch realms.
  local from_hex,is_token,get_hex=carrier.from_hex,carrier.is,carrier.hex
  local result={}
  local function raw_of(token)
    if type(token)~='userdata' or not is_token(token) then error('Expected an Amalur handle token from this realm',3) end
    local raw=get_hex(token)
    if type(raw)~='string' or #raw~=16 or not match(raw,'^[0-9a-f]+$') or sub(raw,16,16)~='b' then
      error('Invalid canonical Amalur type11 carrier',3)
    end
    return raw
  end
  function result.to_words(token)
    local raw=raw_of(token)
    return decode(sub(raw,9,16)),decode(sub(raw,1,8))
  end
  function result.from_words(low,high)
    low=u32(low);high=u32(high)
    if low%16~=11 then error('Native Amalur handle word must retain type11 tag',2) end
    local raw=encode(high)..encode(low)
    local token=from_hex(raw)
    if raw_of(token)~=raw then error('Carrier changed native Amalur handle bits',2) end
    return token
  end
  function result.inspect(token)
    local raw=raw_of(token);local low,high=result.to_words(token);local domain=low-11
    return {kind=names[domain],key_u32=high,key_hex=sub(raw,1,8),
            domain_u32=domain,native_low_u32=low,native_high_u32=high,
            canonical_hex=raw,native_tag=11}
  end
  function result.from_key(kind,key)
    local domain=domains[kind]
    if not domain then error('Unconfirmed Amalur handle domain',2) end
    return result.from_words(domain+11,u32(key))
  end
  function result.quest_key(token)
    local info=result.inspect(token)
    if info.domain_u32~=domains.quest then error('Expected a typed Amalur quest handle',2) end
    return info.key_u32
  end
  function result.space_key(token)
    local info=result.inspect(token)
    if info.domain_u32~=domains.space then error('Expected a typed Amalur space handle',2) end
    return info.key_u32
  end
  return result
end
return module
