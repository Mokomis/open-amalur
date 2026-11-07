"""Bounded native Linux ARM64 Vulkan compatibility check; no game input."""
import ctypes as c
import json
import platform
import os
import sys

if "--layer" in sys.argv:
    os.environ.update(VK_LAYER_PATH="/root/oa-native-tools", GFXRECON_CAPTURE_FILE="/root/oa-native-tools/probe.gfxr", GFXRECON_CAPTURE_FILE_TIMESTAMP="false", GFXRECON_MEMORY_TRACKING_MODE="unassisted")

vk = c.CDLL('libvulkan.so.1')
u32 = c.c_uint32
ptr = c.c_void_p

class Extension(c.Structure):
    _fields_ = [('name', c.c_char * 256), ('version', u32)]

class InstanceInfo(c.Structure):
    _fields_ = [('type', u32), ('next', ptr), ('flags', u32), ('app', ptr),
                ('nlayers', u32), ('layers', ptr), ('nextensions', u32), ('extensions', ptr)]

def bind(name, args):
    f = getattr(vk, name)
    f.restype = c.c_int32
    f.argtypes = args
    return f

enum = bind('vkEnumerateInstanceExtensionProperties', [ptr, c.POINTER(u32), ptr])
n = u32()
assert enum(None, c.byref(n), None) == 0
exts = (Extension * n.value)()
assert enum(None, c.byref(n), exts) == 0
names = sorted(x.name.decode() for x in exts)
create = bind('vkCreateInstance', [c.POINTER(InstanceInfo), ptr, c.POINTER(ptr)])
destroy = bind('vkDestroyInstance', [ptr, ptr])
instance = ptr()
info = InstanceInfo(type=1)
layer_names = (c.c_char_p * 1)(b"VK_LAYER_LUNARG_gfxreconstruct")
if "--layer" in sys.argv:
    info.nlayers = 1
    info.layers = c.cast(layer_names, ptr)
assert create(c.byref(info), None, c.byref(instance)) == 0
try:
    devices = bind('vkEnumeratePhysicalDevices', [ptr, c.POINTER(u32), ptr])
    assert devices(instance, c.byref(n), None) == 0
    handles = (ptr * n.value)()
    assert devices(instance, c.byref(n), handles) == 0
    props = bind('vkGetPhysicalDeviceProperties', [ptr, ptr])
    devs = []
    for handle in handles:
        data = c.create_string_buffer(4096)
        props(handle, data)
        values = c.cast(data, c.POINTER(u32))
        devs.append({'name': data.raw[20:276].split(b'\0')[0].decode(),
                     'api': values[0], 'vendor': values[2], 'device': values[3]})
    print(json.dumps({'architecture': platform.machine(), 'pointer_bits': c.sizeof(ptr)*8,
                      'devices': devs, 'instance_extensions': names}, indent=2), flush=True)
finally:
    destroy(instance, None)
