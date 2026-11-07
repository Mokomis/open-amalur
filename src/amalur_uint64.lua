-- Opaque carrier for Amalur's native type-11 packed values, not Lua numbers.
-- Reader evidence: koa.exe 16a400f6...09cb314, 0x010c13e1..0x010c13f1.
-- The native reader replaces the low nibble with 0xb; preserve raw bytes in IR.
-- This module models transport/identity only. Engine bindings need an adapter.
local lua_type, lua_error = type, error
local make_proxy, get_meta = newproxy, getmetatable
local lower, sub, match = string.lower, string.sub, string.match

if lua_type(make_proxy) ~= "function" then
  lua_error("Amalur type-11 carrier requires Lua 5.1 newproxy", 0)
end

-- Strong interning preserves identity throughout one reconstructed VM realm.
-- Every generated script and adapter in that realm must share this instance.
local interned, metadata = {}, {}
local module = {}

function module.from_hex(raw_hex)
  if lua_type(raw_hex) ~= "string" or #raw_hex ~= 16
      or not match(raw_hex, "^[0-9a-fA-F]+$") then
    lua_error("Amalur type-11 input must be exactly 16 hexadecimal characters", 2)
  end
  local canonical = sub(lower(raw_hex), 1, 15) .. "b"
  local token = interned[canonical]
  if token == nil then
    token = make_proxy(true)
    get_meta(token).__metatable = "Amalur type-11 opaque carrier v1"
    -- No arithmetic, ordering, equality, concatenation, or tostring metamethod.
    metadata[token] = canonical
    interned[canonical] = token
  end
  return token
end

local function is_token(value)
  return lua_type(value) == "userdata" and metadata[value] ~= nil
end
module.is = is_token

function module.hex(token)
  if not is_token(token) then
    lua_error("expected an Amalur type-11 token from this runtime instance", 2)
  end
  return metadata[token]
end

return module
