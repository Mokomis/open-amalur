/* oa_vk.c: the subset of Direct3D 11 and DXGI that koa.exe uses, implemented on Vulkan 1.3.
   Built as d3d11.dll. Anything not implemented logs its name once to oa_vk.log and returns E_NOTIMPL. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#include <malloc.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define VK_NO_PROTOTYPES
#define VK_USE_PLATFORM_WIN32_KHR
#include <vulkan/vulkan.h>
#include "oa_dxbc.h"

#define COM __stdcall
#define S_OK_ 0
#define E_NOTIMPL_ ((HRESULT)0x80004001L)
#define E_NOINTERFACE_ ((HRESULT)0x80004002L)
#define E_FAIL_ ((HRESULT)0x80004005L)
#define E_OOM_ ((HRESULT)0x8007000EL)
#define DXGI_NOT_FOUND ((HRESULT)0x887A0002L)
#define FRAMES 2
#define RING_SIZE (32u << 20)

/* ---- logging ---- */
static FILE *g_log;
static char g_game_log[MAX_PATH];
static CRITICAL_SECTION g_lock;
static void logf_(const char *fmt, ...) {
    va_list a;
    if (!g_log) return;
    EnterCriticalSection(&g_lock);
    va_start(a, fmt);
    vfprintf(g_log, fmt, a);
    va_end(a);
    fputc('\n', g_log);
    fflush(g_log);
    LeaveCriticalSection(&g_lock);
}

/* ---- Vulkan entry points ---- */
#define VK_FUNCS(X) \
    X(vkDestroyInstance) X(vkEnumeratePhysicalDevices) X(vkGetPhysicalDeviceProperties) X(vkGetPhysicalDeviceFeatures2) X(vkGetPhysicalDeviceQueueFamilyProperties) \
    X(vkGetPhysicalDeviceMemoryProperties) X(vkGetPhysicalDeviceFormatProperties) X(vkCreateDevice) X(vkGetDeviceProcAddr) X(vkCreateWin32SurfaceKHR) \
    X(vkGetPhysicalDeviceSurfaceCapabilitiesKHR) X(vkGetPhysicalDeviceSurfaceFormatsKHR) X(vkGetPhysicalDeviceSurfacePresentModesKHR) X(vkGetPhysicalDeviceSurfaceSupportKHR) X(vkGetPhysicalDeviceProperties2)
#define VKD_FUNCS(X) \
    X(vkGetDeviceQueue) X(vkAllocateMemory) X(vkFreeMemory) X(vkMapMemory) X(vkCreateBuffer) X(vkDestroyBuffer) X(vkGetBufferMemoryRequirements) X(vkBindBufferMemory) \
    X(vkCreateImage) X(vkDestroyImage) X(vkGetImageMemoryRequirements) X(vkBindImageMemory) X(vkCreateImageView) X(vkDestroyImageView) X(vkCreateSampler) \
    X(vkCreateShaderModule) X(vkCreateDescriptorSetLayout) X(vkCreatePipelineLayout) X(vkCreateGraphicsPipelines) X(vkCreatePipelineCache) X(vkCreateCommandPool) \
    X(vkResetCommandPool) X(vkAllocateCommandBuffers) X(vkBeginCommandBuffer) X(vkEndCommandBuffer) X(vkQueueSubmit) X(vkQueueWaitIdle) X(vkCreateFence) X(vkWaitForFences) \
    X(vkResetFences) X(vkCreateSemaphore) X(vkCreateSwapchainKHR) X(vkDestroySwapchainKHR) X(vkGetSwapchainImagesKHR) X(vkAcquireNextImageKHR) X(vkQueuePresentKHR) \
    X(vkCmdPipelineBarrier) X(vkCmdCopyBufferToImage) X(vkCmdCopyImage) X(vkCmdBlitImage) X(vkCmdClearColorImage) X(vkCmdClearDepthStencilImage) X(vkCmdBeginRendering) \
    X(vkCmdEndRendering) X(vkCmdBindPipeline) X(vkCmdSetViewport) X(vkCmdSetScissor) X(vkCmdSetStencilReference) X(vkCmdSetBlendConstants) X(vkCmdBindVertexBuffers2) \
    X(vkCmdBindIndexBuffer) X(vkCmdDraw) X(vkCmdDrawIndexed) X(vkCreateQueryPool) X(vkGetQueryPoolResults) X(vkCmdResetQueryPool) X(vkCmdBeginQuery) X(vkCmdEndQuery) X(vkCreateDescriptorPool) X(vkDestroyDescriptorPool) X(vkAllocateDescriptorSets) X(vkUpdateDescriptorSets) X(vkCmdBindDescriptorSets)
#define X(n) static PFN_##n p##n;
VK_FUNCS(X)
VKD_FUNCS(X)
#undef X

static VkInstance g_instance;
static VkPhysicalDevice g_phys;
static VkDevice g_dev;
static VkQueue g_queue;
static uint32_t g_qfam;
static VkPhysicalDeviceMemoryProperties g_mem;
static VkPipelineCache g_pcache;
static VkDeviceSize g_ubo_align = 256;
static VkFormat g_d24s8 = VK_FORMAT_D24_UNORM_S8_UINT;

static uint32_t mem_type(uint32_t bits, VkMemoryPropertyFlags want, VkMemoryPropertyFlags fallback) {
    uint32_t i;
    for (i = 0; i < g_mem.memoryTypeCount; i++)
        if ((bits >> i & 1) && (g_mem.memoryTypes[i].propertyFlags & want) == want) return i;
    for (i = 0; i < g_mem.memoryTypeCount; i++)
        if ((bits >> i & 1) && (g_mem.memoryTypes[i].propertyFlags & fallback) == fallback) return i;
    return 0;
}

typedef struct {
    VkBuffer buf;
    VkDeviceMemory mem;
    uint8_t *ptr;
} vk_buffer;

