-- Generated on Windows from native-compared real function cases.
-- Isolated primitive function coverage only, not whole-game behavior.
local function pack(...) return {n=select('#',...),...} end
local passed=0
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==1,'result count case 0')
assert(result[1]==true,'result value case 0 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==1,'result count case 1')
assert(result[1]==true,'result value case 1 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==1,'result count case 2')
assert(result[1]==true,'result value case 2 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==1,'result count case 3')
assert(result[1]==true,'result value case 3 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==1,'result count case 4')
assert(result[1]==true,'result value case 4 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = false
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==1,'result count case 5')
assert(result[1]==false,'result value case 5 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = false
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==1,'result count case 6')
assert(result[1]==false,'result value case 6 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = false
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==1,'result count case 7')
assert(result[1]==false,'result value case 7 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = false
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==1,'result count case 8')
assert(result[1]==false,'result value case 8 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = false
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==1,'result count case 9')
assert(result[1]==false,'result value case 9 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __loops = {}
  local function __integer(value)
    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end
    return value == 0 and 0 or value
  end
  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end
  local function __multiply(left, right)
    left=left%4294967296; right=right%4294967296
    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536
    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)
  end
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: MUL
      local __left, __right = __integer(__r[0].value), __integer(100000)
      __r[1].value = __multiply(__left,__right)
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==1,'result count case 10')
assert(result[1]==100000,'result value case 10 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __loops = {}
  local function __integer(value)
    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end
    return value == 0 and 0 or value
  end
  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end
  local function __multiply(left, right)
    left=left%4294967296; right=right%4294967296
    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536
    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)
  end
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: MUL
      local __left, __right = __integer(__r[0].value), __integer(100000)
      __r[1].value = __multiply(__left,__right)
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==1,'result count case 11')
assert(result[1]==-100000,'result value case 11 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __loops = {}
  local function __integer(value)
    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end
    return value == 0 and 0 or value
  end
  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end
  local function __multiply(left, right)
    left=left%4294967296; right=right%4294967296
    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536
    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)
  end
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: MUL
      local __left, __right = __integer(__r[0].value), __integer(100000)
      __r[1].value = __multiply(__left,__right)
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==1,'result count case 12')
assert(result[1]==700000,'result value case 12 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __loops = {}
  local function __integer(value)
    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end
    return value == 0 and 0 or value
  end
  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end
  local function __multiply(left, right)
    left=left%4294967296; right=right%4294967296
    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536
    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)
  end
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: MUL
      local __left, __right = __integer(__r[0].value), __integer(100000)
      __r[1].value = __multiply(__left,__right)
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==1,'result count case 13')
assert(result[1]==0,'result value case 13 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __loops = {}
  local function __integer(value)
    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end
    return value == 0 and 0 or value
  end
  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end
  local function __multiply(left, right)
    left=left%4294967296; right=right%4294967296
    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536
    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)
  end
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: MUL
      local __left, __right = __integer(__r[0].value), __integer(100000)
      __r[1].value = __multiply(__left,__right)
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==1,'result count case 14')
assert(result[1]==0,'result value case 14 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function()
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = nil}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[0].value = 500
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)())
assert(result.n==1,'result count case 15')
assert(result[1]==500,'result value case 15 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function()
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = nil}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[0].value = 2
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)())
assert(result.n==1,'result count case 16')
assert(result[1]==2,'result value case 16 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function()
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = nil}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[0].value = 50
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)())
assert(result.n==1,'result count case 17')
assert(result[1]==50,'result value case 17 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==0,'result count case 18')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==0,'result count case 19')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==0,'result count case 20')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==0,'result count case 21')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[1].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==0,'result count case 22')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function()
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = nil}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[0].value = 0
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)())
assert(result.n==1,'result count case 23')
assert(result[1]==0,'result value case 23 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function()
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = nil}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[0].value = true
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)())
assert(result.n==1,'result count case 24')
assert(result[1]==true,'result value case 24 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0, r1)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = r1}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: TEST
      if (not not __r[1].value) == true then
        __pc = 3
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: RETURN
      return
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1,1))
assert(result.n==0,'result count case 25')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0, r1)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = r1}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: TEST
      if (not not __r[1].value) == true then
        __pc = 3
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: RETURN
      return
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1,-1))
assert(result.n==0,'result count case 26')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0, r1)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = r1}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: TEST
      if (not not __r[1].value) == true then
        __pc = 3
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: RETURN
      return
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7,3))
assert(result.n==0,'result count case 27')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0, r1)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = r1}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: TEST
      if (not not __r[1].value) == true then
        __pc = 3
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: RETURN
      return
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0,0))
assert(result.n==0,'result count case 28')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0, r1)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = r1}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: TEST
      if (not not __r[1].value) == true then
        __pc = 3
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: RETURN
      return
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648,2147483647))
assert(result.n==0,'result count case 29')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0, r1)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = r1}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: TEST
      if (not not __r[0].value) == true then
        __pc = 3
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: RETURN
      return
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1,1))
assert(result.n==0,'result count case 30')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0, r1)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = r1}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: TEST
      if (not not __r[0].value) == true then
        __pc = 3
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: RETURN
      return
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1,-1))
assert(result.n==0,'result count case 31')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0, r1)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = r1}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: TEST
      if (not not __r[0].value) == true then
        __pc = 3
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: RETURN
      return
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7,3))
assert(result.n==0,'result count case 32')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0, r1)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = r1}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: TEST
      if (not not __r[0].value) == true then
        __pc = 3
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: RETURN
      return
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0,0))
assert(result.n==0,'result count case 33')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0, r1)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = r1}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: TEST
      if (not not __r[0].value) == true then
        __pc = 3
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: RETURN
      return
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648,2147483647))
assert(result.n==0,'result count case 34')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==1,'result count case 35')
assert(result[1]==1,'result value case 35 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==1,'result count case 36')
assert(result[1]==-1,'result value case 36 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==1,'result count case 37')
assert(result[1]==7,'result value case 37 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==1,'result count case 38')
assert(result[1]==0,'result value case 38 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==1,'result count case 39')
assert(result[1]==-2147483648,'result value case 39 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==0,'result count case 40')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==0,'result count case 41')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==0,'result count case 42')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==0,'result count case 43')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: RETURN
      return
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==0,'result count case 44')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 0
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==1,'result count case 45')
assert(result[1]==0,'result value case 45 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 0
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==1,'result count case 46')
assert(result[1]==0,'result value case 46 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 0
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==1,'result count case 47')
assert(result[1]==0,'result value case 47 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 0
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==1,'result count case 48')
assert(result[1]==0,'result value case 48 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 0
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==1,'result count case 49')
assert(result[1]==0,'result value case 49 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: EQ
      local __left, __right = __r[0].value, 364433
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 5
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: LOADK
      __r[1].value = 100
      __pc = 3
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return __r[1].value
    elseif __pc == 5 then
      -- file 0x114: EQ
      local __left, __right = __r[0].value, 717147
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 10
      else
        __pc = 7
      end
    elseif __pc == 7 then
      -- file 0x11c: LOADK
      __r[1].value = 25
      __pc = 8
    elseif __pc == 8 then
      -- file 0x120: RETURN
      return __r[1].value
    elseif __pc == 10 then
      -- file 0x128: EQ
      local __left, __right = __r[0].value, 4373355
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 14
      else
        __pc = 12
      end
    elseif __pc == 12 then
      -- file 0x130: LOADK
      __r[1].value = 50
      __pc = 13
    elseif __pc == 13 then
      -- file 0x134: RETURN
      return __r[1].value
    elseif __pc == 14 then
      -- file 0x138: LOADK
      __r[1].value = 100
      __pc = 15
    elseif __pc == 15 then
      -- file 0x13c: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==1,'result count case 50')
assert(result[1]==100,'result value case 50 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: EQ
      local __left, __right = __r[0].value, 364433
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 5
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: LOADK
      __r[1].value = 100
      __pc = 3
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return __r[1].value
    elseif __pc == 5 then
      -- file 0x114: EQ
      local __left, __right = __r[0].value, 717147
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 10
      else
        __pc = 7
      end
    elseif __pc == 7 then
      -- file 0x11c: LOADK
      __r[1].value = 25
      __pc = 8
    elseif __pc == 8 then
      -- file 0x120: RETURN
      return __r[1].value
    elseif __pc == 10 then
      -- file 0x128: EQ
      local __left, __right = __r[0].value, 4373355
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 14
      else
        __pc = 12
      end
    elseif __pc == 12 then
      -- file 0x130: LOADK
      __r[1].value = 50
      __pc = 13
    elseif __pc == 13 then
      -- file 0x134: RETURN
      return __r[1].value
    elseif __pc == 14 then
      -- file 0x138: LOADK
      __r[1].value = 100
      __pc = 15
    elseif __pc == 15 then
      -- file 0x13c: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==1,'result count case 51')
assert(result[1]==100,'result value case 51 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: EQ
      local __left, __right = __r[0].value, 364433
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 5
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: LOADK
      __r[1].value = 100
      __pc = 3
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return __r[1].value
    elseif __pc == 5 then
      -- file 0x114: EQ
      local __left, __right = __r[0].value, 717147
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 10
      else
        __pc = 7
      end
    elseif __pc == 7 then
      -- file 0x11c: LOADK
      __r[1].value = 25
      __pc = 8
    elseif __pc == 8 then
      -- file 0x120: RETURN
      return __r[1].value
    elseif __pc == 10 then
      -- file 0x128: EQ
      local __left, __right = __r[0].value, 4373355
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 14
      else
        __pc = 12
      end
    elseif __pc == 12 then
      -- file 0x130: LOADK
      __r[1].value = 50
      __pc = 13
    elseif __pc == 13 then
      -- file 0x134: RETURN
      return __r[1].value
    elseif __pc == 14 then
      -- file 0x138: LOADK
      __r[1].value = 100
      __pc = 15
    elseif __pc == 15 then
      -- file 0x13c: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==1,'result count case 52')
assert(result[1]==100,'result value case 52 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: EQ
      local __left, __right = __r[0].value, 364433
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 5
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: LOADK
      __r[1].value = 100
      __pc = 3
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return __r[1].value
    elseif __pc == 5 then
      -- file 0x114: EQ
      local __left, __right = __r[0].value, 717147
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 10
      else
        __pc = 7
      end
    elseif __pc == 7 then
      -- file 0x11c: LOADK
      __r[1].value = 25
      __pc = 8
    elseif __pc == 8 then
      -- file 0x120: RETURN
      return __r[1].value
    elseif __pc == 10 then
      -- file 0x128: EQ
      local __left, __right = __r[0].value, 4373355
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 14
      else
        __pc = 12
      end
    elseif __pc == 12 then
      -- file 0x130: LOADK
      __r[1].value = 50
      __pc = 13
    elseif __pc == 13 then
      -- file 0x134: RETURN
      return __r[1].value
    elseif __pc == 14 then
      -- file 0x138: LOADK
      __r[1].value = 100
      __pc = 15
    elseif __pc == 15 then
      -- file 0x13c: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==1,'result count case 53')
assert(result[1]==100,'result value case 53 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: EQ
      local __left, __right = __r[0].value, 364433
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 5
      else
        __pc = 2
      end
    elseif __pc == 2 then
      -- file 0x108: LOADK
      __r[1].value = 100
      __pc = 3
    elseif __pc == 3 then
      -- file 0x10c: RETURN
      return __r[1].value
    elseif __pc == 5 then
      -- file 0x114: EQ
      local __left, __right = __r[0].value, 717147
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 10
      else
        __pc = 7
      end
    elseif __pc == 7 then
      -- file 0x11c: LOADK
      __r[1].value = 25
      __pc = 8
    elseif __pc == 8 then
      -- file 0x120: RETURN
      return __r[1].value
    elseif __pc == 10 then
      -- file 0x128: EQ
      local __left, __right = __r[0].value, 4373355
      local __lt, __rt = __type(__left), __type(__right)
      if not ((__lt == "nil" or __lt == "boolean" or __lt == "string" or (__lt == "number" and __left >= -2147483648 and __left <= 2147483647 and __left % 1 == 0)) and (__rt == "nil" or __rt == "boolean" or __rt == "string" or (__rt == "number" and __right >= -2147483648 and __right <= 2147483647 and __right % 1 == 0))) then __unresolved("Unmodeled Amalur comparison domain") end
      if (__left == __right) == false then
        __pc = 14
      else
        __pc = 12
      end
    elseif __pc == 12 then
      -- file 0x130: LOADK
      __r[1].value = 50
      __pc = 13
    elseif __pc == 13 then
      -- file 0x134: RETURN
      return __r[1].value
    elseif __pc == 14 then
      -- file 0x138: LOADK
      __r[1].value = 100
      __pc = 15
    elseif __pc == 15 then
      -- file 0x13c: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==1,'result count case 54')
assert(result[1]==100,'result value case 54 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 110
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==1,'result count case 55')
assert(result[1]==110,'result value case 55 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 110
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==1,'result count case 56')
assert(result[1]==110,'result value case 56 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 110
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==1,'result count case 57')
assert(result[1]==110,'result value case 57 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 110
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==1,'result count case 58')
assert(result[1]==110,'result value case 58 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 110
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==1,'result count case 59')
assert(result[1]==110,'result value case 59 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 2821100
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==1,'result count case 60')
assert(result[1]==2821100,'result value case 60 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 2821100
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==1,'result count case 61')
assert(result[1]==2821100,'result value case 61 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 2821100
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==1,'result count case 62')
assert(result[1]==2821100,'result value case 62 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 2821100
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==1,'result count case 63')
assert(result[1]==2821100,'result value case 63 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADK
      __r[1].value = 2821100
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==1,'result count case 64')
assert(result[1]==2821100,'result value case 64 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function()
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = nil}, [1] = {value = nil}}
  local __top
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: LOADBOOL
      __r[0].value = false
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[0].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)())
assert(result.n==1,'result count case 65')
assert(result[1]==false,'result value case 65 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __loops = {}
  local function __integer(value)
    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end
    return value == 0 and 0 or value
  end
  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end
  local function __multiply(left, right)
    left=left%4294967296; right=right%4294967296
    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536
    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)
  end
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: MUL
      local __left, __right = __integer(__r[0].value), __integer(10000)
      __r[1].value = __multiply(__left,__right)
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(1))
assert(result.n==1,'result count case 66')
assert(result[1]==10000,'result value case 66 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __loops = {}
  local function __integer(value)
    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end
    return value == 0 and 0 or value
  end
  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end
  local function __multiply(left, right)
    left=left%4294967296; right=right%4294967296
    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536
    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)
  end
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: MUL
      local __left, __right = __integer(__r[0].value), __integer(10000)
      __r[1].value = __multiply(__left,__right)
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-1))
assert(result.n==1,'result count case 67')
assert(result[1]==-10000,'result value case 67 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __loops = {}
  local function __integer(value)
    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end
    return value == 0 and 0 or value
  end
  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end
  local function __multiply(left, right)
    left=left%4294967296; right=right%4294967296
    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536
    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)
  end
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: MUL
      local __left, __right = __integer(__r[0].value), __integer(10000)
      __r[1].value = __multiply(__left,__right)
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(7))
assert(result.n==1,'result count case 68')
assert(result[1]==70000,'result value case 68 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __loops = {}
  local function __integer(value)
    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end
    return value == 0 and 0 or value
  end
  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end
  local function __multiply(left, right)
    left=left%4294967296; right=right%4294967296
    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536
    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)
  end
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: MUL
      local __left, __right = __integer(__r[0].value), __integer(10000)
      __r[1].value = __multiply(__left,__right)
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(0))
assert(result.n==1,'result count case 69')
assert(result[1]==0,'result value case 69 slot 1')
passed=passed+1
end
do
local result=pack((function(...)
-- Opem Amalur: initial register-level Lua 5.1 reconstruction.
-- Input SHA-256: 0000000000000000000000000000000000000000000000000000000000000000
-- Static interpretation; not original source or runtime-equivalence proof.
-- Unresolved function bodies are explicit error stubs, never silent no-ops.
-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.
local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable

return (function(r0)
  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.
  local __r = {[0] = {value = r0}, [1] = {value = nil}}
  local __top
  local __loops = {}
  local function __integer(value)
    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end
    return value == 0 and 0 or value
  end
  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end
  local function __multiply(left, right)
    left=left%4294967296; right=right%4294967296
    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536
    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)
  end
  local __pc = 0
  while true do
    if __pc == 0 then
      -- file 0x100: MUL
      local __left, __right = __integer(__r[0].value), __integer(10000)
      __r[1].value = __multiply(__left,__right)
      __pc = 1
    elseif __pc == 1 then
      -- file 0x104: RETURN
      return __r[1].value
    else
      __unresolved("Invalid reconstructed program counter")
    end
  end
end)(...)

end)(-2147483648))
assert(result.n==1,'result count case 70')
assert(result[1]==0,'result value case 70 slot 1')
passed=passed+1
end
return passed
