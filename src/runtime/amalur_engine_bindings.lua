-- Provider bridge for recovered engine namespaces; Lua 5.1.
-- This is an interface scaffold, not an implementation of native behavior.
-- Registry entries describe observed names/addresses, not argument coercions.
local kind, fail, raw, next_item, describe = type, error, rawget, next, tostring
local meta = getmetatable
local module = {}

local function plain(value, label)
  if kind(value) ~= "table" or meta(value) ~= nil then
    fail(label .. " must be a plain table", 3)
  end
end

local function forward(namespace, name, callback)
  if callback == nil then
    return function(...)
      fail("unimplemented Amalur engine binding: " .. namespace .. "." .. name, 2)
    end
  end
  return function(...)
    -- Direct tail forwarding retains trailing nil arguments/results and tokens.
    -- Provider errors propagate unchanged; providers receive no implicit self.
    return callback(...)
  end
end

function module.new(registry, provider)
  plain(registry, "binding registry")
  plain(provider, "engine provider")
  local environment = {}
  for namespace, methods in next_item, registry do
    if kind(namespace) ~= "string" then fail("invalid namespace name", 2) end
    plain(methods, "namespace registry " .. namespace)
    local supplied = raw(provider, namespace)
    if supplied ~= nil then plain(supplied, "provider namespace " .. namespace) end
    local installed = {}
    for name, address in next_item, methods do
      if kind(name) ~= "string" or kind(address) ~= "string" then
        fail("invalid binding registry entry", 2)
      end
      local callback = supplied and raw(supplied, name)
      if callback ~= nil and kind(callback) ~= "function" then
        fail("provider must supply a function: " .. namespace .. "." .. name, 2)
      end
      installed[name] = forward(namespace, name, callback)
    end
    if supplied then
      for name in next_item, supplied do
        if raw(methods, name) == nil then
          fail("provider supplied unregistered binding: " .. namespace .. "." .. describe(name), 2)
        end
      end
    end
    environment[namespace] = installed
  end
  for namespace in next_item, provider do
    if raw(registry, namespace) == nil then
      fail("provider supplied unregistered namespace: " .. describe(namespace), 2)
    end
  end
  -- Tables deliberately remain plain for the reconstructed VM's table guards.
  -- No global writes or mutation of registry/provider; each realm gets new tables.
  return environment
end

return module