static int make_buffer(vk_buffer *b, VkDeviceSize size, VkBufferUsageFlags usage) {
    VkBufferCreateInfo ci = {VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
    VkMemoryRequirements r;
    VkMemoryAllocateInfo ai = {VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    ci.size = size;
    ci.usage = usage;
    if (pvkCreateBuffer(g_dev, &ci, NULL, &b->buf)) return 0;
    pvkGetBufferMemoryRequirements(g_dev, b->buf, &r);
    ai.allocationSize = r.size;
    ai.memoryTypeIndex = mem_type(r.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT | VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    if (pvkAllocateMemory(g_dev, &ai, NULL, &b->mem)) {
        ai.memoryTypeIndex = mem_type(r.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT);
        if (pvkAllocateMemory(g_dev, &ai, NULL, &b->mem)) return 0;
    }
    pvkBindBufferMemory(g_dev, b->buf, b->mem, 0);
    pvkMapMemory(g_dev, b->mem, 0, VK_WHOLE_SIZE, 0, (void **)&b->ptr);
    return 1;
}

/* Mapped memory must be 16-byte aligned: the engine writes it with aligned SSE moves. */
static void *zalloc16(size_t n) {
    void *p = _aligned_malloc(n ? n : 16, 16);
    if (p) memset(p, 0, n);
    return p;
}

/* ---- COM objects ---- */
enum { K_DEVICE, K_CONTEXT, K_DXGI_DEVICE, K_ADAPTER, K_FACTORY, K_CHAIN, K_BUFFER, K_TEX2D, K_SRV, K_RTV, K_DSV, K_LAYOUT, K_VS, K_PS, K_BLEND, K_DEPTH, K_RASTER, K_SAMPLER, K_PREDICATE };

typedef struct {
    void **vtbl;
    volatile LONG ref;
    int kind;
} obj;

#define MAX_GENS 8
typedef struct {
    obj o;
    uint32_t size, usage, bind, cpu, misc, stride;
    int ring;           /* constant buffer: contents live in shadow, copied to the frame's ring */
    uint8_t *shadow;
    VkBuffer ring_buf;
    uint32_t ring_off;
    uint64_t ring_frame;
    int dirty;
    vk_buffer gens[MAX_GENS];
    uint64_t gen_used[MAX_GENS];
    int ngens, cur;
} oa_buffer;

typedef struct {
    obj o;
    uint32_t desc[11];
    uint32_t w, h, depth, mips, layers, fmt, type3d;
    VkFormat vkfmt;
    VkImage image;
    VkDeviceMemory mem;
    int is_depth, has_stencil, block, bytes;
    uint8_t *cpu;       /* staging and dynamic textures */
    uint32_t cpu_size;
    int upload_mip;
    int is_backbuffer;
} oa_tex;

typedef struct {
    obj o;
    oa_tex *tex;
    VkImageView view;
    VkFormat format;
    uint32_t desc[12], w, h, level, uid;
} oa_view;

typedef struct {
    uint32_t name_hash;
    char name[32];
    uint32_t index, fmt, slot, offset, cls, step;
} oa_elem;
typedef struct {
    obj o;
    int n;
    oa_elem e[32];
} oa_layout;

typedef struct {
    obj o;
    VkShaderModule module;
    oa_shader_info info;
    uint32_t hash;
} oa_shader;

typedef struct {
    obj o;
    uint32_t desc[20];
    VkSampler sampler, lod0_sampler;
} oa_state;

/* An occlusion predicate. The result is read back on the CPU from a finished frame, so a hidden object costs no Vulkan work at all. */
typedef struct {
    obj o;
    int visible, acc;
    uint64_t tested_frame;
} oa_pred;

/* forward */
typedef struct oa_chain oa_chain;

typedef struct {
    obj o;
    int deferred;
    oa_buffer *vs_cb[14], *ps_cb[14];
    oa_view *vs_srv[32], *ps_srv[32];
    oa_state *vs_smp[16], *ps_smp[16];
    oa_shader *vs, *ps;
    oa_layout *layout;
    oa_state *blend, *depth, *raster;
    uint32_t stencil_ref;
    float blend_factor[4];
    uint32_t topology;
    oa_buffer *vb[16];
    uint32_t vb_stride[16], vb_off[16];
    oa_buffer *ib;
    uint32_t ib_fmt, ib_off;
    oa_view *rtv[8], *dsv;
    VkViewport vp;
    VkRect2D scissor;
    int have_vp, have_scissor;
    /* recording */
    int rendering, pipeline_valid;
    oa_pred *q_active, *pred;
    VkPipeline last_pipeline;
    /* What the command buffer already has, so unchanged state costs no Vulkan call. Each call is expensive under x86 translation. */
    int cache_valid;
    VkViewport set_vp;
    VkRect2D set_scissor;
    uint32_t set_stencil;
    float set_blend[4];
    VkBuffer set_vb[4];
    VkDeviceSize set_off[4], set_stride[4];
    VkBuffer set_ib;
    uint32_t set_ib_off, set_ib_type;
    VkPipelineLayout set_layout;
    VkDescriptorSet set_desc;
    uint32_t set_ndyn, set_dyn[32];
} oa_context;

struct oa_chain {
    obj o;
    HWND hwnd;
    uint32_t w, h, fmt;
    oa_tex *back;
    VkSurfaceKHR surface;
    VkSwapchainKHR swapchain;
    VkImage images[8];
    uint32_t nimages;
    VkExtent2D extent;
    VkFormat swap_fmt;
};

static void *g_vt[32];
static obj g_device_obj = {0};
static oa_context *g_ctx;
static int g_force_lod0; /* diagnostic only: highest mip in each bound view */

/* ---- generated stubs for methods not implemented ---- */
static const char *const DEVICE_NAMES[43] = {"QueryInterface", "AddRef", "Release", "CreateBuffer", "CreateTexture1D", "CreateTexture2D", "CreateTexture3D", "CreateShaderResourceView", "CreateUnorderedAccessView", "CreateRenderTargetView", "CreateDepthStencilView", "CreateInputLayout", "CreateVertexShader", "CreateGeometryShader", "CreateGeometryShaderWithStreamOutput", "CreatePixelShader", "CreateHullShader", "CreateDomainShader", "CreateComputeShader", "CreateClassLinkage", "CreateBlendState", "CreateDepthStencilState", "CreateRasterizerState", "CreateSamplerState", "CreateQuery", "CreatePredicate", "CreateCounter", "CreateDeferredContext", "OpenSharedResource", "CheckFormatSupport", "CheckMultisampleQualityLevels", "CheckCounterInfo", "CheckCounter", "CheckFeatureSupport", "GetPrivateData", "SetPrivateData", "SetPrivateDataInterface", "GetFeatureLevel", "GetCreationFlags", "GetDeviceRemovedReason", "GetImmediateContext", "SetExceptionMode", "GetExceptionMode"};
static const uint8_t DEVICE_ARGS[43] = {3,1,1,4,4,4,4,4,4,4,4,6,5,5,10,5,5,5,5,2,3,3,3,3,3,3,3,3,4,3,4,2,10,4,4,4,3,1,1,1,2,2,1};
static const uint8_t CONTEXT_ARGS[115] = {3,1,1,2,4,4,3,4,4,4,4,4,4,3,6,3,4,2,6,4,6,5,4,4,2,4,4,2,2,5,3,4,4,4,8,4,3,4,1,3,3,4,3,2,3,3,9,3,7,4,3,3,3,5,2,3,2,6,3,4,4,4,4,4,4,4,4,4,5,4,4,4,4,4,4,4,4,4,2,6,4,4,4,2,4,4,3,4,4,4,7,4,3,3,2,3,3,4,4,4,4,4,4,4,4,4,4,4,4,4,1,1,1,1,3};

typedef struct { char label[48]; } stub_info;
static stub_info g_stubs[512];
static volatile LONG g_stub_seen[512];
static int g_nstubs;
static uint8_t *g_stub_code;

static void __cdecl stub_hit(int i) {
    if (InterlockedExchange(&g_stub_seen[i], 1) == 0) logf_("NOT IMPLEMENTED %s", g_stubs[i].label);
}

static void *make_stub(const char *label, int args) {
    uint8_t *t = g_stub_code + g_nstubs * 24;
    int i = g_nstubs++;
    snprintf(g_stubs[i].label, sizeof(g_stubs[i].label), "%s", label);
    t[0] = 0x68; memcpy(t + 1, &i, 4);                                  /* push i */
    t[5] = 0xE8; *(int32_t *)(t + 6) = (int32_t)((uint8_t *)stub_hit - (t + 10)); /* call stub_hit */
    t[10] = 0x83; t[11] = 0xC4; t[12] = 0x04;                            /* add esp,4 */
    t[13] = 0xB8; *(uint32_t *)(t + 14) = 0x80004001u;                   /* mov eax,E_NOTIMPL */
    t[18] = 0xC2; *(uint16_t *)(t + 19) = (uint16_t)(args * 4);          /* ret n */
    return t;
}

static void **make_vtable(const char *iface, const char *const *names, const uint8_t *args, int n) {
    void **vt = calloc((size_t)n, sizeof(void *));
    int i;
    for (i = 0; i < n; i++) {
        char label[48];
        if (names) snprintf(label, sizeof(label), "%s::%s", iface, names[i]);
        else snprintf(label, sizeof(label), "%s::slot%d", iface, i);
        vt[i] = make_stub(label, args[i]);
    }
    return vt;
}

/* ---- IUnknown ---- */
static ULONG COM o_addref(obj *o) { return (ULONG)InterlockedIncrement(&o->ref); }

/* Objects are parked for a few frames before their Vulkan handles go away; the GPU may still be using them. */
typedef struct gone { struct gone *next; obj *o; uint64_t frame; } gone;
static gone *g_gone;
static uint64_t g_frame = 1, g_done_frame;

static ULONG COM o_release(obj *o) {
    LONG r = InterlockedDecrement(&o->ref);
    if (r == 0) {
        gone *g = malloc(sizeof(gone));
        EnterCriticalSection(&g_lock);
        g->o = o;
        g->frame = g_frame;
        g->next = g_gone;
        g_gone = g;
        LeaveCriticalSection(&g_lock);
    }
    return (ULONG)r;
}

static void destroy_obj(obj *o) {
    int i;
    switch (o->kind) {
    case K_BUFFER: {
        oa_buffer *b = (oa_buffer *)o;
        for (i = 0; i < b->ngens; i++) {
            pvkDestroyBuffer(g_dev, b->gens[i].buf, NULL);
            pvkFreeMemory(g_dev, b->gens[i].mem, NULL);
        }
        _aligned_free(b->shadow);
        break;
    }
    case K_TEX2D: {
        oa_tex *t = (oa_tex *)o;
        if (t->image) pvkDestroyImage(g_dev, t->image, NULL);
        if (t->mem) pvkFreeMemory(g_dev, t->mem, NULL);
        _aligned_free(t->cpu);
        break;
    }
    case K_SRV: case K_RTV: case K_DSV: {
        oa_view *v = (oa_view *)o;
        if (v->view) pvkDestroyImageView(g_dev, v->view, NULL);
        if (v->tex) o_release(&v->tex->o);
        break;
    }
    default: break;
    }
    free(o);
}

static void collect_gone(void) {
    gone *keep = NULL, *g, *n, *dead = NULL;
    EnterCriticalSection(&g_lock);
    for (g = g_gone; g; g = n) {
        n = g->next;
        if (g->frame + FRAMES + 1 < g_frame && g->frame <= g_done_frame) { g->next = dead; dead = g; }
        else { g->next = keep; keep = g; }
    }
    g_gone = keep;
    LeaveCriticalSection(&g_lock);
    for (g = dead; g; g = n) {
        n = g->next;
        destroy_obj(g->o);
        free(g);
    }
}

static const GUID IID_IUnknown_ = {0, 0, 0, {0xC0, 0, 0, 0, 0, 0, 0, 0x46}};
static const GUID IID_D3D11Device = {0xdb6f6ddb, 0xac77, 0x4e88, {0x82, 0x53, 0x81, 0x9d, 0xf9, 0xbb, 0xf1, 0x40}};
static const GUID IID_DXGIDevice = {0x54ec77fa, 0x1377, 0x44e6, {0x8c, 0x32, 0x88, 0xfd, 0x5f, 0x44, 0xc8, 0x4c}};
static obj *g_dxgi_device, *g_adapter, *g_factory;

static HRESULT COM o_qi(obj *o, const GUID *iid, void **out) {
    if (!memcmp(iid, &IID_IUnknown_, sizeof(GUID))) {
        o_addref(o);
        *out = o;
        return S_OK_;
    }
    if (o->kind == K_DEVICE && !memcmp(iid, &IID_D3D11Device, sizeof(GUID))) {
        o_addref(o);
        *out = o;
        return S_OK_;
    }
    if (o->kind == K_DEVICE && !memcmp(iid, &IID_DXGIDevice, sizeof(GUID))) {
        o_addref(g_dxgi_device);
        *out = g_dxgi_device;
        return S_OK_;
    }
    if (o->kind == K_TEX2D || o->kind == K_BUFFER || o->kind == K_CHAIN || o->kind == K_FACTORY || o->kind == K_ADAPTER || o->kind == K_DXGI_DEVICE) {
        /* Same object for any derived interface of the object itself. */
        o_addref(o);
        *out = o;
        return S_OK_;
    }
    logf_("QueryInterface kind %d unknown %08lx-%04x-%04x", o->kind, iid->Data1, iid->Data2, iid->Data3);
    *out = NULL;
    return E_NOINTERFACE_;
}

static obj *new_obj(size_t size, int kind) {
    obj *o = calloc(1, size);
    o->vtbl = g_vt[kind];
    o->ref = 1;
    o->kind = kind;
    return o;
}

/* ---- formats ---- */
typedef struct { VkFormat vk; int block, bytes; } fmt_info;

static fmt_info dx_format(uint32_t f) {
    fmt_info r = {VK_FORMAT_UNDEFINED, 1, 4};
#define F(D, V, B, Y) case D: r.vk = V; r.block = B; r.bytes = Y; break
    switch (f) {
    F(2, VK_FORMAT_R32G32B32A32_SFLOAT, 1, 16);
    F(6, VK_FORMAT_R32G32B32_SFLOAT, 1, 12);
    F(9, VK_FORMAT_R16G16B16A16_SFLOAT, 1, 8);
    F(10, VK_FORMAT_R16G16B16A16_SFLOAT, 1, 8);
    F(11, VK_FORMAT_R16G16B16A16_UNORM, 1, 8);
    F(12, VK_FORMAT_R16G16B16A16_UINT, 1, 8);
    F(13, VK_FORMAT_R16G16B16A16_SNORM, 1, 8);
    F(14, VK_FORMAT_R16G16B16A16_SINT, 1, 8);
    F(16, VK_FORMAT_R32G32_SFLOAT, 1, 8);
    F(24, VK_FORMAT_A2B10G10R10_UNORM_PACK32, 1, 4);
    F(26, VK_FORMAT_B10G11R11_UFLOAT_PACK32, 1, 4);
    F(27, VK_FORMAT_R8G8B8A8_UNORM, 1, 4);
    F(28, VK_FORMAT_R8G8B8A8_UNORM, 1, 4);
    F(29, VK_FORMAT_R8G8B8A8_SRGB, 1, 4);
    F(30, VK_FORMAT_R8G8B8A8_UINT, 1, 4);
    F(31, VK_FORMAT_R8G8B8A8_SNORM, 1, 4);
    F(32, VK_FORMAT_R8G8B8A8_SINT, 1, 4);
    F(34, VK_FORMAT_R16G16_SFLOAT, 1, 4);
    F(35, VK_FORMAT_R16G16_UNORM, 1, 4);
    F(36, VK_FORMAT_R16G16_UINT, 1, 4);
    F(37, VK_FORMAT_R16G16_SNORM, 1, 4);
    F(38, VK_FORMAT_R16G16_SINT, 1, 4);
    F(39, VK_FORMAT_R32_SFLOAT, 1, 4);
    F(40, VK_FORMAT_D32_SFLOAT, 1, 4);
    F(41, VK_FORMAT_R32_SFLOAT, 1, 4);
    F(44, g_d24s8, 1, 4);
    F(45, g_d24s8, 1, 4);
    F(46, g_d24s8, 1, 4);
    F(49, VK_FORMAT_R8G8_UNORM, 1, 2);
    F(53, VK_FORMAT_R16_UNORM, 1, 2);
    F(54, VK_FORMAT_R16_SFLOAT, 1, 2);
    F(55, VK_FORMAT_D16_UNORM, 1, 2);
    F(56, VK_FORMAT_R16_UNORM, 1, 2);
    F(57, VK_FORMAT_R16_UINT, 1, 2);
    F(61, VK_FORMAT_R8_UNORM, 1, 1);
    F(65, VK_FORMAT_R8_UNORM, 1, 1);
    F(71, VK_FORMAT_BC1_RGBA_UNORM_BLOCK, 4, 8);
    F(72, VK_FORMAT_BC1_RGBA_SRGB_BLOCK, 4, 8);
    F(74, VK_FORMAT_BC2_UNORM_BLOCK, 4, 16);
    F(75, VK_FORMAT_BC2_SRGB_BLOCK, 4, 16);
    F(77, VK_FORMAT_BC3_UNORM_BLOCK, 4, 16);
    F(78, VK_FORMAT_BC3_SRGB_BLOCK, 4, 16);
    F(80, VK_FORMAT_BC4_UNORM_BLOCK, 4, 8);
    F(83, VK_FORMAT_BC5_UNORM_BLOCK, 4, 16);
    F(87, VK_FORMAT_B8G8R8A8_UNORM, 1, 4);
    F(88, VK_FORMAT_B8G8R8A8_UNORM, 1, 4);
    F(91, VK_FORMAT_B8G8R8A8_SRGB, 1, 4);
    default: logf_("unknown DXGI format %u", f); break;
    }
#undef F
    return r;
}

/* Report once per format anything this driver cannot do with it. Using an unsupported format is undefined, and can differ by GPU. */
static uint8_t g_fmt_seen[256];
static void check_format(uint32_t dx, int use_vertex, int use_rt, uint32_t w, uint32_t h, uint32_t mips) {
    VkFormatProperties p;
    fmt_info fi;
    uint8_t bit = use_vertex ? 1 : use_rt ? 2 : 4;
    if (dx >= 256 || (g_fmt_seen[dx] & bit)) return;
    g_fmt_seen[dx] |= bit;
    fi = dx_format(dx);
    pvkGetPhysicalDeviceFormatProperties(g_phys, fi.vk, &p);
    logf_("format dxgi %u vk %d use %s first %ux%u mips %u: buffer %x optimal %x%s%s%s", dx, fi.vk, use_vertex ? "vertex" : use_rt ? "target" : "texture", w, h, mips, p.bufferFeatures, p.optimalTilingFeatures,
          use_vertex && !(p.bufferFeatures & VK_FORMAT_FEATURE_VERTEX_BUFFER_BIT) ? " NO-VERTEX" : "",
          !use_vertex && !(p.optimalTilingFeatures & VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT) ? " NO-SAMPLE" : !use_vertex && !(p.optimalTilingFeatures & VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT) ? " NO-LINEAR" : "",
          use_rt && !(p.optimalTilingFeatures & VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BLEND_BIT) ? " NO-BLEND" : "");
}

static uint32_t mip_dim(uint32_t d, uint32_t m) { d >>= m; return d ? d : 1; }

/* ---- frames, ring and one-shot commands ---- */
typedef struct {
    VkCommandPool pool;
    VkCommandBuffer cmd;
    VkFence fence;
    VkSemaphore acquired, rendered;
    vk_buffer rings[8];
    int nrings, ring_cur;
    uint32_t ring_off;
    uint64_t frame;
    int submitted;
    VkQueryPool qpool;
    uint32_t qused, qreset;
    oa_pred **qlist;
} oa_frame;
static oa_frame g_f[FRAMES];
static oa_frame *g_cur;
static VkCommandPool g_upload_pool;
static VkCommandBuffer g_upload_cmd;
static VkFence g_upload_fence;
static int g_ring_overflow;

static void *ring_alloc(uint32_t size, VkBuffer *buf, uint32_t *off) {
    oa_frame *f = g_cur;
    uint32_t a = (uint32_t)g_ubo_align, o = (f->ring_off + a - 1) & ~(a - 1);
    if (size > RING_SIZE) { logf_("ring request of %u bytes is too large", size); size = RING_SIZE; }
    if (o + size > RING_SIZE) {
        f->ring_cur++;
        if (f->ring_cur == f->nrings) {
            if (f->nrings < 8 && make_buffer(&f->rings[f->nrings], RING_SIZE, VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT)) {
                f->nrings++;
                logf_("ring grew to %d chunks", f->nrings);
            } else {
                if (!g_ring_overflow) { g_ring_overflow = 1; logf_("ring overflow"); }
                f->ring_cur = 0;
            }
        }
        o = 0;
    }
    f->ring_off = o + size;
    *buf = f->rings[f->ring_cur].buf;
    *off = o;
    return f->rings[f->ring_cur].ptr + o;
}

static void desc_retire_pools(void);
#define QUERY_MAX 32768u
static long g_n_culled, g_n_tests, g_n_test_skipped;
static int g_cull = 1;

static void read_queries(oa_frame *f) {
    static uint32_t r[QUERY_MAX];
    uint32_t i, n = f->qused;
    f->qreset = n ? n : f->qreset;
    f->qused = 0;
    if (!n) return;
    if (pvkGetQueryPoolResults(g_dev, f->qpool, 0, n, n * 4, r, 4, 0)) return;
    for (i = 0; i < n; i++) f->qlist[i]->acc = 0;
    for (i = 0; i < n; i++) f->qlist[i]->acc |= r[i] != 0;
    for (i = 0; i < n; i++) {
        f->qlist[i]->visible = f->qlist[i]->acc;
        f->qlist[i]->tested_frame = f->frame;
    }
}

static void frame_begin(void) {
    oa_frame *f = &g_f[g_frame % FRAMES];
    VkCommandBufferBeginInfo bi = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    if (f->submitted) {
        pvkWaitForFences(g_dev, 1, &f->fence, VK_TRUE, UINT64_MAX);
        pvkResetFences(g_dev, 1, &f->fence);
        f->submitted = 0;
        g_done_frame = f->frame;
        read_queries(f);
    }
    collect_gone();
    desc_retire_pools();
    pvkResetCommandPool(g_dev, f->pool, 0);
    bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    pvkBeginCommandBuffer(f->cmd, &bi);
    if (f->qreset) {
        pvkCmdResetQueryPool(f->cmd, f->qpool, 0, f->qreset);
        f->qreset = 0;
    }
    f->ring_off = 0;
    f->ring_cur = 0;
    f->frame = g_frame;
    g_cur = f;
}

static void barrier_all(VkCommandBuffer c) {
    VkMemoryBarrier m = {VK_STRUCTURE_TYPE_MEMORY_BARRIER};
    m.srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT;
    m.dstAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT;
    pvkCmdPipelineBarrier(c, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 1, &m, 0, NULL, 0, NULL);
}

static void image_layout(VkCommandBuffer c, VkImage i, VkImageAspectFlags aspect, VkImageLayout from, VkImageLayout to) {
    VkImageMemoryBarrier b = {VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
    b.srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT;
    b.dstAccessMask = VK_ACCESS_MEMORY_READ_BIT | VK_ACCESS_MEMORY_WRITE_BIT;
    b.oldLayout = from;
    b.newLayout = to;
    b.srcQueueFamilyIndex = b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    b.image = i;
    b.subresourceRange.aspectMask = aspect;
    b.subresourceRange.levelCount = VK_REMAINING_MIP_LEVELS;
    b.subresourceRange.layerCount = VK_REMAINING_ARRAY_LAYERS;
    pvkCmdPipelineBarrier(c, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 0, NULL, 0, NULL, 1, &b);
}

static int64_t g_t_upload, g_uploads;
static void upload_begin(void) {
    VkCommandBufferBeginInfo bi = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    pvkResetCommandPool(g_dev, g_upload_pool, 0);
    bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    pvkBeginCommandBuffer(g_upload_cmd, &bi);
}

/* The queue is shared with the render thread, so submits go through g_lock. */
static void upload_submit(void) {
    VkSubmitInfo si = {VK_STRUCTURE_TYPE_SUBMIT_INFO};
    pvkEndCommandBuffer(g_upload_cmd);
    si.commandBufferCount = 1;
    si.pCommandBuffers = &g_upload_cmd;
    pvkQueueSubmit(g_queue, 1, &si, g_upload_fence);
    pvkWaitForFences(g_dev, 1, &g_upload_fence, VK_TRUE, UINT64_MAX);
    pvkResetFences(g_dev, 1, &g_upload_fence);
}

/* ---- device: resources ---- */
static int buffer_add_gen(oa_buffer *b) {
    VkBufferUsageFlags u = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT | VK_BUFFER_USAGE_INDEX_BUFFER_BIT | VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
    if (b->ngens >= MAX_GENS) return 0;
    if (!make_buffer(&b->gens[b->ngens], b->size, u)) return 0;
    b->gen_used[b->ngens] = 0;
    b->ngens++;
    return 1;
}

typedef struct { const void *mem; uint32_t row, slice; } oa_init;

static HRESULT COM d_create_buffer(obj *d, const uint32_t *desc, const oa_init *init, oa_buffer **out) {
    oa_buffer *b;
    (void)d;
    if (!out) return S_OK_;
    b = (oa_buffer *)new_obj(sizeof(oa_buffer), K_BUFFER);
    b->size = desc[0]; b->usage = desc[1]; b->bind = desc[2]; b->cpu = desc[3]; b->misc = desc[4]; b->stride = desc[5];
    if (b->bind & 4) {
        b->ring = 1;
        b->shadow = zalloc16(b->size);
        if (init) memcpy(b->shadow, init->mem, b->size);
    } else {
        if (!buffer_add_gen(b)) { logf_("buffer %u failed", b->size); free(b); return E_OOM_; }
        if (init) memcpy(b->gens[0].ptr, init->mem, b->size);
    }
    *out = b;
    return S_OK_;
}

static VkImageAspectFlags tex_aspect(const oa_tex *t) {
    return t->is_depth ? (VK_IMAGE_ASPECT_DEPTH_BIT | (t->has_stencil ? VK_IMAGE_ASPECT_STENCIL_BIT : 0)) : VK_IMAGE_ASPECT_COLOR_BIT;
}

static int make_image(oa_tex *t, VkImageUsageFlags usage, VkImageCreateFlags flags, VkImageType type) {
    VkImageCreateInfo ci = {VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};
    VkMemoryRequirements r;
    VkMemoryAllocateInfo ai = {VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    ci.flags = flags;
    ci.imageType = type;
    ci.format = t->vkfmt;
    ci.extent.width = t->w;
    ci.extent.height = t->h;
    ci.extent.depth = t->depth;
    ci.mipLevels = t->mips;
    ci.arrayLayers = t->layers;
    ci.samples = VK_SAMPLE_COUNT_1_BIT;
    ci.tiling = VK_IMAGE_TILING_OPTIMAL;
    ci.usage = usage;
    ci.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    if (pvkCreateImage(g_dev, &ci, NULL, &t->image)) return 0;
    pvkGetImageMemoryRequirements(g_dev, t->image, &r);
    ai.allocationSize = r.size;
    ai.memoryTypeIndex = mem_type(r.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, 0);
    if (pvkAllocateMemory(g_dev, &ai, NULL, &t->mem)) return 0;
    pvkBindImageMemory(g_dev, t->image, t->mem, 0);
    return 1;
}

static uint32_t rows_of(const oa_tex *t, uint32_t h) { return t->block == 4 ? (h + 3) / 4 : h; }
static uint32_t pitch_of(const oa_tex *t, uint32_t w) { return (t->block == 4 ? (w + 3) / 4 : w) * (uint32_t)t->bytes; }

static uint32_t cpu_mip_offset(const oa_tex *t, uint32_t mip) {
    uint32_t off = 0, m;
    for (m = 0; m < mip; m++) off += pitch_of(t, mip_dim(t->w, m)) * rows_of(t, mip_dim(t->h, m)) * mip_dim(t->depth, m);
    return off;
}

static HRESULT create_texture(const uint32_t *desc, const oa_init *init, oa_tex **out, int is3d) {
    /* 2D desc: W H Mips Array Fmt Samples Quality Usage Bind Cpu Misc. 3D desc: W H D Mips Fmt Usage Bind Cpu Misc. */
    oa_tex *t = (oa_tex *)new_obj(sizeof(oa_tex), K_TEX2D);
    uint32_t usage_d3d, bind, misc, cpu;
    fmt_info fi;
    VkImageUsageFlags usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
    VkImageCreateFlags flags = 0;
    t->w = desc[0];
    t->h = desc[1];
    if (is3d) {
        t->depth = desc[2]; t->mips = desc[3]; t->layers = 1; t->fmt = desc[4]; usage_d3d = desc[5]; bind = desc[6]; cpu = desc[7]; misc = desc[8];
    } else {
        t->depth = 1; t->mips = desc[2]; t->layers = desc[3]; t->fmt = desc[4]; usage_d3d = desc[7]; bind = desc[8]; cpu = desc[9]; misc = desc[10];
    }
    (void)cpu;
    t->type3d = (uint32_t)is3d;
    memcpy(t->desc, desc, (is3d ? 9 : 11) * 4);
    if (!t->mips) {
        uint32_t m = t->w > t->h ? t->w : t->h;
        t->mips = 1;
        while (m > 1) { m >>= 1; t->mips++; }
    }
    if (bind & 0x40) { /* depth stencil */
        t->is_depth = 1;
        if (t->fmt == 53 || t->fmt == 55) { t->vkfmt = VK_FORMAT_D16_UNORM; t->bytes = 2; t->block = 1; }
        else if (t->fmt == 39 || t->fmt == 40) { t->vkfmt = VK_FORMAT_D32_SFLOAT; t->bytes = 4; t->block = 1; }
        else { t->vkfmt = g_d24s8; t->bytes = 4; t->block = 1; t->has_stencil = 1; }
        usage |= VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT;
    } else {
        fi = dx_format(t->fmt);
        t->vkfmt = fi.vk; t->block = fi.block; t->bytes = fi.bytes;
        check_format(t->fmt, 0, (bind & 0x20) != 0, t->w, t->h, t->mips);
        flags |= VK_IMAGE_CREATE_MUTABLE_FORMAT_BIT;
        if (bind & 0x20) usage |= VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
    }
    usage |= VK_IMAGE_USAGE_SAMPLED_BIT;
    if (misc & 4) flags |= VK_IMAGE_CREATE_CUBE_COMPATIBLE_BIT;
    /* Anything the CPU maps keeps its contents in plain memory; staging textures have no image at all. */
    if (usage_d3d == 2 || usage_d3d == 3) {
        t->cpu_size = cpu_mip_offset(t, t->mips) * t->layers;
        t->cpu = zalloc16(t->cpu_size);
    }
    if (usage_d3d != 3 && !make_image(t, usage, flags, is3d ? VK_IMAGE_TYPE_3D : VK_IMAGE_TYPE_2D)) {
        logf_("image %ux%u fmt %u failed", t->w, t->h, t->fmt);
        _aligned_free(t->cpu);
        free(t);
        return E_OOM_;
    }
    if (t->image) {
        vk_buffer st = {0};
        LARGE_INTEGER u0, u1;
        QueryPerformanceCounter(&u0);
        EnterCriticalSection(&g_lock);
        upload_begin();
        image_layout(g_upload_cmd, t->image, tex_aspect(t), VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_GENERAL);
        if (init) {
            uint32_t total = 0, sub = 0, layer, mip, off = 0;
            for (layer = 0; layer < t->layers; layer++)
                for (mip = 0; mip < t->mips; mip++)
                    total += pitch_of(t, mip_dim(t->w, mip)) * rows_of(t, mip_dim(t->h, mip)) * mip_dim(t->depth, mip);
            if (!make_buffer(&st, total, VK_BUFFER_USAGE_TRANSFER_SRC_BIT)) { LeaveCriticalSection(&g_lock); return E_OOM_; }
            for (layer = 0; layer < t->layers; layer++)
                for (mip = 0; mip < t->mips; mip++, sub++) {
                    uint32_t w = mip_dim(t->w, mip), h = mip_dim(t->h, mip), dp = mip_dim(t->depth, mip), rows = rows_of(t, h), pitch = pitch_of(t, w), y, z;
                    VkBufferImageCopy c = {0};
                    const uint8_t *src = init[sub].mem;
                    for (z = 0; z < dp; z++)
                        for (y = 0; y < rows; y++) memcpy(st.ptr + off + (uint64_t)z * pitch * rows + (uint64_t)y * pitch, src + (uint64_t)z * init[sub].slice + (uint64_t)y * init[sub].row, pitch);
                    c.bufferOffset = off;
                    c.imageSubresource.aspectMask = t->is_depth ? VK_IMAGE_ASPECT_DEPTH_BIT : VK_IMAGE_ASPECT_COLOR_BIT;
                    c.imageSubresource.mipLevel = mip;
                    c.imageSubresource.baseArrayLayer = layer;
                    c.imageSubresource.layerCount = 1;
                    c.imageExtent.width = w; c.imageExtent.height = h; c.imageExtent.depth = dp;
                    pvkCmdCopyBufferToImage(g_upload_cmd, st.buf, t->image, VK_IMAGE_LAYOUT_GENERAL, 1, &c);
                    off += pitch * rows * dp;
                }
        }
        barrier_all(g_upload_cmd);
        upload_submit();
        LeaveCriticalSection(&g_lock);
        QueryPerformanceCounter(&u1);
        g_t_upload += u1.QuadPart - u0.QuadPart;
        g_uploads++;
        if (st.buf) {
            pvkDestroyBuffer(g_dev, st.buf, NULL);
            pvkFreeMemory(g_dev, st.mem, NULL);
        }
    }
    *out = t;
    return S_OK_;
}

static HRESULT COM d_create_tex2d(obj *d, const uint32_t *desc, const oa_init *init, oa_tex **out) {
    (void)d;
    if (!out) return S_OK_;
    return create_texture(desc, init, out, 0);
}
static HRESULT COM d_create_tex3d(obj *d, const uint32_t *desc, const oa_init *init, oa_tex **out) {
    (void)d;
    if (!out) return S_OK_;
    return create_texture(desc, init, out, 1);
}

static VkImageView make_view(oa_tex *t, VkImageViewType type, VkFormat f, VkImageAspectFlags aspect, uint32_t base_mip, uint32_t mips, uint32_t base_layer, uint32_t layers, int alpha_only) {
    VkImageViewCreateInfo ci = {VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
    VkImageView v = VK_NULL_HANDLE;
    ci.image = t->image;
    ci.viewType = type;
    ci.format = f;
    if (alpha_only) {
        ci.components.r = ci.components.g = ci.components.b = VK_COMPONENT_SWIZZLE_ZERO;
        ci.components.a = VK_COMPONENT_SWIZZLE_R;
    }
    ci.subresourceRange.aspectMask = aspect;
    ci.subresourceRange.baseMipLevel = base_mip;
    ci.subresourceRange.levelCount = mips;
    ci.subresourceRange.baseArrayLayer = base_layer;
    ci.subresourceRange.layerCount = layers;
    if (pvkCreateImageView(g_dev, &ci, NULL, &v)) logf_("view failed fmt %d", f);
    return v;
}

static HRESULT COM d_create_srv(obj *d, oa_tex *t, const uint32_t *desc, oa_view **out) {
    oa_view *v;
    uint32_t fmt = desc ? desc[0] : t->fmt, dim = desc ? desc[1] : (t->type3d ? 8 : 4), base = 0, mips = VK_REMAINING_MIP_LEVELS, bl = 0, ll = t->layers;
    VkImageViewType type = VK_IMAGE_VIEW_TYPE_2D;
    VkFormat f;
    (void)d;
    if (t->o.kind != K_TEX2D) { logf_("SRV of a buffer is not implemented"); return E_NOTIMPL_; }
    if (!out) return S_OK_;
    /* D3D11_SRV_DIMENSION: 2=1D 3=1DARRAY 4=2D 5=2DARRAY 8=3D 9=CUBE */
    if (desc) {
        if (dim == 4 || dim == 8 || dim == 9) { base = desc[2]; mips = desc[3]; }
        else if (dim == 5) { base = desc[2]; mips = desc[3]; bl = desc[4]; ll = desc[5]; }
        else { logf_("SRV dimension %u", dim); return E_NOTIMPL_; }
    } else if (t->layers == 6) dim = 9;
    if (dim == 9) { type = VK_IMAGE_VIEW_TYPE_CUBE; ll = 6; }
    else if (dim == 8) type = VK_IMAGE_VIEW_TYPE_3D;
    else if (dim == 5) type = VK_IMAGE_VIEW_TYPE_2D_ARRAY;
    else ll = 1;
    if (mips == 0xffffffffu) mips = VK_REMAINING_MIP_LEVELS;
    v = (oa_view *)new_obj(sizeof(oa_view), K_SRV);
    v->tex = t;
    o_addref(&t->o);
    f = t->is_depth ? t->vkfmt : (fmt ? dx_format(fmt).vk : t->vkfmt);
    if (t->block == 4) f = t->vkfmt == dx_format(fmt).vk ? f : f;
    v->format = f;
    {
        static uint32_t next_uid;
        v->uid = ++next_uid;
    }
    if (t->image) v->view = make_view(t, type, f, t->is_depth ? VK_IMAGE_ASPECT_DEPTH_BIT : VK_IMAGE_ASPECT_COLOR_BIT, base, mips, bl, ll, fmt == 65);
    *out = v;
    return S_OK_;
}

static HRESULT COM d_create_rtv(obj *d, oa_tex *t, const uint32_t *desc, oa_view **out) {
    oa_view *v;
    uint32_t fmt = desc && desc[0] ? desc[0] : t->fmt, level = desc ? desc[2] : 0;
    (void)d;
    if (!out) return S_OK_;
    v = (oa_view *)new_obj(sizeof(oa_view), K_RTV);
    v->tex = t;
    o_addref(&t->o);
    v->format = dx_format(fmt).vk;
    v->level = level;
    v->w = mip_dim(t->w, level);
    v->h = mip_dim(t->h, level);
    v->view = make_view(t, VK_IMAGE_VIEW_TYPE_2D, v->format, VK_IMAGE_ASPECT_COLOR_BIT, level, 1, 0, 1, 0);
    *out = v;
    return S_OK_;
}

static HRESULT COM d_create_dsv(obj *d, oa_tex *t, const uint32_t *desc, oa_view **out) {
    oa_view *v;
    uint32_t level = desc ? desc[3] : 0;
    (void)d;
    if (!out) return S_OK_;
    v = (oa_view *)new_obj(sizeof(oa_view), K_DSV);
    v->tex = t;
    o_addref(&t->o);
    v->format = t->vkfmt;
    v->level = level;
    v->w = mip_dim(t->w, level);
    v->h = mip_dim(t->h, level);
    v->view = make_view(t, VK_IMAGE_VIEW_TYPE_2D, t->vkfmt, tex_aspect(t), level, 1, 0, 1, 0);
    *out = v;
    return S_OK_;
}

static HRESULT COM d_create_layout(obj *d, const uint32_t *e, UINT n, const void *code, SIZE_T size, oa_layout **out) {
    oa_layout *l;
    UINT i;
    uint32_t next[16] = {0};
    (void)d; (void)code; (void)size;
    if (!out) return S_OK_;
    l = (oa_layout *)new_obj(sizeof(oa_layout), K_LAYOUT);
    l->n = (int)n;
    for (i = 0; i < n && i < 32; i++) {
        const uint32_t *x = e + i * 7;
        oa_elem *o = &l->e[i];
        snprintf(o->name, sizeof(o->name), "%s", (const char *)(uintptr_t)x[0]);
        o->index = x[1]; o->fmt = x[2]; o->slot = x[3]; o->offset = x[4]; o->cls = x[5]; o->step = x[6];
        if (o->offset == 0xffffffffu) o->offset = next[o->slot & 15];
        next[o->slot & 15] = o->offset + (uint32_t)dx_format(o->fmt).bytes;
        check_format(o->fmt, 1, 0, 0, 0, 0);
    }
    *out = l;
    return S_OK_;
}

static HRESULT create_shader(const void *code, SIZE_T size, oa_shader **out, int kind) {
    oa_shader *s = (oa_shader *)new_obj(sizeof(oa_shader), kind);
    uint32_t *spv = NULL;
    size_t words = 0;
    char err[200];
    VkShaderModuleCreateInfo ci = {VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
    if (!oa_dxbc_translate(code, size, &s->info, &spv, &words, err, sizeof(err))) {
        logf_("shader translate failed: %s", err);
        free(s);
        return E_FAIL_;
    }
    ci.codeSize = words * 4;
    ci.pCode = spv;
    if (pvkCreateShaderModule(g_dev, &ci, NULL, &s->module)) { logf_("shader module failed"); free(spv); free(s); return E_FAIL_; }
    free(spv);
    *out = s;
    return S_OK_;
}
static HRESULT COM d_create_vs(obj *d, const void *code, SIZE_T size, void *link, oa_shader **out) { (void)d; (void)link; if (!out) return S_OK_; return create_shader(code, size, out, K_VS); }
static HRESULT COM d_create_ps(obj *d, const void *code, SIZE_T size, void *link, oa_shader **out) { (void)d; (void)link; if (!out) return S_OK_; return create_shader(code, size, out, K_PS); }

static HRESULT create_state(const void *desc, size_t words, oa_state **out, int kind) {
    oa_state *s;
    if (!out) return S_OK_;
    s = (oa_state *)new_obj(sizeof(oa_state), kind);
    memcpy(s->desc, desc, words * 4);
    *out = s;
    return S_OK_;
}
/* The blend description is 2+8*8 words; only the first target is kept unless independent blend is on, so it is stored in full on the side. */
typedef struct { oa_state s; uint32_t rt[64]; } oa_blend;
static HRESULT COM d_create_blend(obj *d, const uint32_t *desc, oa_state **out) {
    oa_blend *b;
    (void)d;
    if (!out) return S_OK_;
    b = (oa_blend *)new_obj(sizeof(oa_blend), K_BLEND);
    b->s.desc[0] = desc[0];
    b->s.desc[1] = desc[1];
    memcpy(b->rt, desc + 2, 64 * 4);
    *out = &b->s;
    return S_OK_;
}
static HRESULT COM d_create_depth(obj *d, const void *desc, oa_state **out) { (void)d; return create_state(desc, 13, out, K_DEPTH); }
static HRESULT COM d_create_raster(obj *d, const void *desc, oa_state **out) { (void)d; return create_state(desc, 10, out, K_RASTER); }

static VkSamplerAddressMode addr_mode(uint32_t m) {
    switch (m) {
    case 1: return VK_SAMPLER_ADDRESS_MODE_REPEAT;
    case 2: return VK_SAMPLER_ADDRESS_MODE_MIRRORED_REPEAT;
    case 3: return VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    case 4: return VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_BORDER;
    default: return VK_SAMPLER_ADDRESS_MODE_MIRROR_CLAMP_TO_EDGE;
    }
}

static VkSampler create_vk_sampler(const uint32_t *x, int force_lod0) {
    VkSamplerCreateInfo ci = {VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
    VkSampler sampler = VK_NULL_HANDLE;
    uint32_t f = x[0];
    const float *fl = (const float *)x;
    ci.magFilter = (f >> 2 & 1) ? VK_FILTER_LINEAR : VK_FILTER_NEAREST;
    ci.minFilter = (f >> 4 & 1) ? VK_FILTER_LINEAR : VK_FILTER_NEAREST;
    ci.mipmapMode = (f & 1) ? VK_SAMPLER_MIPMAP_MODE_LINEAR : VK_SAMPLER_MIPMAP_MODE_NEAREST;
    if (f & 0x40) { ci.magFilter = ci.minFilter = VK_FILTER_LINEAR; ci.mipmapMode = VK_SAMPLER_MIPMAP_MODE_LINEAR; ci.anisotropyEnable = VK_TRUE; ci.maxAnisotropy = (float)x[5]; }
    ci.addressModeU = addr_mode(x[1]);
    ci.addressModeV = addr_mode(x[2]);
    ci.addressModeW = addr_mode(x[3]);
    ci.mipLodBias = fl[4];
    if (f & 0x80) { ci.compareEnable = VK_TRUE; ci.compareOp = (VkCompareOp)(x[6] - 1); }
    ci.borderColor = (fl[10] > 0.5f) ? VK_BORDER_COLOR_FLOAT_OPAQUE_WHITE : (fl[7] > 0.5f ? VK_BORDER_COLOR_FLOAT_OPAQUE_WHITE : VK_BORDER_COLOR_FLOAT_TRANSPARENT_BLACK);
    ci.minLod = fl[11];
    ci.maxLod = fl[12];
    if (force_lod0) {
        ci.minLod = ci.maxLod = ci.mipLodBias = 0.0f;
        ci.anisotropyEnable = VK_FALSE;
    }
    if (pvkCreateSampler(g_dev, &ci, NULL, &sampler)) logf_("sampler failed (lod0=%d)", force_lod0);
    return sampler;
}

static HRESULT COM d_create_sampler(obj *d, const uint32_t *x, oa_state **out) {
    oa_state *s;
    (void)d;
    if (!out) return S_OK_;
    s = (oa_state *)new_obj(sizeof(oa_state), K_SAMPLER);
    memcpy(s->desc, x, 13 * 4);
    s->sampler = create_vk_sampler(x, 0);
    *out = s;
    return S_OK_;
}

static VkSampler sampler_for_draw(oa_state *s, int pixel_stage) {
    /* Preserve vertex and comparison samplers, including the shadow path. */
    if (!g_force_lod0 || !pixel_stage || (s->desc[0] & 0x80)) return s->sampler;
    if (!s->lod0_sampler) {
        s->lod0_sampler = create_vk_sampler(s->desc, 1);
        if (s->lod0_sampler) logf_("DIAG lod0 sampler created filter=%x old bias=%.3f min=%.3f max=%.3f",
            s->desc[0], ((float *)s->desc)[4], ((float *)s->desc)[11], ((float *)s->desc)[12]);
    }
    return s->lod0_sampler ? s->lod0_sampler : s->sampler;
}

static HRESULT COM d_create_predicate(obj *d, const void *desc, oa_pred **out) {
    (void)d; (void)desc;
    if (out) {
        *out = (oa_pred *)new_obj(sizeof(oa_pred), K_PREDICATE);
        (*out)->visible = 1;
    }
    return S_OK_;
}
static HRESULT COM d_check_format(obj *d, UINT fmt, UINT *out) { (void)d; (void)fmt; *out = 0x000FFFFF; return S_OK_; }
static HRESULT COM d_check_msaa(obj *d, UINT fmt, UINT count, UINT *out) { (void)d; (void)fmt; *out = count == 1 ? 1 : 0; return S_OK_; }
static HRESULT COM d_get_private(obj *d, const GUID *g, UINT *size, void *data) { (void)d; (void)g; (void)data; if (size) *size = 0; return DXGI_NOT_FOUND; }
static HRESULT COM d_set_private(obj *d, const GUID *g, UINT size, const void *data) { (void)d; (void)g; (void)size; (void)data; return S_OK_; }
static UINT COM d_feature_level(obj *d) { (void)d; return 0xb000; }
static UINT COM d_flags(obj *d) { (void)d; return 0; }
static HRESULT COM d_removed(obj *d) { (void)d; return S_OK_; }
static void COM d_immediate(obj *d, oa_context **out) { (void)d; o_addref(&g_ctx->o); *out = g_ctx; }
static HRESULT COM d_deferred(obj *d, UINT flags, oa_context **out) {
    oa_context *c;
    (void)d; (void)flags;
    if (!out) return S_OK_;
    c = (oa_context *)new_obj(sizeof(oa_context), K_CONTEXT);
    c->deferred = 1;
    *out = c;
    return S_OK_;
}

/* ---- pipelines ---- */
typedef struct {
    oa_shader *vs, *ps;
    oa_layout *layout;
    oa_state *blend, *depth, *raster;
    uint32_t topology;
    VkFormat rt[8], ds;
} pipe_key;

typedef struct { pipe_key k; VkPipeline p; int used; } pipe_entry;
static pipe_entry *g_pipes;
static uint32_t g_pipes_cap = 1u << 14, g_pipes_n;

typedef struct { oa_shader *vs, *ps; VkPipelineLayout layout; VkDescriptorSetLayout dsl; int used; } prog_entry;
static prog_entry g_progs[1u << 13];

static uint32_t hash_bytes(const void *p, size_t n) {
    const uint8_t *b = p;
    uint32_t h = 2166136261u;
    while (n--) h = (h ^ *b++) * 16777619u;
    return h;
}

static void add_bindings(const oa_shader_info *i, VkDescriptorSetLayoutBinding *b, uint32_t *n, VkShaderStageFlags stage) {
    uint32_t s;
    for (s = 0; s < 16; s++)
        if (i->cb_mask >> s & 1) {
            VkDescriptorSetLayoutBinding *x = &b[(*n)++];
            x->binding = i->binding_base + OA_BIND_CB + s; x->descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC; x->descriptorCount = 1; x->stageFlags = stage; x->pImmutableSamplers = NULL;
        }
    for (s = 0; s < 16; s++)
        if (i->sampler_mask >> s & 1) {
            VkDescriptorSetLayoutBinding *x = &b[(*n)++];
            x->binding = i->binding_base + OA_BIND_SAMPLER + s; x->descriptorType = VK_DESCRIPTOR_TYPE_SAMPLER; x->descriptorCount = 1; x->stageFlags = stage; x->pImmutableSamplers = NULL;
        }
    for (s = 0; s < 32; s++)
        if (i->texture_mask >> s & 1) {
            VkDescriptorSetLayoutBinding *x = &b[(*n)++];
            x->binding = i->binding_base + OA_BIND_TEXTURE + s; x->descriptorType = VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE; x->descriptorCount = 1; x->stageFlags = stage; x->pImmutableSamplers = NULL;
        }
}

static prog_entry *program_of(oa_shader *vs, oa_shader *ps) {
    uint32_t h = hash_bytes(&vs, sizeof(vs)) ^ hash_bytes(&ps, sizeof(ps)) * 31u, m = (1u << 13) - 1, i = h & m;
    VkDescriptorSetLayoutBinding b[128];
    uint32_t n = 0;
    VkDescriptorSetLayoutCreateInfo dci = {VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
    VkPipelineLayoutCreateInfo lci = {VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    VkDescriptorSetLayout dsl;
    while (g_progs[i].used) {
        if (g_progs[i].vs == vs && g_progs[i].ps == ps) return &g_progs[i];
        i = (i + 1) & m;
    }
    add_bindings(&vs->info, b, &n, VK_SHADER_STAGE_VERTEX_BIT);
    if (ps) add_bindings(&ps->info, b, &n, VK_SHADER_STAGE_FRAGMENT_BIT);
    dci.bindingCount = n;
    dci.pBindings = b;
    if (pvkCreateDescriptorSetLayout(g_dev, &dci, NULL, &dsl)) logf_("set layout failed, %u bindings", n);
    lci.setLayoutCount = 1;
    lci.pSetLayouts = &dsl;
    pvkCreatePipelineLayout(g_dev, &lci, NULL, &g_progs[i].layout);
    g_progs[i].vs = vs;
    g_progs[i].ps = ps;
    g_progs[i].dsl = dsl;
    g_progs[i].used = 1;
    return &g_progs[i];
}
static VkPipelineLayout program_layout(oa_shader *vs, oa_shader *ps) { return program_of(vs, ps)->layout; }

static VkBlendFactor blend_factor(uint32_t b) {
    static const VkBlendFactor T[20] = {VK_BLEND_FACTOR_ZERO, VK_BLEND_FACTOR_ZERO, VK_BLEND_FACTOR_ONE, VK_BLEND_FACTOR_SRC_COLOR, VK_BLEND_FACTOR_ONE_MINUS_SRC_COLOR, VK_BLEND_FACTOR_SRC_ALPHA, VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA, VK_BLEND_FACTOR_DST_ALPHA, VK_BLEND_FACTOR_ONE_MINUS_DST_ALPHA, VK_BLEND_FACTOR_DST_COLOR, VK_BLEND_FACTOR_ONE_MINUS_DST_COLOR, VK_BLEND_FACTOR_SRC_ALPHA_SATURATE, VK_BLEND_FACTOR_ZERO, VK_BLEND_FACTOR_ZERO, VK_BLEND_FACTOR_CONSTANT_COLOR, VK_BLEND_FACTOR_ONE_MINUS_CONSTANT_COLOR, VK_BLEND_FACTOR_SRC1_COLOR, VK_BLEND_FACTOR_ONE_MINUS_SRC1_COLOR, VK_BLEND_FACTOR_SRC1_ALPHA, VK_BLEND_FACTOR_ONE_MINUS_SRC1_ALPHA};
    return b < 20 ? T[b] : VK_BLEND_FACTOR_ONE;
}
static VkBlendOp blend_op(uint32_t o) {
    switch (o) { case 2: return VK_BLEND_OP_SUBTRACT; case 3: return VK_BLEND_OP_REVERSE_SUBTRACT; case 4: return VK_BLEND_OP_MIN; case 5: return VK_BLEND_OP_MAX; default: return VK_BLEND_OP_ADD; }
}
static VkStencilOp stencil_op(uint32_t o) {
    static const VkStencilOp T[9] = {VK_STENCIL_OP_KEEP, VK_STENCIL_OP_KEEP, VK_STENCIL_OP_ZERO, VK_STENCIL_OP_REPLACE, VK_STENCIL_OP_INCREMENT_AND_CLAMP, VK_STENCIL_OP_DECREMENT_AND_CLAMP, VK_STENCIL_OP_INVERT, VK_STENCIL_OP_INCREMENT_AND_WRAP, VK_STENCIL_OP_DECREMENT_AND_WRAP};
    return o < 9 ? T[o] : VK_STENCIL_OP_KEEP;
}

static VkPipeline build_pipeline(const pipe_key *k, VkPipelineLayout layout) {
    VkGraphicsPipelineCreateInfo ci = {VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};
    VkPipelineRenderingCreateInfo ri = {VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO};
    VkPipelineShaderStageCreateInfo st[2];
    VkPipelineVertexInputStateCreateInfo vi = {VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    VkPipelineInputAssemblyStateCreateInfo ia = {VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
    VkPipelineViewportStateCreateInfo vp = {VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
    VkPipelineRasterizationStateCreateInfo rs = {VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
    VkPipelineMultisampleStateCreateInfo ms = {VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
    VkPipelineDepthStencilStateCreateInfo ds = {VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO};
    VkPipelineColorBlendStateCreateInfo cb = {VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
    VkPipelineColorBlendAttachmentState att[8];
    VkPipelineDynamicStateCreateInfo dy = {VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO};
    static const VkDynamicState DYN[] = {VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR, VK_DYNAMIC_STATE_STENCIL_REFERENCE, VK_DYNAMIC_STATE_BLEND_CONSTANTS, VK_DYNAMIC_STATE_VERTEX_INPUT_BINDING_STRIDE};
    VkVertexInputBindingDescription vb[16];
    VkVertexInputAttributeDescription va[32];
    uint32_t nb = 0, na = 0, i, j, nrt = 0, seen = 0;
    VkPipeline p = VK_NULL_HANDLE;

    memset(st, 0, sizeof(st));
    st[0].sType = st[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    st[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
    st[0].module = k->vs->module;
    st[0].pName = "main";
    if (k->ps) {
        st[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
        st[1].module = k->ps->module;
        st[1].pName = "main";
    }
    /* Vertex attributes: the layout's elements matched to the shader's inputs by semantic. */
    for (i = 0; k->layout && i < (uint32_t)k->vs->info.input_count; i++) {
        const oa_sig_element *in = &k->vs->info.inputs[i];
        int found = 0;
        for (j = 0; j < (uint32_t)k->layout->n; j++) {
            const oa_elem *e = &k->layout->e[j];
            if (e->index == in->semantic_index && !_stricmp(e->name, in->name)) {
                va[na].location = in->reg;
                va[na].binding = e->slot;
                va[na].format = dx_format(e->fmt).vk;
                va[na].offset = e->offset;
                na++;
                if (!(seen >> e->slot & 1)) {
                    seen |= 1u << e->slot;
                    vb[nb].binding = e->slot;
                    vb[nb].stride = 0;
                    vb[nb].inputRate = e->cls ? VK_VERTEX_INPUT_RATE_INSTANCE : VK_VERTEX_INPUT_RATE_VERTEX;
                    nb++;
                }
                found = 1;
                break;
            }
        }
        if (!found && in->sysval == 0) logf_("vertex shader input %s%u has no layout element", in->name, in->semantic_index);
    }
    vi.vertexBindingDescriptionCount = nb;
    vi.pVertexBindingDescriptions = vb;
    vi.vertexAttributeDescriptionCount = na;
    vi.pVertexAttributeDescriptions = va;
    switch (k->topology) {
    case 1: ia.topology = VK_PRIMITIVE_TOPOLOGY_POINT_LIST; break;
    case 2: ia.topology = VK_PRIMITIVE_TOPOLOGY_LINE_LIST; break;
    case 3: ia.topology = VK_PRIMITIVE_TOPOLOGY_LINE_STRIP; ia.primitiveRestartEnable = VK_TRUE; break;
    case 5: ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_STRIP; ia.primitiveRestartEnable = VK_TRUE; break;
    default: ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST; break;
    }
    vp.viewportCount = vp.scissorCount = 1;
    /* Raster: Fill Cull FrontCCW DepthBias BiasClamp Slope DepthClip Scissor MS AA */
    rs.polygonMode = (k->raster && k->raster->desc[0] == 2) ? VK_POLYGON_MODE_LINE : VK_POLYGON_MODE_FILL;
    rs.cullMode = !k->raster ? VK_CULL_MODE_BACK_BIT : k->raster->desc[1] == 1 ? VK_CULL_MODE_NONE : k->raster->desc[1] == 2 ? VK_CULL_MODE_FRONT_BIT : VK_CULL_MODE_BACK_BIT;
    rs.frontFace = (k->raster && k->raster->desc[2]) ? VK_FRONT_FACE_COUNTER_CLOCKWISE : VK_FRONT_FACE_CLOCKWISE;
    rs.lineWidth = 1.0f;
    if (k->raster) {
        int32_t bias = (int32_t)k->raster->desc[3];
        float clamp_, slope;
        memcpy(&clamp_, &k->raster->desc[4], 4);
        memcpy(&slope, &k->raster->desc[5], 4);
        rs.depthBiasEnable = bias != 0 || slope != 0.0f;
        rs.depthBiasConstantFactor = (float)bias;
        rs.depthBiasClamp = clamp_;
        rs.depthBiasSlopeFactor = slope;
        rs.depthClampEnable = !k->raster->desc[6];
    }
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
    /* Depth: Enable Write Func StencilEnable RW(bytes) Front(4) Back(4) */
    if (k->depth) {
        const uint32_t *d = k->depth->desc;
        ds.depthTestEnable = d[0] != 0;
        ds.depthWriteEnable = d[0] != 0 && d[1] != 0;
        ds.depthCompareOp = d[2] ? (VkCompareOp)(d[2] - 1) : VK_COMPARE_OP_ALWAYS;
        ds.stencilTestEnable = d[3] != 0;
        ds.front.failOp = stencil_op(d[5]); ds.front.depthFailOp = stencil_op(d[6]); ds.front.passOp = stencil_op(d[7]);
        ds.front.compareOp = d[8] ? (VkCompareOp)(d[8] - 1) : VK_COMPARE_OP_ALWAYS;
        ds.front.compareMask = d[4] & 0xff; ds.front.writeMask = (d[4] >> 8) & 0xff;
        ds.back.failOp = stencil_op(d[9]); ds.back.depthFailOp = stencil_op(d[10]); ds.back.passOp = stencil_op(d[11]);
        ds.back.compareOp = d[12] ? (VkCompareOp)(d[12] - 1) : VK_COMPARE_OP_ALWAYS;
        ds.back.compareMask = ds.front.compareMask; ds.back.writeMask = ds.front.writeMask;
    } else {
        ds.depthTestEnable = VK_TRUE;
        ds.depthWriteEnable = VK_TRUE;
        ds.depthCompareOp = VK_COMPARE_OP_LESS;
    }
    /* Blend: AlphaToCoverage Independent then 8 targets of Enable Src Dst Op SrcA DstA OpA Mask */
    memset(att, 0, sizeof(att));
    for (i = 0; i < 8; i++) {
        if (k->rt[i]) nrt = i + 1;
    }
    for (i = 0; i < nrt; i++) {
        const uint32_t *r = NULL;
        if (k->blend) {
            const oa_blend *bl = (const oa_blend *)k->blend;
            r = bl->rt + (bl->s.desc[1] ? i : 0) * 8;
        }
        att[i].colorWriteMask = r ? (r[7] & 0xf) : 0xf;
        if (r && r[0]) {
            att[i].blendEnable = VK_TRUE;
            att[i].srcColorBlendFactor = blend_factor(r[1]);
            att[i].dstColorBlendFactor = blend_factor(r[2]);
            att[i].colorBlendOp = blend_op(r[3]);
            att[i].srcAlphaBlendFactor = blend_factor(r[4]);
            att[i].dstAlphaBlendFactor = blend_factor(r[5]);
            att[i].alphaBlendOp = blend_op(r[6]);
        }
    }
    cb.attachmentCount = nrt;
    cb.pAttachments = att;
    dy.dynamicStateCount = 5;
    dy.pDynamicStates = DYN;
    ri.colorAttachmentCount = nrt;
    ri.pColorAttachmentFormats = k->rt;
    ri.depthAttachmentFormat = k->ds;
    if (k->ds == g_d24s8) ri.stencilAttachmentFormat = k->ds;
    ci.pNext = &ri;
    ci.stageCount = k->ps ? 2 : 1;
    ci.pStages = st;
    ci.pVertexInputState = &vi;
    ci.pInputAssemblyState = &ia;
    ci.pViewportState = &vp;
    ci.pRasterizationState = &rs;
    ci.pMultisampleState = &ms;
    ci.pDepthStencilState = &ds;
    ci.pColorBlendState = &cb;
    ci.pDynamicState = &dy;
    ci.layout = layout;
    if (pvkCreateGraphicsPipelines(g_dev, g_pcache, 1, &ci, NULL, &p)) logf_("pipeline failed");
    return p;
}

static VkPipeline get_pipeline(const pipe_key *k) {
    uint32_t m = g_pipes_cap - 1, i = hash_bytes(k, sizeof(*k)) & m;
    while (g_pipes[i].used) {
        if (!memcmp(&g_pipes[i].k, k, sizeof(*k))) return g_pipes[i].p;
        i = (i + 1) & m;
    }
    if (g_pipes_n + 1 >= g_pipes_cap) { logf_("pipeline table full"); return VK_NULL_HANDLE; }
    g_pipes[i].k = *k;
    g_pipes[i].p = build_pipeline(k, program_layout(k->vs, k->ps));
    g_pipes[i].used = 1;
    g_pipes_n++;
    return g_pipes[i].p;
}

/* ---- context: state ---- */
static void end_rendering(oa_context *c) {
    if (c->rendering) {
        pvkCmdEndRendering(g_cur->cmd);
        c->rendering = 0;
    }
}

static void begin_rendering(oa_context *c) {
    VkRenderingInfo ri = {VK_STRUCTURE_TYPE_RENDERING_INFO};
    VkRenderingAttachmentInfo col[8], dep = {VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO};
    uint32_t i, n = 0, w = 0, h = 0;
    if (c->rendering) return;
    barrier_all(g_cur->cmd);
    memset(col, 0, sizeof(col));
    for (i = 0; i < 8; i++) {
        col[i].sType = VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO;
        col[i].imageLayout = VK_IMAGE_LAYOUT_GENERAL;
        col[i].loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
        col[i].storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        if (c->rtv[i]) {
            col[i].imageView = c->rtv[i]->view;
            n = i + 1;
            w = c->rtv[i]->w;
            h = c->rtv[i]->h;
        }
    }
    if (c->dsv) { w = c->dsv->w; h = c->dsv->h; }
    ri.renderArea.extent.width = w;
    ri.renderArea.extent.height = h;
    ri.layerCount = 1;
    ri.colorAttachmentCount = n;
    ri.pColorAttachments = col;
    if (c->dsv) {
        dep.imageView = c->dsv->view;
        dep.imageLayout = VK_IMAGE_LAYOUT_GENERAL;
        dep.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
        dep.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        ri.pDepthAttachment = &dep;
        if (c->dsv->tex->has_stencil) ri.pStencilAttachment = &dep;
    }
    pvkCmdBeginRendering(g_cur->cmd, &ri);
    c->rendering = 1;
    c->pipeline_valid = 0;
}

static void clear_refs(void **p, int n) { memset(p, 0, (size_t)n * sizeof(void *)); }

static void COM c_set_vs_cb(oa_context *c, UINT s, UINT n, oa_buffer *const *b) { UINT i; for (i = 0; i < n && s + i < 14; i++) c->vs_cb[s + i] = b ? b[i] : NULL; }
static void COM c_set_ps_cb(oa_context *c, UINT s, UINT n, oa_buffer *const *b) { UINT i; for (i = 0; i < n && s + i < 14; i++) c->ps_cb[s + i] = b ? b[i] : NULL; }
static void COM c_set_vs_srv(oa_context *c, UINT s, UINT n, oa_view *const *v) { UINT i; for (i = 0; i < n && s + i < 32; i++) c->vs_srv[s + i] = v ? v[i] : NULL; }
static void COM c_set_ps_srv(oa_context *c, UINT s, UINT n, oa_view *const *v) { UINT i; for (i = 0; i < n && s + i < 32; i++) c->ps_srv[s + i] = v ? v[i] : NULL; }
static void COM c_set_vs_smp(oa_context *c, UINT s, UINT n, oa_state *const *v) { UINT i; for (i = 0; i < n && s + i < 16; i++) c->vs_smp[s + i] = v ? v[i] : NULL; }
static void COM c_set_ps_smp(oa_context *c, UINT s, UINT n, oa_state *const *v) { UINT i; for (i = 0; i < n && s + i < 16; i++) c->ps_smp[s + i] = v ? v[i] : NULL; }
static void COM c_set_vs(oa_context *c, oa_shader *s, void *i, UINT n) { (void)i; (void)n; c->vs = s; }
static void COM c_set_ps(oa_context *c, oa_shader *s, void *i, UINT n) { (void)i; (void)n; c->ps = s; }
static void COM c_set_layout(oa_context *c, oa_layout *l) { c->layout = l; }
static void COM c_set_vb(oa_context *c, UINT s, UINT n, oa_buffer *const *b, const UINT *st, const UINT *of) {
    UINT i;
    for (i = 0; i < n && s + i < 16; i++) {
        c->vb[s + i] = b ? b[i] : NULL;
        c->vb_stride[s + i] = st ? st[i] : 0;
        c->vb_off[s + i] = of ? of[i] : 0;
    }
}
static void COM c_set_ib(oa_context *c, oa_buffer *b, UINT f, UINT o) { c->ib = b; c->ib_fmt = f; c->ib_off = o; }
static void COM c_set_topo(oa_context *c, UINT t) { c->topology = t; }
static void COM c_set_blend(oa_context *c, oa_state *b, const float *f, UINT m) { (void)m; c->blend = b; if (f) memcpy(c->blend_factor, f, 16); }
static void COM c_set_depth(oa_context *c, oa_state *d, UINT r) { c->depth = d; c->stencil_ref = r; }
static void COM c_set_raster(oa_context *c, oa_state *r) { c->raster = r; }
static void COM c_set_viewports(oa_context *c, UINT n, const float *v) {
    if (!n) return;
    c->vp.x = v[0];
    c->vp.y = v[1] + v[3];
    c->vp.width = v[2];
    c->vp.height = -v[3];
    c->vp.minDepth = v[4];
    c->vp.maxDepth = v[5];
    c->have_vp = 1;
}
static void COM c_set_scissors(oa_context *c, UINT n, const LONG *r) {
    if (!n) return;
    c->scissor.offset.x = r[0];
    c->scissor.offset.y = r[1];
    c->scissor.extent.width = (uint32_t)(r[2] - r[0]);
    c->scissor.extent.height = (uint32_t)(r[3] - r[1]);
    c->have_scissor = 1;
}
static void COM c_set_rts(oa_context *c, UINT n, oa_view *const *v, oa_view *d) {
    UINT i;
    int changed = c->dsv != d;
    for (i = 0; i < 8; i++) {
        oa_view *nv = (v && i < n) ? v[i] : NULL;
        if (c->rtv[i] != nv) changed = 1;
        c->rtv[i] = nv;
    }
    c->dsv = d;
    if (changed && !c->deferred) end_rendering(c);
}
static void COM c_clear_state(oa_context *c) {
    if (!c->deferred && g_cur) end_rendering(c);
    clear_refs((void **)c->vs_cb, 14); clear_refs((void **)c->ps_cb, 14);
    clear_refs((void **)c->vs_srv, 32); clear_refs((void **)c->ps_srv, 32);
    clear_refs((void **)c->vs_smp, 16); clear_refs((void **)c->ps_smp, 16);
    clear_refs((void **)c->vb, 16); clear_refs((void **)c->rtv, 8);
    c->vs = c->ps = NULL; c->layout = NULL; c->blend = c->depth = c->raster = NULL;
    c->ib = NULL; c->dsv = NULL; c->topology = 0; c->have_vp = c->have_scissor = 0;
    c->stencil_ref = 0;
    c->blend_factor[0] = c->blend_factor[1] = c->blend_factor[2] = c->blend_factor[3] = 1.0f;
}
static void COM c_flush(oa_context *c) { (void)c; }

/* Predication uses results from a finished frame, not this frame, so an object coming into view can appear a frame or two late. */
static void COM c_begin(oa_context *c, oa_pred *q) { c->q_active = q; }
static void COM c_end(oa_context *c, oa_pred *q) { (void)q; c->q_active = NULL; }
/* The engine passes FALSE: skip rendering when the predicate says nothing passed. */
static void COM c_set_predication(oa_context *c, oa_pred *q, BOOL v) { c->pred = v ? NULL : q; }

/* ---- map ---- */
typedef struct { void *p; UINT row, slice; } oa_mapped;

static HRESULT map_i(oa_context *c, obj *res, UINT sub, UINT type, UINT flags, oa_mapped *m) {
    (void)c; (void)flags;
    if (res->kind == K_BUFFER) {
        oa_buffer *b = (oa_buffer *)res;
        if (b->ring) {
            m->p = b->shadow;
        } else {
            if (type == 4 && b->gen_used[b->cur] >= g_done_frame && b->gen_used[b->cur] != 0) {
                /* Discard: move to a copy the GPU is not reading. */
                int i, found = -1;
                for (i = 0; i < b->ngens; i++)
                    if (b->gen_used[i] == 0 || b->gen_used[i] <= g_done_frame) { found = i; break; }
                if (found < 0) {
                    if (buffer_add_gen(b)) found = b->ngens - 1;
                    else { logf_("out of generations, buffer %u", b->size); found = b->cur; }
                }
                b->cur = found;
            }
            m->p = b->gens[b->cur].ptr;
        }
        m->row = m->slice = b->size;
        return S_OK_;
    }
    if (res->kind == K_TEX2D) {
        oa_tex *t = (oa_tex *)res;
        uint32_t mip = sub % t->mips, layer = sub / t->mips, w = mip_dim(t->w, mip), h = mip_dim(t->h, mip);
        if (!t->cpu) { logf_("Map of a texture with no CPU copy"); return E_FAIL_; }
        m->row = pitch_of(t, w);
        m->slice = m->row * rows_of(t, h);
        m->p = t->cpu + cpu_mip_offset(t, mip) + (t->cpu_size / t->layers) * layer;
        t->upload_mip = (int)sub;
        return S_OK_;
    }
    return E_FAIL_;
}

static void upload_region(oa_tex *t, uint32_t sub, const uint8_t *src, uint32_t row, uint32_t dx, uint32_t dy, uint32_t w, uint32_t h, oa_context *c) {
    uint32_t mip = sub % t->mips, layer = sub / t->mips, rows = rows_of(t, h), pitch = pitch_of(t, w), y;
    VkBuffer buf;
    uint32_t off;
    uint8_t *dst;
    VkBufferImageCopy r = {0};
    end_rendering(c);
    dst = ring_alloc(pitch * rows, &buf, &off);
    for (y = 0; y < rows; y++) memcpy(dst + (uint64_t)y * pitch, src + (uint64_t)y * row, pitch);
    r.bufferOffset = off;
    r.imageSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    r.imageSubresource.mipLevel = mip;
    r.imageSubresource.baseArrayLayer = layer;
    r.imageSubresource.layerCount = 1;
    r.imageOffset.x = (int32_t)dx;
    r.imageOffset.y = (int32_t)dy;
    r.imageExtent.width = w;
    r.imageExtent.height = h;
    r.imageExtent.depth = 1;
    barrier_all(g_cur->cmd);
    pvkCmdCopyBufferToImage(g_cur->cmd, buf, t->image, VK_IMAGE_LAYOUT_GENERAL, 1, &r);
    barrier_all(g_cur->cmd);
}

static void unmap_i(oa_context *c, obj *res, UINT sub) {
    if (res->kind == K_BUFFER) {
        oa_buffer *b = (oa_buffer *)res;
        if (b->ring) b->dirty = 1; /* copied when a draw uses it, so a skipped draw costs nothing */
        return;
    }
    if (res->kind == K_TEX2D) {
        oa_tex *t = (oa_tex *)res;
        if (t->image && t->cpu) {
            uint32_t mip = sub % t->mips, layer = sub / t->mips, w = mip_dim(t->w, mip), h = mip_dim(t->h, mip);
            upload_region(t, sub, t->cpu + cpu_mip_offset(t, mip) + (t->cpu_size / t->layers) * layer, pitch_of(t, w), 0, 0, w, h, c);
        }
    }
}

static void COM c_copy_subresource(oa_context *c, obj *dst, UINT dsub, UINT x, UINT y, UINT z, obj *src, UINT ssub, const uint32_t *box) {
    oa_tex *d = (oa_tex *)dst, *s = (oa_tex *)src;
    static int warned;
    (void)z;
    if (dst->kind != K_TEX2D || src->kind != K_TEX2D) { if (!warned++) logf_("CopySubresourceRegion on buffers is not implemented"); return; }
    if (d->image && s->cpu) {
        uint32_t mip = ssub % s->mips, layer = ssub / s->mips, sw = mip_dim(s->w, mip), sh = mip_dim(s->h, mip), bx = box ? box[0] : 0, by = box ? box[1] : 0;
        uint32_t w = box ? box[3] - box[0] : sw, h = box ? box[4] - box[1] : sh, row = pitch_of(s, sw);
        const uint8_t *p = s->cpu + cpu_mip_offset(s, mip) + (s->cpu_size / s->layers) * layer;
        p += (uint64_t)(s->block == 4 ? by / 4 : by) * row + (uint64_t)(s->block == 4 ? bx / 4 : bx) * (uint32_t)s->bytes;
        upload_region(d, dsub, p, row, x, y, w, h, c);
    } else if (d->image && s->image) {
        VkImageCopy r = {0};
        uint32_t smip = ssub % s->mips, dmip = dsub % d->mips;
        end_rendering(c);
        r.srcSubresource.aspectMask = r.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        r.srcSubresource.mipLevel = smip;
        r.srcSubresource.baseArrayLayer = ssub / s->mips;
        r.srcSubresource.layerCount = 1;
        r.dstSubresource.mipLevel = dmip;
        r.dstSubresource.baseArrayLayer = dsub / d->mips;
        r.dstSubresource.layerCount = 1;
        r.srcOffset.x = box ? (int32_t)box[0] : 0;
        r.srcOffset.y = box ? (int32_t)box[1] : 0;
        r.dstOffset.x = (int32_t)x;
        r.dstOffset.y = (int32_t)y;
        r.extent.width = box ? box[3] - box[0] : mip_dim(s->w, smip);
        r.extent.height = box ? box[4] - box[1] : mip_dim(s->h, smip);
        r.extent.depth = 1;
        barrier_all(g_cur->cmd);
        pvkCmdCopyImage(g_cur->cmd, s->image, VK_IMAGE_LAYOUT_GENERAL, d->image, VK_IMAGE_LAYOUT_GENERAL, 1, &r);
        barrier_all(g_cur->cmd);
    } else if (!warned++) {
        logf_("CopySubresourceRegion readback to CPU is not implemented");
    }
}

static void COM c_clear_rtv(oa_context *c, oa_view *v, const float *col) {
    VkClearColorValue cv;
    VkImageSubresourceRange r = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    if (!v || !v->tex->image) return;
    end_rendering(c);
    memcpy(cv.float32, col, 16);
    r.baseMipLevel = v->level;
    barrier_all(g_cur->cmd);
    pvkCmdClearColorImage(g_cur->cmd, v->tex->image, VK_IMAGE_LAYOUT_GENERAL, &cv, 1, &r);
}

static void COM c_clear_dsv(oa_context *c, oa_view *v, UINT flags, float depth, UINT8 stencil) {
    VkClearDepthStencilValue cv;
    VkImageSubresourceRange r = {0, 0, 1, 0, 1};
    if (!v) return;
    end_rendering(c);
    cv.depth = depth;
    cv.stencil = stencil;
    /* Vulkan clears through the image, so clear both aspects if the image has stencil and only one was asked for, unless that would destroy data. */
    r.aspectMask = ((flags & 1) ? VK_IMAGE_ASPECT_DEPTH_BIT : 0) | (((flags & 2) && v->tex->has_stencil) ? VK_IMAGE_ASPECT_STENCIL_BIT : 0);
    r.baseMipLevel = v->level;
    if (!r.aspectMask) return;
    barrier_all(g_cur->cmd);
    pvkCmdClearDepthStencilImage(g_cur->cmd, v->tex->image, VK_IMAGE_LAYOUT_GENERAL, &cv, 1, &r);
}

/* ---- draw ---- */
static oa_tex *g_dummy2d, *g_dummycube, *g_dummy3d;
static oa_view *g_null2d, *g_nullcube, *g_null3d;
static oa_state *g_null_sampler;
static vk_buffer g_zero_ubo;

static long g_n_null_srv, g_n_dim_bad, g_n_no_view, g_c_push, g_c_vb, g_c_pipe, g_c_ib;
static int64_t g_t_draw, g_t_map, g_t_unmap;
static struct { const void *shader; uint32_t slot; long n; } g_nulls[24];
static uint32_t g_null_seen[64];

typedef struct {
    VkWriteDescriptorSet w[96];
    VkDescriptorImageInfo img[96];
    VkDescriptorBufferInfo buf[32];
    uint32_t dyn[32];
    uint64_t key[192];
    uint32_t nw, nimg, nbuf, nkey;
} desc_build;

/* Descriptor sets, reused whenever a draw needs the same textures, samplers and buffers. Constant buffer positions are dynamic offsets. */
#define DESC_TABLE (1u << 16)
#define DESC_POOL_SETS 16384u
typedef struct { uint32_t hash, nkey; uint64_t *key; VkDescriptorSet set; } desc_entry;
static desc_entry *g_desc;
static uint32_t g_desc_n;
static VkDescriptorPool g_pool;
static struct { VkDescriptorPool pool; uint64_t frame; } g_old_pools[8];
static long g_c_set_miss, g_c_pools;

static void desc_new_pool(void) {
    VkDescriptorPoolSize sz[3];
    VkDescriptorPoolCreateInfo ci = {VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    uint32_t i;
    if (g_pool) {
        for (i = 0; i < 8; i++)
            if (!g_old_pools[i].pool) { g_old_pools[i].pool = g_pool; g_old_pools[i].frame = g_frame; break; }
        if (i == 8) logf_("too many retired descriptor pools");
    }
    sz[0].type = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC; sz[0].descriptorCount = DESC_POOL_SETS * 6;
    sz[1].type = VK_DESCRIPTOR_TYPE_SAMPLER; sz[1].descriptorCount = DESC_POOL_SETS * 12;
    sz[2].type = VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE; sz[2].descriptorCount = DESC_POOL_SETS * 12;
    ci.maxSets = DESC_POOL_SETS;
    ci.poolSizeCount = 3;
    ci.pPoolSizes = sz;
    if (pvkCreateDescriptorPool(g_dev, &ci, NULL, &g_pool)) logf_("descriptor pool failed");
    if (!g_desc) g_desc = calloc(DESC_TABLE, sizeof(desc_entry));
    for (i = 0; i < DESC_TABLE; i++) {
        free(g_desc[i].key);
        g_desc[i].key = NULL;
    }
    g_desc_n = 0;
    g_c_pools++;
}

static void desc_retire_pools(void) {
    uint32_t i;
    for (i = 0; i < 8; i++)
        if (g_old_pools[i].pool && g_old_pools[i].frame + FRAMES + 2 < g_frame && g_old_pools[i].frame <= g_done_frame) {
            pvkDestroyDescriptorPool(g_dev, g_old_pools[i].pool, NULL);
            g_old_pools[i].pool = VK_NULL_HANDLE;
        }
}

static VkDescriptorSet desc_get(const prog_entry *prog, desc_build *d) {
    uint32_t h = 2166136261u, i, m = DESC_TABLE - 1, at;
    VkDescriptorSetAllocateInfo ai = {VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
    VkDescriptorSet set = VK_NULL_HANDLE;
    d->key[d->nkey++] = (uint64_t)prog->dsl;
    for (i = 0; i < d->nkey; i++) h = (h ^ (uint32_t)d->key[i] ^ (uint32_t)(d->key[i] >> 32)) * 16777619u;
    at = h & m;
    while (g_desc[at].key) {
        if (g_desc[at].hash == h && g_desc[at].nkey == d->nkey && !memcmp(g_desc[at].key, d->key, d->nkey * 8)) return g_desc[at].set;
        at = (at + 1) & m;
    }
    if (g_desc_n >= DESC_POOL_SETS - 1) {
        desc_new_pool();
        at = h & m;
    }
    ai.descriptorPool = g_pool;
    ai.descriptorSetCount = 1;
    ai.pSetLayouts = &prog->dsl;
    if (pvkAllocateDescriptorSets(g_dev, &ai, &set)) {
        desc_new_pool();
        at = h & m;
        ai.descriptorPool = g_pool;
        if (pvkAllocateDescriptorSets(g_dev, &ai, &set)) { logf_("descriptor set allocation failed"); return VK_NULL_HANDLE; }
    }
    for (i = 0; i < d->nw; i++) d->w[i].dstSet = set;
    if (d->nw) pvkUpdateDescriptorSets(g_dev, d->nw, d->w, 0, NULL);
    g_desc[at].hash = h;
    g_desc[at].nkey = d->nkey;
    g_desc[at].key = malloc(d->nkey * 8);
    memcpy(g_desc[at].key, d->key, d->nkey * 8);
    g_desc[at].set = set;
    g_desc_n++;
    g_c_set_miss++;
    return set;
}

static void write_stage(desc_build *d, const oa_shader_info *i, oa_buffer **cbs, oa_view **srv, oa_state **smp) {
    uint32_t s;
    for (s = 0; s < 16; s++)
        if (i->cb_mask >> s & 1) {
            VkWriteDescriptorSet *w = &d->w[d->nw++];
            VkDescriptorBufferInfo *b = &d->buf[d->nbuf++];
            oa_buffer *x = s < 14 ? cbs[s] : NULL;
            memset(w, 0, sizeof(*w));
            w->sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            w->dstBinding = i->binding_base + OA_BIND_CB + s;
            w->descriptorCount = 1;
            w->descriptorType = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC;
            w->pBufferInfo = b;
            if (x && x->ring) {
                if (x->ring_frame != g_frame || x->dirty) {
                    void *p = ring_alloc(x->size, &x->ring_buf, &x->ring_off);
                    memcpy(p, x->shadow, x->size);
                    x->ring_frame = g_frame;
                    x->dirty = 0;
                }
                b->buffer = x->ring_buf;
                b->offset = 0;
                b->range = x->size;
                d->dyn[d->nbuf - 1] = x->ring_off;
            } else if (x) {
                b->buffer = x->gens[x->cur].buf;
                b->offset = 0;
                b->range = x->size;
                d->dyn[d->nbuf - 1] = 0;
                x->gen_used[x->cur] = g_frame;
            } else {
                b->buffer = g_zero_ubo.buf;
                b->offset = 0;
                b->range = 65536;
                d->dyn[d->nbuf - 1] = 0;
            }
            d->key[d->nkey++] = (uint64_t)b->buffer;
            d->key[d->nkey++] = b->range;
        }
    for (s = 0; s < 16; s++)
        if (i->sampler_mask >> s & 1) {
            VkWriteDescriptorSet *w = &d->w[d->nw++];
            VkDescriptorImageInfo *g = &d->img[d->nimg++];
            memset(w, 0, sizeof(*w));
            memset(g, 0, sizeof(*g));
            w->sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            w->dstBinding = i->binding_base + OA_BIND_SAMPLER + s;
            w->descriptorCount = 1;
            w->descriptorType = VK_DESCRIPTOR_TYPE_SAMPLER;
            w->pImageInfo = g;
            g->sampler = sampler_for_draw(smp[s] ? smp[s] : g_null_sampler, i->is_pixel);
            d->key[d->nkey++] = (uint64_t)g->sampler;
        }
    for (s = 0; s < 32; s++)
        if (i->texture_mask >> s & 1) {
            VkWriteDescriptorSet *w = &d->w[d->nw++];
            VkDescriptorImageInfo *g = &d->img[d->nimg++];
            oa_view *v = srv[s];
            if (!v || !v->view) {
                int ni;
                if (v) g_n_no_view++;
                else g_n_null_srv++;
                for (ni = 0; ni < 24; ni++) {
                    if (!g_nulls[ni].shader) {
                        g_nulls[ni].shader = i;
                        g_nulls[ni].slot = s;
                        logf_("texture slot unbound: %s shader %p t%u dim %d, view object %p", i->is_pixel ? "pixel" : "vertex", (const void *)i, s, i->texture_dim[s], (void *)v);
                    }
                    if (g_nulls[ni].shader == i && g_nulls[ni].slot == s) { g_nulls[ni].n++; break; }
                }
                v = i->texture_dim[s] == 6 ? g_nullcube : i->texture_dim[s] == 5 ? g_null3d : g_null2d;
            } else {
                int want = i->texture_dim[s], have = v->tex->type3d ? 5 : v->tex->layers == 6 ? 6 : 3;
                if (want != have) {
                    uint32_t key = (uint32_t)want * 16u + (uint32_t)have, h;
                    g_n_dim_bad++;
                    for (h = 0; h < 64 && g_null_seen[h] && g_null_seen[h] != key; h++) {}
                    if (h < 64 && !g_null_seen[h]) { g_null_seen[h] = key; logf_("texture dimension mismatch: shader wants %d, bound %ux%u layers %u", want, v->tex->w, v->tex->h, v->tex->layers); }
                    v = want == 6 ? g_nullcube : want == 5 ? g_null3d : g_null2d;
                }
            }
            memset(w, 0, sizeof(*w));
            memset(g, 0, sizeof(*g));
            w->sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            w->dstBinding = i->binding_base + OA_BIND_TEXTURE + s;
            w->descriptorCount = 1;
            w->descriptorType = VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE;
            w->pImageInfo = g;
            g->imageView = v->view;
            g->imageLayout = VK_IMAGE_LAYOUT_GENERAL;
            d->key[d->nkey++] = v->uid;
        }
}

static long g_n_draw, g_n_skip_vs, g_n_skip_rt, g_n_skip_pipe, g_n_clear, g_n_skip_ib, g_n_skip_query, g_n_query_kept;

static int prepare_draw(oa_context *c) {
    VkCommandBuffer cmd;
    pipe_key k;
    VkPipeline p;
    uint32_t i;
    static desc_build d;
    if (c->deferred) return 0;
    if (c->q_active) g_n_query_kept++;
    if (!c->vs) { g_n_skip_vs++; return 0; }
    if (!c->rtv[0] && !c->dsv) { g_n_skip_rt++; return 0; }
    begin_rendering(c);
    cmd = g_cur->cmd;
    memset(&k, 0, sizeof(k));
    k.vs = c->vs; k.ps = c->ps; k.layout = c->layout; k.blend = c->blend; k.depth = c->depth; k.raster = c->raster; k.topology = c->topology;
    for (i = 0; i < 8; i++) k.rt[i] = c->rtv[i] ? c->rtv[i]->format : VK_FORMAT_UNDEFINED;
    k.ds = c->dsv ? c->dsv->format : VK_FORMAT_UNDEFINED;
    p = get_pipeline(&k);
    if (!p) { g_n_skip_pipe++; return 0; }
    g_n_draw++;
    if (!c->pipeline_valid || p != c->last_pipeline) {
        pvkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, p);
        g_c_pipe++;
        c->last_pipeline = p;
        c->pipeline_valid = 1;
    }
    if (!c->cache_valid) {
        memset(&c->set_vp, 0, sizeof(c->set_vp));
        memset(&c->set_scissor, 0, sizeof(c->set_scissor));
        c->set_stencil = 0xffffffffu;
        c->set_blend[0] = -1.0f;
        memset(c->set_vb, 0, sizeof(c->set_vb));
        c->set_ib = VK_NULL_HANDLE;
        c->set_layout = VK_NULL_HANDLE;
        c->set_desc = VK_NULL_HANDLE;
        c->cache_valid = 1;
    }
    if (c->have_vp && memcmp(&c->vp, &c->set_vp, sizeof(c->vp))) { pvkCmdSetViewport(cmd, 0, 1, &c->vp); c->set_vp = c->vp; }
    {
        VkRect2D r;
        if (c->raster && c->raster->desc[7] && c->have_scissor) r = c->scissor;
        else {
            r.offset.x = r.offset.y = 0;
            r.extent.width = c->rtv[0] ? c->rtv[0]->w : c->dsv->w;
            r.extent.height = c->rtv[0] ? c->rtv[0]->h : c->dsv->h;
        }
        if (memcmp(&r, &c->set_scissor, sizeof(r))) { pvkCmdSetScissor(cmd, 0, 1, &r); c->set_scissor = r; }
    }
    if (c->stencil_ref != c->set_stencil) { pvkCmdSetStencilReference(cmd, VK_STENCIL_FACE_FRONT_AND_BACK, c->stencil_ref); c->set_stencil = c->stencil_ref; }
    if (memcmp(c->blend_factor, c->set_blend, 16)) { pvkCmdSetBlendConstants(cmd, c->blend_factor); memcpy(c->set_blend, c->blend_factor, 16); }
    {
        VkBuffer bufs[4];
        VkDeviceSize offs[4], strides[4], sizes[4];
        int changed = 0;
        for (i = 0; i < 4; i++) {
            oa_buffer *b = c->vb[i];
            if (b && !b->ring) {
                bufs[i] = b->gens[b->cur].buf;
                offs[i] = c->vb_off[i];
                strides[i] = c->vb_stride[i];
                b->gen_used[b->cur] = g_frame;
            } else {
                bufs[i] = g_zero_ubo.buf;
                offs[i] = 0;
                strides[i] = 0;
            }
            sizes[i] = VK_WHOLE_SIZE;
            if (bufs[i] != c->set_vb[i] || offs[i] != c->set_off[i] || strides[i] != c->set_stride[i]) changed = 1;
        }
        if (changed) {
            pvkCmdBindVertexBuffers2(cmd, 0, 4, bufs, offs, sizes, strides);
            g_c_vb++;
            memcpy(c->set_vb, bufs, sizeof(bufs));
            memcpy(c->set_off, offs, sizeof(offs));
            memcpy(c->set_stride, strides, sizeof(strides));
        }
    }
    d.nw = d.nimg = d.nbuf = d.nkey = 0;
    /* Pixel bindings are numbered first, and dynamic offsets go in binding order. */
    if (c->ps) write_stage(&d, &c->ps->info, c->ps_cb, c->ps_srv, c->ps_smp);
    write_stage(&d, &c->vs->info, c->vs_cb, c->vs_srv, c->vs_smp);
    if (d.nw) {
        const prog_entry *prog = program_of(c->vs, c->ps);
        VkDescriptorSet set = desc_get(prog, &d);
        if (set != c->set_desc || prog->layout != c->set_layout || d.nbuf != c->set_ndyn || memcmp(d.dyn, c->set_dyn, d.nbuf * 4)) {
            pvkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, prog->layout, 0, 1, &set, d.nbuf, d.dyn);
            g_c_push++;
            c->set_desc = set;
            c->set_layout = prog->layout;
            c->set_ndyn = d.nbuf;
            memcpy(c->set_dyn, d.dyn, d.nbuf * 4);
        }
    }
    return 1;
}

static int pred_skips(const oa_context *c) {
    const oa_pred *p = c->pred;
    if (!p || !g_cull || p->visible || p->tested_frame + 8 < g_frame) return 0;
    g_n_culled++;
    return 1;
}

/* Hidden objects are tested every frame. Visible ones only every 4th, since each test costs two Vulkan calls. */
static int query_begin(oa_context *c) {
    oa_pred *p = c->q_active;
    oa_frame *f = g_cur;
    uint32_t i;
    if (!p) return 0;
    if (p->visible && ((g_frame + ((uintptr_t)p >> 6)) & 3)) { g_n_test_skipped++; return 0; }
    if (f->qused >= QUERY_MAX) return 0;
    i = f->qused++;
    f->qlist[i] = p;
    pvkCmdBeginQuery(f->cmd, f->qpool, i, 0);
    g_n_tests++;
    return 1;
}
static void query_end(void) { pvkCmdEndQuery(g_cur->cmd, g_cur->qpool, g_cur->qused - 1); }

static void draw_i(oa_context *c, UINT n, UINT first) {
    int q;
    if (pred_skips(c) || !prepare_draw(c)) return;
    q = query_begin(c);
    pvkCmdDraw(g_cur->cmd, n, 1, first, 0);
    if (q) query_end();
}
static void draw_indexed_i(oa_context *c, UINT n, UINT first, INT base) {
    if (!c->ib || c->ib->ring) { g_n_skip_ib++; return; }
    if (pred_skips(c) || !prepare_draw(c)) return;
    c->ib->gen_used[c->ib->cur] = g_frame;
    {
        VkBuffer b = c->ib->gens[c->ib->cur].buf;
        uint32_t ty = c->ib_fmt == 42 ? VK_INDEX_TYPE_UINT32 : VK_INDEX_TYPE_UINT16;
        if (b != c->set_ib || c->ib_off != c->set_ib_off || ty != c->set_ib_type) {
            pvkCmdBindIndexBuffer(g_cur->cmd, b, c->ib_off, (VkIndexType)ty);
            g_c_ib++;
            c->set_ib = b; c->set_ib_off = c->ib_off; c->set_ib_type = ty;
        }
    }
    {
        int q = query_begin(c);
        pvkCmdDrawIndexed(g_cur->cmd, n, 1, first, base, 0);
        if (q) query_end();
    }
}

static int g_sample;
#define TIMED(store, call) do { if (g_sample) { LARGE_INTEGER t0_, t1_; QueryPerformanceCounter(&t0_); call; QueryPerformanceCounter(&t1_); store += t1_.QuadPart - t0_.QuadPart; } else { call; } } while (0)
static void COM c_draw(oa_context *c, UINT n, UINT first) { TIMED(g_t_draw, draw_i(c, n, first)); }
static void COM c_draw_indexed(oa_context *c, UINT n, UINT first, INT base) { TIMED(g_t_draw, draw_indexed_i(c, n, first, base)); }
static HRESULT COM c_map(oa_context *c, obj *res, UINT sub, UINT type, UINT flags, oa_mapped *m) { HRESULT hr; TIMED(g_t_map, hr = map_i(c, res, sub, type, flags, m)); return hr; }
static void COM c_unmap(oa_context *c, obj *res, UINT sub) { TIMED(g_t_unmap, unmap_i(c, res, sub)); }

/* ---- DXGI ---- */
static HRESULT COM x_get_parent(obj *o, const GUID *iid, void **out) {
    obj *p = o->kind == K_DXGI_DEVICE ? g_adapter : g_factory;
    (void)iid;
    o_addref(p);
    *out = p;
    return S_OK_;
}
static HRESULT COM x_get_adapter(obj *o, void **out) { (void)o; o_addref(g_adapter); *out = g_adapter; return S_OK_; }
static HRESULT COM x_set_priority(obj *o, INT p) { (void)o; (void)p; return S_OK_; }

static HRESULT COM a_enum_outputs(obj *o, UINT i, void **out) { (void)o; (void)i; *out = NULL; return DXGI_NOT_FOUND; }
static HRESULT COM a_get_desc(obj *o, void *desc) {
    VkPhysicalDeviceProperties p;
    uint8_t *d = desc;
    int i;
    (void)o;
    memset(d, 0, 0x124);
    pvkGetPhysicalDeviceProperties(g_phys, &p);
    for (i = 0; i < 127 && p.deviceName[i]; i++) ((wchar_t *)d)[i] = (wchar_t)p.deviceName[i];
    *(uint32_t *)(d + 256) = p.vendorID;
    *(uint32_t *)(d + 260) = p.deviceID;
    *(uint32_t *)(d + 272) = 0x7fffffffu; /* DedicatedVideoMemory: the engine treats small values as a low-spec machine */
    return S_OK_;
}

static int create_swapchain(oa_chain *s) {
    VkSurfaceCapabilitiesKHR cap;
    VkSwapchainCreateInfoKHR ci = {VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR};
    VkSurfaceFormatKHR fmts[32];
    uint32_t n = 32, i;
    VkBool32 sup = 0;
    pvkGetPhysicalDeviceSurfaceSupportKHR(g_phys, g_qfam, s->surface, &sup);
    pvkGetPhysicalDeviceSurfaceCapabilitiesKHR(g_phys, s->surface, &cap);
    pvkGetPhysicalDeviceSurfaceFormatsKHR(g_phys, s->surface, &n, fmts);
    s->swap_fmt = fmts[0].format;
    ci.imageColorSpace = fmts[0].colorSpace;
    for (i = 0; i < n; i++)
        if (fmts[i].format == VK_FORMAT_B8G8R8A8_UNORM || fmts[i].format == VK_FORMAT_R8G8B8A8_UNORM) {
            s->swap_fmt = fmts[i].format;
            ci.imageColorSpace = fmts[i].colorSpace;
            break;
        }
    s->extent = cap.currentExtent;
    if (s->extent.width == 0xffffffffu) { s->extent.width = s->w; s->extent.height = s->h; }
    ci.surface = s->surface;
    ci.minImageCount = cap.minImageCount < 2 ? 2 : cap.minImageCount;
    if (cap.maxImageCount && ci.minImageCount > cap.maxImageCount) ci.minImageCount = cap.maxImageCount;
    ci.imageFormat = s->swap_fmt;
    ci.imageExtent = s->extent;
    ci.imageArrayLayers = 1;
    ci.imageUsage = VK_IMAGE_USAGE_TRANSFER_DST_BIT;
    ci.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
    ci.preTransform = cap.currentTransform;
    ci.compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
    ci.presentMode = VK_PRESENT_MODE_FIFO_KHR;
    ci.clipped = VK_TRUE;
    ci.oldSwapchain = s->swapchain;
    {
        VkSwapchainKHR nw;
        VkResult r = pvkCreateSwapchainKHR(g_dev, &ci, NULL, &nw);
        if (r) { logf_("swapchain failed %d supported %u", r, sup); return 0; }
        if (s->swapchain) pvkDestroySwapchainKHR(g_dev, s->swapchain, NULL);
        s->swapchain = nw;
    }
    s->nimages = 8;
    pvkGetSwapchainImagesKHR(g_dev, s->swapchain, &s->nimages, s->images);
    logf_("swapchain %ux%u format %d images %u", s->extent.width, s->extent.height, s->swap_fmt, s->nimages);
    return 1;
}

static void make_back(oa_chain *s) {
    uint32_t d[11] = {0};
    d[0] = s->w; d[1] = s->h; d[2] = 1; d[3] = 1; d[4] = 28; d[5] = 1; d[7] = 0; d[8] = 0x28;
    create_texture(d, NULL, &s->back, 0);
    s->back->is_backbuffer = 1;
    s->back->fmt = s->fmt;
    s->back->desc[4] = s->fmt;
}

static HRESULT COM f_create_chain(obj *f, obj *device, const uint32_t *desc, oa_chain **out) {
    oa_chain *s = (oa_chain *)new_obj(sizeof(oa_chain), K_CHAIN);
    VkWin32SurfaceCreateInfoKHR si = {VK_STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR};
    (void)f; (void)device;
    s->w = desc[0];
    s->h = desc[1];
    s->fmt = desc[4];
    s->hwnd = (HWND)(uintptr_t)desc[11];
    si.hinstance = GetModuleHandleA(NULL);
    si.hwnd = s->hwnd;
    if (pvkCreateWin32SurfaceKHR(g_instance, &si, NULL, &s->surface)) { logf_("surface failed"); return E_FAIL_; }
    if (!create_swapchain(s)) return E_FAIL_;
    make_back(s);
    logf_("chain %ux%u fmt %u hwnd %p", s->w, s->h, s->fmt, (void *)s->hwnd);
    *out = s;
    return S_OK_;
}
static HRESULT COM f_window_assoc(obj *f, HWND h, UINT flags) { (void)f; (void)h; (void)flags; return S_OK_; }

static HRESULT COM s_get_buffer(oa_chain *s, UINT i, const GUID *iid, void **out) {
    (void)i; (void)iid;
    o_addref(&s->back->o);
    *out = s->back;
    return S_OK_;
}

static uint64_t g_frames_shown;
static int64_t g_t_wait, g_t_acquire, g_t_submit;
static HRESULT COM s_present(oa_chain *s, UINT sync, UINT flags) {
    LARGE_INTEGER q0, q1, q2;
    oa_frame *f = g_cur;
    oa_context *c = g_ctx;
    uint32_t idx = 0;
    VkResult r;
    VkImageBlit b = {0};
    VkSubmitInfo si = {VK_STRUCTURE_TYPE_SUBMIT_INFO};
    VkPresentInfoKHR pi = {VK_STRUCTURE_TYPE_PRESENT_INFO_KHR};
    VkPipelineStageFlags wait = VK_PIPELINE_STAGE_ALL_COMMANDS_BIT;
    (void)sync; (void)flags;
    end_rendering(c);
    QueryPerformanceCounter(&q0);
    r = pvkAcquireNextImageKHR(g_dev, s->swapchain, UINT64_MAX, f->acquired, VK_NULL_HANDLE, &idx);
    QueryPerformanceCounter(&q1);
    g_t_acquire += q1.QuadPart - q0.QuadPart;
    if (r == VK_ERROR_OUT_OF_DATE_KHR) {
        pvkQueueWaitIdle(g_queue);
        create_swapchain(s);
        r = pvkAcquireNextImageKHR(g_dev, s->swapchain, UINT64_MAX, f->acquired, VK_NULL_HANDLE, &idx);
    }
    if (r && r != VK_SUBOPTIMAL_KHR) { logf_("acquire failed %d", r); }
    barrier_all(f->cmd);
    image_layout(f->cmd, s->images[idx], VK_IMAGE_ASPECT_COLOR_BIT, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
    b.srcSubresource.aspectMask = b.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    b.srcSubresource.layerCount = b.dstSubresource.layerCount = 1;
    b.srcOffsets[1].x = (int32_t)s->w; b.srcOffsets[1].y = (int32_t)s->h; b.srcOffsets[1].z = 1;
    b.dstOffsets[1].x = (int32_t)s->extent.width; b.dstOffsets[1].y = (int32_t)s->extent.height; b.dstOffsets[1].z = 1;
    pvkCmdBlitImage(f->cmd, s->back->image, VK_IMAGE_LAYOUT_GENERAL, s->images[idx], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &b, VK_FILTER_LINEAR);
    image_layout(f->cmd, s->images[idx], VK_IMAGE_ASPECT_COLOR_BIT, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR);
    pvkEndCommandBuffer(f->cmd);
    si.waitSemaphoreCount = 1;
    si.pWaitSemaphores = &f->acquired;
    si.pWaitDstStageMask = &wait;
    si.commandBufferCount = 1;
    si.pCommandBuffers = &f->cmd;
    si.signalSemaphoreCount = 1;
    si.pSignalSemaphores = &f->rendered;
    QueryPerformanceCounter(&q1);
    EnterCriticalSection(&g_lock);
    pvkQueueSubmit(g_queue, 1, &si, f->fence);
    f->submitted = 1;
    pi.waitSemaphoreCount = 1;
    pi.pWaitSemaphores = &f->rendered;
    pi.swapchainCount = 1;
    pi.pSwapchains = &s->swapchain;
    pi.pImageIndices = &idx;
    r = pvkQueuePresentKHR(g_queue, &pi);
    LeaveCriticalSection(&g_lock);
    QueryPerformanceCounter(&q2);
    g_t_submit += q2.QuadPart - q1.QuadPart;
    g_sample = (g_frames_shown & 7) == 0;
    if (g_frames_shown % 120 == 0) {
        int want = GetFileAttributesA("Z:\\storage\\emulated\\0\\Download\\oa\\nocull") == INVALID_FILE_ATTRIBUTES && GetFileAttributesA("nocull") == INVALID_FILE_ATTRIBUTES;
        if (want != g_cull) { g_cull = want; logf_("culling %s at frame %llu", want ? "on" : "off", (unsigned long long)g_frames_shown); }
        {
            int force = GetFileAttributesA("Z:\\storage\\emulated\\0\\Download\\oa\\force-lod0") != INVALID_FILE_ATTRIBUTES || GetFileAttributesA("force-lod0") != INVALID_FILE_ATTRIBUTES;
            if (force != g_force_lod0) {
                g_force_lod0 = force;
                logf_("DIAG force-lod0 %s at frame %llu (pixel, noncomparison samplers only)", force ? "ON" : "OFF", (unsigned long long)g_frames_shown);
            }
        }
    }
    if (g_frames_shown % 1800 == 300) CopyFileA(g_game_log, "Z:\\storage\\emulated\\0\\Download\\oa\\game.log", FALSE);
    if (++g_frames_shown % 600 == 1) {
        static DWORD last_tick;
        static long last_draws, last_skipq;
        DWORD now = GetTickCount();
        LARGE_INTEGER fq;
        double ms;
        QueryPerformanceFrequency(&fq);
        ms = 1000.0 / (double)fq.QuadPart / 600.0;
        logf_("frame %llu fps %.1f draws/f %ld skipq/f %ld keptq %ld pipes %u | ms/f gpuwait %.2f acquire %.2f submit %.2f | uploads %lld %.1f ms total | null srv %ld dim bad %ld", (unsigned long long)g_frames_shown, last_tick && now != last_tick ? 600000.0 / (now - last_tick) : 0.0, (g_n_draw - last_draws) / 600, (g_n_skip_query - last_skipq) / 600, g_n_query_kept, g_pipes_n, g_t_wait * ms, g_t_acquire * ms, g_t_submit * ms, (long long)g_uploads, (double)g_t_upload * 1000.0 / (double)fq.QuadPart, g_n_null_srv, g_n_dim_bad);
        logf_("  ms/f draw calls %.2f map %.2f unmap %.2f | per frame bindset %ld newset %ld vb %ld pipe %ld ib %ld | sets %u pools %ld | unbound %ld no-view %ld", g_t_draw * ms * 8, g_t_map * ms * 8, g_t_unmap * ms * 8, g_c_push / 600, g_c_set_miss / 600, g_c_vb / 600, g_c_pipe / 600, g_c_ib / 600, g_desc_n, g_c_pools, g_n_null_srv, g_n_no_view);
        g_c_set_miss = 0;
        logf_("  culling %d: hidden skipped/f %ld tests/f %ld tests saved/f %ld", g_cull, g_n_culled / 600, g_n_tests / 600, g_n_test_skipped / 600);
        g_n_culled = g_n_tests = g_n_test_skipped = 0;
        g_t_draw = g_t_map = g_t_unmap = 0; g_c_push = g_c_vb = g_c_pipe = g_c_ib = 0;
        g_t_wait = g_t_acquire = g_t_submit = 0; g_t_upload = g_uploads = 0;
        last_draws = g_n_draw; last_skipq = g_n_skip_query;
        last_tick = now;
    }
    g_frame++;
    {
        LARGE_INTEGER t0, t1;
        QueryPerformanceCounter(&t0);
        frame_begin();
        QueryPerformanceCounter(&t1);
        g_t_wait += t1.QuadPart - t0.QuadPart;
    }
    c->pipeline_valid = 0;
    c->cache_valid = 0;
    return S_OK_;
}
static HRESULT COM s_get_desc(oa_chain *s, uint32_t *d) {
    memset(d, 0, 15 * 4);
    d[0] = s->w; d[1] = s->h; d[4] = s->fmt; d[7] = 1; d[9] = 0x20; d[10] = 1; d[11] = (uint32_t)(uintptr_t)s->hwnd; d[12] = 1;
    return S_OK_;
}
static HRESULT COM s_set_fullscreen(oa_chain *s, BOOL f, void *t) { (void)s; (void)f; (void)t; return S_OK_; }
static HRESULT COM s_get_fullscreen(oa_chain *s, BOOL *f, void **t) { (void)s; if (f) *f = FALSE; if (t) *t = NULL; return S_OK_; }
static HRESULT COM s_resize(oa_chain *s, UINT n, UINT w, UINT h, UINT fmt, UINT fl) {
    (void)n; (void)fl;
    if (w) s->w = w;
    if (h) s->h = h;
    if (fmt) s->fmt = fmt;
    logf_("ResizeBuffers %ux%u", s->w, s->h);
    end_rendering(g_ctx);
    o_release(&s->back->o);
    make_back(s);
    return S_OK_;
}
static HRESULT COM s_resize_target(oa_chain *s, const void *d) { (void)s; (void)d; return S_OK_; }

/* ---- resource getters ---- */
static void COM t_get_desc(oa_tex *t, uint32_t *d) { memcpy(d, t->desc, (t->type3d ? 9 : 11) * 4); if (!t->type3d) d[2] = t->mips; else d[3] = t->mips; }
static void COM b_get_desc(oa_buffer *b, uint32_t *d) { d[0] = b->size; d[1] = b->usage; d[2] = b->bind; d[3] = b->cpu; d[4] = b->misc; d[5] = b->stride; }
static void COM r_get_type(obj *o, UINT *t) { *t = o->kind == K_BUFFER ? 1 : (((oa_tex *)o)->type3d ? 4 : 3); }
static void COM v_get_resource(oa_view *v, obj **out) { o_addref(&v->tex->o); *out = &v->tex->o; }
static void COM child_get_device(obj *o, obj **out) { (void)o; o_addref(&g_device_obj); *out = &g_device_obj; }

/* ---- setup ---- */
static void init_vtables(void) {
    static const uint8_t CHILD[] = {3, 1, 1, 2, 4, 4, 3, 2, 2, 1, 2, 2, 2, 2, 2};
    static const uint8_t DXGI_DEV[] = {3, 1, 1, 4, 3, 4, 3, 2, 6, 4, 2, 2};
    static const uint8_t ADAPTER[] = {3, 1, 1, 4, 3, 4, 3, 3, 2, 3};
    static const uint8_t FACTORY[] = {3, 1, 1, 4, 3, 4, 3, 3, 3, 2, 4, 3};
    static const uint8_t CHAIN[] = {3, 1, 1, 4, 3, 4, 3, 3, 3, 4, 3, 3, 2, 6, 2, 2, 2, 2};
    void **v;
    int k;
    g_stub_code = VirtualAlloc(NULL, 512 * 24, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
#define COMMON(v) (v)[0] = (void *)o_qi; (v)[1] = (void *)o_addref; (v)[2] = (void *)o_release
    v = make_vtable("Device", DEVICE_NAMES, DEVICE_ARGS, 43);
    COMMON(v);
    v[3] = (void *)d_create_buffer; v[5] = (void *)d_create_tex2d; v[6] = (void *)d_create_tex3d; v[7] = (void *)d_create_srv; v[9] = (void *)d_create_rtv; v[10] = (void *)d_create_dsv;
    v[11] = (void *)d_create_layout; v[12] = (void *)d_create_vs; v[15] = (void *)d_create_ps; v[20] = (void *)d_create_blend; v[21] = (void *)d_create_depth; v[22] = (void *)d_create_raster;
    v[23] = (void *)d_create_sampler; v[25] = (void *)d_create_predicate; v[24] = (void *)d_create_predicate; v[27] = (void *)d_deferred; v[29] = (void *)d_check_format; v[30] = (void *)d_check_msaa;
    v[34] = (void *)d_get_private; v[35] = (void *)d_set_private; v[37] = (void *)d_feature_level; v[38] = (void *)d_flags; v[39] = (void *)d_removed; v[40] = (void *)d_immediate;
    g_vt[K_DEVICE] = v;
    v = make_vtable("Context", NULL, CONTEXT_ARGS, 115);
    COMMON(v);
    v[3] = (void *)child_get_device; v[7] = (void *)c_set_vs_cb; v[8] = (void *)c_set_ps_srv; v[9] = (void *)c_set_ps; v[10] = (void *)c_set_ps_smp; v[11] = (void *)c_set_vs; v[12] = (void *)c_draw_indexed; v[13] = (void *)c_draw;
    v[14] = (void *)c_map; v[15] = (void *)c_unmap; v[16] = (void *)c_set_ps_cb; v[17] = (void *)c_set_layout; v[18] = (void *)c_set_vb; v[19] = (void *)c_set_ib; v[24] = (void *)c_set_topo; v[25] = (void *)c_set_vs_srv; v[26] = (void *)c_set_vs_smp;
    v[27] = (void *)c_begin; v[28] = (void *)c_end; v[30] = (void *)c_set_predication; v[33] = (void *)c_set_rts; v[35] = (void *)c_set_blend; v[36] = (void *)c_set_depth; v[43] = (void *)c_set_raster; v[44] = (void *)c_set_viewports; v[45] = (void *)c_set_scissors;
    v[46] = (void *)c_copy_subresource; v[50] = (void *)c_clear_rtv; v[53] = (void *)c_clear_dsv; v[110] = (void *)c_clear_state; v[111] = (void *)c_flush;
    g_vt[K_CONTEXT] = v;
    v = make_vtable("DXGIDevice", NULL, DXGI_DEV, 12);
    COMMON(v);
    v[6] = (void *)x_get_parent; v[7] = (void *)x_get_adapter; v[10] = (void *)x_set_priority;
    g_vt[K_DXGI_DEVICE] = v;
    v = make_vtable("Adapter", NULL, ADAPTER, 10);
    COMMON(v);
    v[6] = (void *)x_get_parent; v[7] = (void *)a_enum_outputs; v[8] = (void *)a_get_desc;
    g_vt[K_ADAPTER] = v;
    v = make_vtable("Factory", NULL, FACTORY, 12);
    COMMON(v);
    v[6] = (void *)x_get_parent; v[8] = (void *)f_window_assoc; v[10] = (void *)f_create_chain;
    g_vt[K_FACTORY] = v;
    v = make_vtable("SwapChain", NULL, CHAIN, 18);
    COMMON(v);
    v[6] = (void *)x_get_parent; v[7] = (void *)child_get_device; v[8] = (void *)s_present; v[9] = (void *)s_get_buffer; v[10] = (void *)s_set_fullscreen; v[11] = (void *)s_get_fullscreen; v[12] = (void *)s_get_desc; v[13] = (void *)s_resize; v[14] = (void *)s_resize_target;
    g_vt[K_CHAIN] = v;
    /* Resources, views, shaders, states: DeviceChild is 7 slots, then a few getters. */
    for (k = K_BUFFER; k <= K_PREDICATE; k++) {
        static const char *const NAMES[] = {"Buffer", "Texture", "SRV", "RTV", "DSV", "InputLayout", "VS", "PS", "Blend", "DepthState", "Raster", "Sampler", "Predicate"};
        v = make_vtable(NAMES[k - K_BUFFER], NULL, CHILD, 15);
        COMMON(v);
        v[3] = (void *)child_get_device;
        v[4] = (void *)d_get_private;
        v[5] = (void *)d_set_private;
        if (k == K_BUFFER || k == K_TEX2D) { v[7] = (void *)r_get_type; v[10] = k == K_BUFFER ? (void *)b_get_desc : (void *)t_get_desc; }
        if (k == K_SRV || k == K_RTV || k == K_DSV) v[7] = (void *)v_get_resource;
        g_vt[k] = v;
    }
}

static int init_vulkan(void) {
    HMODULE lib = LoadLibraryA("vulkan-1.dll");
    PFN_vkGetInstanceProcAddr gipa;
    PFN_vkCreateInstance create;
    VkApplicationInfo app = {VK_STRUCTURE_TYPE_APPLICATION_INFO};
    VkInstanceCreateInfo ici = {VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    static const char *const IEXT[] = {"VK_KHR_surface", "VK_KHR_win32_surface"};
    static const char *const DEXT[] = {"VK_KHR_swapchain"};
    VkPhysicalDevice devs[8];
    uint32_t n = 8, i;
    VkDeviceQueueCreateInfo qi = {VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    float prio = 1.0f;
    VkDeviceCreateInfo dci = {VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    VkPhysicalDeviceFeatures2 f2 = {VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2};
    VkPhysicalDeviceVulkan13Features f13 = {VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES};
    VkPhysicalDeviceProperties prop;
    VkQueueFamilyProperties qf[16];
    VkFormatProperties fp;
    if (!lib) { logf_("vulkan-1.dll not found"); return 0; }
    gipa = (PFN_vkGetInstanceProcAddr)GetProcAddress(lib, "vkGetInstanceProcAddr");
    create = (PFN_vkCreateInstance)gipa(NULL, "vkCreateInstance");
    app.apiVersion = VK_API_VERSION_1_3;
    app.pApplicationName = "Opem Amalur";
    ici.pApplicationInfo = &app;
    ici.enabledExtensionCount = 2;
    ici.ppEnabledExtensionNames = IEXT;
    if (create(&ici, NULL, &g_instance)) { logf_("vkCreateInstance failed"); return 0; }
#define X(f) p##f = (PFN_##f)gipa(g_instance, #f);
    VK_FUNCS(X)
#undef X
    pvkEnumeratePhysicalDevices(g_instance, &n, devs);
    g_phys = devs[0];
    for (i = 0; i < n; i++) {
        pvkGetPhysicalDeviceProperties(devs[i], &prop);
        if (prop.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) { g_phys = devs[i]; break; }
    }
    pvkGetPhysicalDeviceProperties(g_phys, &prop);
    logf_("GPU %s api %u.%u", prop.deviceName, VK_API_VERSION_MAJOR(prop.apiVersion), VK_API_VERSION_MINOR(prop.apiVersion));
    g_ubo_align = prop.limits.minUniformBufferOffsetAlignment;
    pvkGetPhysicalDeviceMemoryProperties(g_phys, &g_mem);
    n = 16;
    pvkGetPhysicalDeviceQueueFamilyProperties(g_phys, &n, qf);
    for (i = 0; i < n; i++)
        if (qf[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) { g_qfam = i; break; }
    pvkGetPhysicalDeviceFormatProperties(g_phys, VK_FORMAT_D24_UNORM_S8_UINT, &fp);
    if (!(fp.optimalTilingFeatures & VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT)) g_d24s8 = VK_FORMAT_D32_SFLOAT_S8_UINT;
    qi.queueFamilyIndex = g_qfam;
    qi.queueCount = 1;
    qi.pQueuePriorities = &prio;
    f13.dynamicRendering = VK_TRUE;
    f13.synchronization2 = VK_FALSE;
    f2.pNext = &f13;
    f2.features.textureCompressionBC = VK_TRUE;
    f2.features.samplerAnisotropy = VK_TRUE;
    f2.features.depthClamp = VK_TRUE;
    f2.features.depthBiasClamp = VK_TRUE;
    f2.features.independentBlend = VK_TRUE;
    f2.features.dualSrcBlend = VK_TRUE;
    f2.features.fillModeNonSolid = VK_TRUE;
    f2.features.robustBufferAccess = VK_TRUE;
    dci.pNext = &f2;
    dci.queueCreateInfoCount = 1;
    dci.pQueueCreateInfos = &qi;
    dci.enabledExtensionCount = 1;
    dci.ppEnabledExtensionNames = DEXT;
    {
        VkResult r = pvkCreateDevice(g_phys, &dci, NULL, &g_dev);
        if (r) { logf_("vkCreateDevice failed %d", r); return 0; }
    }
#define X(f) p##f = (PFN_##f)pvkGetDeviceProcAddr(g_dev, #f);
    VKD_FUNCS(X)
#undef X
    pvkGetDeviceQueue(g_dev, g_qfam, 0, &g_queue);
    {
        VkPipelineCacheCreateInfo pc = {VK_STRUCTURE_TYPE_PIPELINE_CACHE_CREATE_INFO};
        VkCommandPoolCreateInfo cp = {VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
        VkCommandBufferAllocateInfo ca = {VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
        VkFenceCreateInfo fc = {VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
        VkSemaphoreCreateInfo sc = {VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
        pvkCreatePipelineCache(g_dev, &pc, NULL, &g_pcache);
        cp.queueFamilyIndex = g_qfam;
        ca.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
        ca.commandBufferCount = 1;
        for (i = 0; i < FRAMES; i++) {
            pvkCreateCommandPool(g_dev, &cp, NULL, &g_f[i].pool);
            ca.commandPool = g_f[i].pool;
            pvkAllocateCommandBuffers(g_dev, &ca, &g_f[i].cmd);
            pvkCreateFence(g_dev, &fc, NULL, &g_f[i].fence);
            pvkCreateSemaphore(g_dev, &sc, NULL, &g_f[i].acquired);
            pvkCreateSemaphore(g_dev, &sc, NULL, &g_f[i].rendered);
            {
                VkQueryPoolCreateInfo qc = {VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO};
                qc.queryType = VK_QUERY_TYPE_OCCLUSION;
                qc.queryCount = QUERY_MAX;
                if (pvkCreateQueryPool(g_dev, &qc, NULL, &g_f[i].qpool)) { logf_("query pool failed"); return 0; }
                g_f[i].qlist = calloc(QUERY_MAX, sizeof(oa_pred *));
                g_f[i].qreset = QUERY_MAX;
            }
            if (!make_buffer(&g_f[i].rings[0], RING_SIZE, VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT)) { logf_("ring failed"); return 0; }
            g_f[i].nrings = 1;
        }
        pvkCreateCommandPool(g_dev, &cp, NULL, &g_upload_pool);
        ca.commandPool = g_upload_pool;
        pvkAllocateCommandBuffers(g_dev, &ca, &g_upload_cmd);
        pvkCreateFence(g_dev, &fc, NULL, &g_upload_fence);
    }
    if (!make_buffer(&g_zero_ubo, 65536, VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT | VK_BUFFER_USAGE_VERTEX_BUFFER_BIT)) return 0;
    memset(g_zero_ubo.ptr, 0, 65536);
    g_pipes = calloc(g_pipes_cap, sizeof(pipe_entry));
    desc_new_pool();
    return 1;
}

static void init_dummies(void) {
    uint32_t d2[11] = {1, 1, 1, 1, 28, 1, 0, 0, 8, 0, 0}, dc[11] = {1, 1, 1, 6, 28, 1, 0, 0, 8, 0, 4}, d3[9] = {1, 1, 1, 1, 28, 0, 8, 0, 0};
    uint32_t smp[13] = {0x15, 3, 3, 3, 0, 1, 1, 0, 0, 0, 0, 0, 0x7f7fffff};
    create_texture(d2, NULL, &g_dummy2d, 0);
    create_texture(dc, NULL, &g_dummycube, 0);
    create_texture(d3, NULL, &g_dummy3d, 1);
    d_create_srv(NULL, g_dummy2d, NULL, &g_null2d);
    d_create_srv(NULL, g_dummycube, NULL, &g_nullcube);
    d_create_srv(NULL, g_dummy3d, NULL, &g_null3d);
    d_create_sampler(NULL, smp, &g_null_sampler);
}

/* If Present stops, log where every thread is: instruction pointer plus code addresses found on its stack. */
static void describe_addr(uint32_t a, char *out, size_t n) {
    HMODULE m = NULL;
    char name[MAX_PATH] = "?", *b;
    if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (const char *)(uintptr_t)a, &m) && m) {
        GetModuleFileNameA(m, name, MAX_PATH);
        b = strrchr(name, '\\');
        if (m == GetModuleHandleA(NULL)) snprintf(out, n, "koa:%08x", (unsigned)(a - (uint32_t)(uintptr_t)m + 0x400000u));
        else snprintf(out, n, "%s+%x", b ? b + 1 : name, (unsigned)(a - (uint32_t)(uintptr_t)m));
    } else out[0] = 0;
}

static void stack_line(const char *tag, uint32_t ip, uint32_t esp) {
    char line[900], d[96];
    size_t used;
    int i, shown = 0;
    MEMORY_BASIC_INFORMATION mi;
    describe_addr(ip, d, sizeof(d));
    used = (size_t)snprintf(line, sizeof(line), "%s ip %s (%08x):", tag, d, ip);
    if (VirtualQuery((void *)(uintptr_t)esp, &mi, sizeof(mi)) && mi.State == MEM_COMMIT) {
        uint32_t *sp = (uint32_t *)(uintptr_t)esp;
        size_t room = ((uint8_t *)mi.BaseAddress + mi.RegionSize - (uint8_t *)sp) / 4;
        for (i = 0; i < 500 && (size_t)i < room && shown < 16; i++) {
            MEMORY_BASIC_INFORMATION ci;
            if (sp[i] >= 0x10000 && VirtualQuery((void *)(uintptr_t)sp[i], &ci, sizeof(ci)) && (ci.Protect & (PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE))) {
                describe_addr(sp[i], d, sizeof(d));
                if (d[0] && used < sizeof(line) - 100) { used += (size_t)snprintf(line + used, sizeof(line) - used, " %s", d); shown++; }
            }
        }
    }
    logf_("%s", line);
}

static LONG WINAPI on_exception(EXCEPTION_POINTERS *e) {
    static volatile LONG count;
    DWORD code = e->ExceptionRecord->ExceptionCode;
    if ((code == EXCEPTION_ACCESS_VIOLATION || code == EXCEPTION_ILLEGAL_INSTRUCTION || code == EXCEPTION_INT_DIVIDE_BY_ZERO || code == EXCEPTION_STACK_OVERFLOW || code == EXCEPTION_PRIV_INSTRUCTION) && InterlockedIncrement(&count) <= 6) {
        CONTEXT *c = e->ContextRecord;
        logf_("EXCEPTION %08lx op %lu addr %08lx thread %lu frame %llu eax %08lx ecx %08lx edx %08lx ebx %08lx esi %08lx edi %08lx", code, (unsigned long)e->ExceptionRecord->ExceptionInformation[0], (unsigned long)e->ExceptionRecord->ExceptionInformation[1], GetCurrentThreadId(), (unsigned long long)g_frames_shown, c->Eax, c->Ecx, c->Edx, c->Ebx, c->Esi, c->Edi);
        stack_line("crash", c->Eip, c->Esp);
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

static DWORD WINAPI watchdog(void *unused) {
    uint64_t last = 0;
    int stalled = 0, reports = 0;
    (void)unused;
    for (;;) {
        Sleep(1000);
        if (g_frames_shown != last) { last = g_frames_shown; stalled = 0; continue; }
        if (++stalled != 10 || reports >= 3) continue;
        reports++;
        logf_("STALL: no Present for 10 s after frame %llu", (unsigned long long)last);
        {
            HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
            THREADENTRY32 te;
            te.dwSize = sizeof(te);
            if (Thread32First(snap, &te)) do {
                if (te.th32OwnerProcessID == GetCurrentProcessId() && te.th32ThreadID != GetCurrentThreadId()) {
                    HANDLE t = OpenThread(THREAD_ALL_ACCESS, FALSE, te.th32ThreadID);
                    CONTEXT cx;
                    if (t && SuspendThread(t) != (DWORD)-1) {
                        char line[900], d[96];
                        size_t used = 0;
                        int i, shown = 0;
                        cx.ContextFlags = CONTEXT_CONTROL;
                        if (GetThreadContext(t, &cx)) {
                            MEMORY_BASIC_INFORMATION mi;
                            describe_addr(cx.Eip, d, sizeof(d));
                            used = (size_t)snprintf(line, sizeof(line), "thread %lu ip %s:", te.th32ThreadID, d);
                            if (VirtualQuery((void *)(uintptr_t)cx.Esp, &mi, sizeof(mi)) && mi.State == MEM_COMMIT) {
                                uint32_t *sp = (uint32_t *)(uintptr_t)cx.Esp;
                                size_t room = ((uint8_t *)mi.BaseAddress + mi.RegionSize - (uint8_t *)sp) / 4;
                                for (i = 0; i < 400 && (size_t)i < room && shown < 12; i++) {
                                    if (sp[i] >= 0x10000) {
                                        MEMORY_BASIC_INFORMATION ci;
                                        if (VirtualQuery((void *)(uintptr_t)sp[i], &ci, sizeof(ci)) && (ci.Protect & (PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE))) {
                                            describe_addr(sp[i], d, sizeof(d));
                                            if (d[0] && used < sizeof(line) - 100) { used += (size_t)snprintf(line + used, sizeof(line) - used, " %s", d); shown++; }
                                        }
                                    }
                                }
                            }
                            logf_("%s", line);
                        }
                        ResumeThread(t);
                    }
                    if (t) CloseHandle(t);
                }
            } while (Thread32Next(snap, &te));
            CloseHandle(snap);
        }
    }
    return 0;
}

__declspec(dllexport) HRESULT WINAPI D3D11CreateDevice(void *adapter, int type, HMODULE sw, UINT flags, const void *levels, UINT n, UINT sdk, obj **device, UINT *level, oa_context **ctx) {
    static int ready;
    (void)adapter; (void)type; (void)sw; (void)levels; (void)n; (void)sdk;
    logf_("D3D11CreateDevice flags=%x", flags);
    logf_("DIAG texture-lod0-20261104: live switch force-lod0; default OFF");
    if (!ready) {
        init_vtables();
        if (!init_vulkan()) return E_FAIL_;
        g_device_obj.vtbl = g_vt[K_DEVICE];
        g_device_obj.ref = 1;
        g_device_obj.kind = K_DEVICE;
        g_dxgi_device = new_obj(sizeof(obj), K_DXGI_DEVICE);
        g_adapter = new_obj(sizeof(obj), K_ADAPTER);
        g_factory = new_obj(sizeof(obj), K_FACTORY);
        g_ctx = (oa_context *)new_obj(sizeof(oa_context), K_CONTEXT);
        init_dummies();
        frame_begin();
        ready = 1;
        AddVectoredExceptionHandler(1, on_exception);
        CreateThread(NULL, 0, watchdog, NULL, 0, NULL);
    }
    if (device) { o_addref(&g_device_obj); *device = &g_device_obj; }
    if (ctx) { o_addref(&g_ctx->o); *ctx = g_ctx; }
    if (level) *level = 0xb000;
    return S_OK_;
}

__declspec(dllexport) HRESULT WINAPI D3D11CreateDeviceAndSwapChain(void *a, int t, HMODULE s, UINT f, const void *l, UINT n, UINT sdk, const void *desc, void **chain, obj **dev, UINT *lvl, oa_context **ctx) {
    (void)a; (void)t; (void)s; (void)f; (void)l; (void)n; (void)sdk; (void)desc; (void)chain; (void)dev; (void)lvl; (void)ctx;
    logf_("NOT IMPLEMENTED D3D11CreateDeviceAndSwapChain");
    return E_NOTIMPL_;
}

BOOL WINAPI DllMain(HINSTANCE self, DWORD why, LPVOID r) {
    (void)r;
    if (why == DLL_PROCESS_ATTACH) {
        char mod[MAX_PATH], *slash;
        DisableThreadLibraryCalls(self);
        InitializeCriticalSection(&g_lock);
        GetModuleFileNameA(self, mod, MAX_PATH);
        if ((slash = strrchr(mod, '\\'))) *slash = 0;
        snprintf(g_game_log, sizeof(g_game_log), "%s\\Kingdoms of Amalur_ Re-Reckoning.log", mod);
        lstrcatA(mod, "\\oa_vk.log");
        /* Under DroidDeck the tablet's shared storage is reachable, so the log can be read with adb. */
        g_log = fopen("Z:\\storage\\emulated\\0\\Download\\oa\\oa_vk.log", "w");
        if (!g_log) g_log = fopen(mod, "w");
    }
    return TRUE;
}
