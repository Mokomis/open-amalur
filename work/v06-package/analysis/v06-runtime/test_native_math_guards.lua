-- Admission policy checks; native equivalence is tested separately.
local math = ...
local checks = {}
local function reject(label, fn)
  local ok, err = pcall(fn)
  assert(not ok and tostring(err):find('signed-int32', 1, true), label)
  checks[#checks+1] = label
end
local invalid = {false, true, '1', {}, function() end, 0/0, 1/0, -1/0,
                 0.5, -0.5, 2147483648, -2147483649}
for _, name in ipairs({'abs','sqrt','min','max'}) do
  for i, value in ipairs(invalid) do
    reject(name..' invalid argument '..i, function() math[name](value) end)
  end
  reject(name..' missing argument', function() math[name]() end)
end
for i, value in ipairs(invalid) do
  reject('pow invalid base '..i, function() math.pow(value, 2) end)
  reject('pow invalid exponent '..i, function() math.pow(2, value) end)
end
reject('pow missing exponent', function() math.pow(2) end)
reject('min trailing nil', function() math.min(7, nil) end)
reject('max trailing nil', function() math.max(7, nil) end)
reject('min invalid later argument', function() math.min(-5, '7') end)
reject('max invalid later argument', function() math.max(5, {}) end)
assert(math.abs(-2147483648)==-2147483648)
assert(math.sqrt(-1)==-1 and math.sqrt(2147395599)==46339)
assert(math.sqrt(2147395600)==-1 and math.sqrt(2147483647)==-1)
assert(math.pow(65537,2)==131073 and math.pow(0,0)==1 and math.pow(2,-1)==0)
assert(math.min(0,-2147483648,2147483647)==-2147483648)
assert(math.max(0,-2147483648,2147483647)==2147483647)
checks[#checks+1]='native-confirmed overflow and boundary examples'
return checks
