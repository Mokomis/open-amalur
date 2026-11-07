-- Verify real GC semantics, including the historical first-NUL boundary.
local cases = {
  {"", false, false}, {"k", true, false}, {"v", false, true},
  {"kv", true, true}, {"vk", true, true}, {"x", false, false},
  {"kkvv", true, true}, {"\0kv", false, false},
  {"k\0v", true, false}, {"v\0k", false, true},
  {"x\0kv", false, false}, {"kv\0", true, true},
  {string.rep("x", 4096) .. "kv", true, true},
  {string.rep("x", 4096) .. "\0kv", false, false},
  {false, false, false}, {7, false, false},
}

local function key_table(mode)
  local t = setmetatable({}, {__mode = mode})
  t[{}] = true
  return t
end

local function value_table(mode)
  local t = setmetatable({}, {__mode = mode})
  t[1] = {}
  return t
end

local checks = 0
for i, case in ipairs(cases) do
  local keys, values = key_table(case[1]), value_table(case[1])
  collectgarbage("collect")
  collectgarbage("collect")
  assert((next(keys) == nil) == case[2], "weak keys case " .. i)
  assert((values[1] == nil) == case[3], "weak values case " .. i)
  checks = checks + 2
end
print("weak-mode GC checks: " .. checks)
