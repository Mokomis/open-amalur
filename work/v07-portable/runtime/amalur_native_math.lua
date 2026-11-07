-- Native Amalur integer math bindings, guarded signed-int32 domain only.
-- Target16a400f6...09cb314. Native callbacks at00aa1fa0..00aa21b6.
-- Ordinary Lua5.1 math is not equivalent at overflow/negative-root boundaries.
local type, error, select = type, error, select
local module = {}
local function integer(value)
  if type(value)~='number' or value~=value or value < -2147483648 or value > 2147483647 or value%1~=0 then
    error('Amalur native math requires signed-int32 arguments', 3)
  end
  return value==0 and 0 or value
end
local function wrap(value) return (value+2147483648)%4294967296-2147483648 end
local function multiply(a,b)
  a=a%4294967296;b=b%4294967296
  local al,bl=a%65536,b%65536
  return wrap(al*bl + ((al*((b-bl)/65536)+((a-al)/65536)*bl)%65536)*65536)
end
function module.abs(value)
  value=integer(value)
  return value<0 and wrap(-value) or value
end
function module.pow(value,exponent)
  value=integer(value);exponent=integer(exponent)
  if exponent<0 then return 0 end
  local result=1
  while exponent>0 do
    if exponent%2==1 then result=multiply(result,value) end
    exponent=(exponent-exponent%2)/2
    if exponent>0 then value=multiply(value,value) end
  end
  return result
end
function module.min(first,...)
  local result=integer(first)
  for i=1,select('#',...) do local value=integer(select(i,...));if value<result then result=value end end
  return result
end
function module.max(first,...)
  local result=integer(first)
  for i=1,select('#',...) do local value=integer(select(i,...));if value>result then result=value end end
  return result
end
function module.sqrt(value)
  value=integer(value)
  if value<=0 then return value==0 and 0 or -1 end
  local bits,bound=4,16
  while value>bound do
    bits=bits+2;bound=wrap(bound*4)
    if bits>=31 then break end
  end
  local guess=2^(bits/2)
  local quotient=value/guess;quotient=quotient-quotient%1
  local next_guess=(quotient+guess)/2;next_guess=next_guess-next_guess%1
  while next_guess<guess do
    guess=next_guess;quotient=value/guess;quotient=quotient-quotient%1
    next_guess=(quotient+guess)/2;next_guess=next_guess-next_guess%1
  end
  -- Preserve signed IMUL overflow in the native callback's final two checks.
  if multiply(guess,guess)<=value and multiply(guess+1,guess+1)>value then return guess end
  return -1
end
return module
