/* oa_d3d11.c: d3d11.dll proxy for koa.exe (32-bit). Forwards to the real d3d11 and records how the engine uses it.
   Every device and context method goes through a generated thunk that counts the call and can log it to a frame trace.
   Output goes to oa_rec next to the exe: stats.txt, resources.txt, shaders/, trace_<frame>.txt. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <intrin.h>

#define COM __stdcall
typedef HRESULT(WINAPI *create_device_fn)(void *, int, HMODULE, UINT, const void *, UINT, UINT, void **, UINT *, void **);
typedef HRESULT(WINAPI *create_chain_fn)(void *, int, HMODULE, UINT, const void *, UINT, UINT, const void *, void **, void **, UINT *, void **);

static const char *const DEVICE_NAMES[43] = {"QueryInterface", "AddRef", "Release", "CreateBuffer", "CreateTexture1D", "CreateTexture2D", "CreateTexture3D", "CreateShaderResourceView", "CreateUnorderedAccessView", "CreateRenderTargetView", "CreateDepthStencilView", "CreateInputLayout", "CreateVertexShader", "CreateGeometryShader", "CreateGeometryShaderWithStreamOutput", "CreatePixelShader", "CreateHullShader", "CreateDomainShader", "CreateComputeShader", "CreateClassLinkage", "CreateBlendState", "CreateDepthStencilState", "CreateRasterizerState", "CreateSamplerState", "CreateQuery", "CreatePredicate", "CreateCounter", "CreateDeferredContext", "OpenSharedResource", "CheckFormatSupport", "CheckMultisampleQualityLevels", "CheckCounterInfo", "CheckCounter", "CheckFeatureSupport", "GetPrivateData", "SetPrivateData", "SetPrivateDataInterface", "GetFeatureLevel", "GetCreationFlags", "GetDeviceRemovedReason", "GetImmediateContext", "SetExceptionMode", "GetExceptionMode"};
static const char *const CONTEXT_NAMES[115] = {"QueryInterface", "AddRef", "Release", "GetDevice", "GetPrivateData", "SetPrivateData", "SetPrivateDataInterface", "VSSetConstantBuffers", "PSSetShaderResources", "PSSetShader", "PSSetSamplers", "VSSetShader", "DrawIndexed", "Draw", "Map", "Unmap", "PSSetConstantBuffers", "IASetInputLayout", "IASetVertexBuffers", "IASetIndexBuffer", "DrawIndexedInstanced", "DrawInstanced", "GSSetConstantBuffers", "GSSetShader", "IASetPrimitiveTopology", "VSSetShaderResources", "VSSetSamplers", "Begin", "End", "GetData", "SetPredication", "GSSetShaderResources", "GSSetSamplers", "OMSetRenderTargets", "OMSetRenderTargetsAndUnorderedAccessViews", "OMSetBlendState", "OMSetDepthStencilState", "SOSetTargets", "DrawAuto", "DrawIndexedInstancedIndirect", "DrawInstancedIndirect", "Dispatch", "DispatchIndirect", "RSSetState", "RSSetViewports", "RSSetScissorRects", "CopySubresourceRegion", "CopyResource", "UpdateSubresource", "CopyStructureCount", "ClearRenderTargetView", "ClearUnorderedAccessViewUint", "ClearUnorderedAccessViewFloat", "ClearDepthStencilView", "GenerateMips", "SetResourceMinLOD", "GetResourceMinLOD", "ResolveSubresource", "ExecuteCommandList", "HSSetShaderResources", "HSSetShader", "HSSetSamplers", "HSSetConstantBuffers", "DSSetShaderResources", "DSSetShader", "DSSetSamplers", "DSSetConstantBuffers", "CSSetShaderResources", "CSSetUnorderedAccessViews", "CSSetShader", "CSSetSamplers", "CSSetConstantBuffers", "VSGetConstantBuffers", "PSGetShaderResources", "PSGetShader", "PSGetSamplers", "VSGetShader", "PSGetConstantBuffers", "IAGetInputLayout", "IAGetVertexBuffers", "IAGetIndexBuffer", "GSGetConstantBuffers", "GSGetShader", "IAGetPrimitiveTopology", "VSGetShaderResources", "VSGetSamplers", "GetPredication", "GSGetShaderResources", "GSGetSamplers", "OMGetRenderTargets", "OMGetRenderTargetsAndUnorderedAccessViews", "OMGetBlendState", "OMGetDepthStencilState", "SOGetTargets", "RSGetState", "RSGetViewports", "RSGetScissorRects", "HSGetShaderResources", "HSGetShader", "HSGetSamplers", "HSGetConstantBuffers", "DSGetShaderResources", "DSGetShader", "DSGetSamplers", "DSGetConstantBuffers", "CSGetShaderResources", "CSGetUnorderedAccessViews", "CSGetShader", "CSGetSamplers", "CSGetConstantBuffers", "ClearState", "Flush", "GetType", "GetContextFlags", "FinishCommandList"};

#define N_DEVICE 43
#define N_CONTEXT 115
#define N_ALL (N_DEVICE + N_CONTEXT)
#define THUNK_SIZE 28
#define TRACE_MAX (1u << 20)
#define TRACE_EVERY 600

static volatile LONG g_count[N_ALL], g_frame_count[N_ALL];
static void *g_orig[N_ALL];
static uint8_t *g_thunks;
static volatile LONG g_tracing = 1, g_trace_len, g_frame;
static uint16_t *g_trace, *g_trace_prev;
static LONG g_trace_prev_len;
static FILE *g_frames;
static char g_dir[MAX_PATH];
static FILE *g_res;
static CRITICAL_SECTION g_lock;
static int g_device_done, g_context_done, g_chain_done, g_factory_done;
static HRESULT(COM *g_present)(void *, UINT, UINT);
static HRESULT(COM *g_create_chain)(void *, void *, void *, void **);

#define MAX_CALLERS 96
static volatile LONG g_caller[N_ALL][MAX_CALLERS], g_caller_n[N_ALL][MAX_CALLERS], g_caller_over[N_ALL];

void oa_engine_install(void (*log)(const char *, ...));
void oa_engine_report(const char *path);

static void __fastcall on_call(int id, uintptr_t ret) {
    int i;
    for (i = 0; i < MAX_CALLERS; i++) {
        LONG c = g_caller[id][i];
        if (c == (LONG)ret || (!c && (InterlockedCompareExchange(&g_caller[id][i], (LONG)ret, 0) == 0 || g_caller[id][i] == (LONG)ret))) {
            InterlockedIncrement(&g_caller_n[id][i]);
            break;
        }
    }
    if (i == MAX_CALLERS) InterlockedIncrement(&g_caller_over[id]);
    if (g_tracing) {
        LONG i = InterlockedIncrement(&g_trace_len) - 1;
        if (i >= 0 && (ULONG)i < TRACE_MAX) g_trace[i] = (uint16_t)id;
    }
}

/* lock inc [count]; mov edx,[esp]; mov ecx,id; call on_call; jmp [orig]. COM methods here keep arguments on the stack, so ecx and edx are free. */
static void *make_thunk(int id) {
    uint8_t *t = g_thunks + id * THUNK_SIZE;
    t[0] = 0xF0; t[1] = 0xFF; t[2] = 0x05;
    *(void **)(t + 3) = (void *)&g_frame_count[id];
    t[7] = 0x8B; t[8] = 0x14; t[9] = 0x24;
    t[10] = 0xB9;
    *(int *)(t + 11) = id;
    t[15] = 0xE8;
    *(int32_t *)(t + 16) = (int32_t)((uint8_t *)on_call - (t + 20));
    t[20] = 0xFF; t[21] = 0x25;
    *(void **)(t + 22) = (void *)&g_orig[id];
    return t;
}

static void patch(void **slot, void *value) {
    DWORD old;
    VirtualProtect(slot, sizeof(void *), PAGE_READWRITE, &old);
    *slot = value;
    VirtualProtect(slot, sizeof(void *), old, &old);
}

static void path_in(char *out, size_t n, const char *name) { snprintf(out, n, "%s\\%s", g_dir, name); }

static uint32_t fnv(const void *p, size_t n) {
    const uint8_t *b = p;
    uint32_t h = 2166136261u;
    while (n--) h = (h ^ *b++) * 16777619u;
    return h;
}

static void res_log(const char *fmt, ...) {
    va_list a;
    EnterCriticalSection(&g_lock);
    if (g_res) {
        fprintf(g_res, "%ld ", g_frame);
        va_start(a, fmt);
        vfprintf(g_res, fmt, a);
        va_end(a);
        fputc('\n', g_res);
    }
    LeaveCriticalSection(&g_lock);
}

static void dump_shader(const char *kind, const void *code, SIZE_T size) {
    char name[64], full[MAX_PATH];
    uint32_t h = fnv(code, size);
    FILE *f;
    snprintf(name, sizeof(name), "shaders\\%s_%08x.dxbc", kind, h);
    path_in(full, sizeof(full), name);
    if (GetFileAttributesA(full) == INVALID_FILE_ATTRIBUTES && (f = fopen(full, "wb"))) {
        fwrite(code, 1, size, f);
        fclose(f);
    }
    res_log("shader %s %08x %lu", kind, h, (unsigned long)size);
}

#define ORIG(i, type) ((type)g_orig[i])
#define THUNK_THEN(i) InterlockedIncrement(&g_frame_count[i]); on_call(i, (uintptr_t)_ReturnAddress())

static HRESULT COM h_buffer(void *d, const uint32_t *desc, const void *init, void **out) {
    THUNK_THEN(3);
    res_log("buffer size=%u usage=%u bind=%x cpu=%x misc=%x stride=%u init=%d", desc[0], desc[1], desc[2], desc[3], desc[4], desc[5], init != NULL);
    return ORIG(3, HRESULT(COM *)(void *, const void *, const void *, void **))(d, desc, init, out);
}
static HRESULT COM h_tex2d(void *d, const uint32_t *t, const void *init, void **out) {
    THUNK_THEN(5);
    res_log("tex2d %ux%u mips=%u array=%u fmt=%u samples=%u usage=%u bind=%x cpu=%x misc=%x init=%d", t[0], t[1], t[2], t[3], t[4], t[5], t[7], t[8], t[9], t[10], init != NULL);
    return ORIG(5, HRESULT(COM *)(void *, const void *, const void *, void **))(d, t, init, out);
}
static HRESULT COM h_tex3d(void *d, const uint32_t *t, const void *init, void **out) {
    THUNK_THEN(6);
    res_log("tex3d %ux%ux%u mips=%u fmt=%u usage=%u bind=%x", t[0], t[1], t[2], t[3], t[4], t[5], t[6]);
    return ORIG(6, HRESULT(COM *)(void *, const void *, const void *, void **))(d, t, init, out);
}
#define SHADER_HOOK(fn, idx, kind)                                                                   \
    static HRESULT COM fn(void *d, const void *code, SIZE_T size, void *link, void **out) {           \
        THUNK_THEN(idx);                                                                              \
        dump_shader(kind, code, size);                                                                \
        return ORIG(idx, HRESULT(COM *)(void *, const void *, SIZE_T, void *, void **))(d, code, size, link, out); \
    }
SHADER_HOOK(h_vs, 12, "vs")
SHADER_HOOK(h_gs, 13, "gs")
SHADER_HOOK(h_ps, 15, "ps")
SHADER_HOOK(h_hs, 16, "hs")
SHADER_HOOK(h_ds, 17, "ds")
SHADER_HOOK(h_cs, 18, "cs")

static HRESULT COM h_layout(void *d, const uint32_t *e, UINT n, const void *code, SIZE_T size, void **out) {
    UINT i;
    THUNK_THEN(11);
    /* D3D11_INPUT_ELEMENT_DESC is 7 dwords on x86: name, index, format, slot, offset, class, step. */
    EnterCriticalSection(&g_lock);
    if (g_res) {
        fprintf(g_res, "%ld layout", g_frame);
        for (i = 0; i < n; i++) {
            const uint32_t *x = e + i * 7;
            fprintf(g_res, " %s%u:fmt%u:s%u:o%u:c%u", (const char *)(uintptr_t)x[0], x[1], x[2], x[3], x[4], x[5]);
        }
        fputc('\n', g_res);
    }
    LeaveCriticalSection(&g_lock);
    return ORIG(11, HRESULT(COM *)(void *, const void *, UINT, const void *, SIZE_T, void **))(d, e, n, code, size, out);
}
static HRESULT COM h_query(void *d, const uint32_t *q, void **out) {
    THUNK_THEN(24);
    res_log("query type=%u misc=%u", q[0], q[1]);
    return ORIG(24, HRESULT(COM *)(void *, const void *, void **))(d, q, out);
}
static HRESULT COM h_predicate(void *d, const uint32_t *q, void **out) {
    THUNK_THEN(25);
    res_log("predicate type=%u misc=%u", q[0], q[1]);
    return ORIG(25, HRESULT(COM *)(void *, const void *, void **))(d, q, out);
}

static void hook_context(void *ctx) {
    void **vt = *(void ***)ctx;
    int i;
    EnterCriticalSection(&g_lock);
    if (!g_context_done) {
        g_context_done = 1;
        for (i = 0; i < N_CONTEXT; i++) {
            g_orig[N_DEVICE + i] = vt[i];
            patch(&vt[i], make_thunk(N_DEVICE + i));
        }
    }
    LeaveCriticalSection(&g_lock);
}

static void write_stats(void) {
    char full[MAX_PATH];
    FILE *f;
    int i;
    path_in(full, sizeof(full), "stats.txt");
    if (!(f = fopen(full, "w"))) return;
    fprintf(f, "frames %ld\n", g_frame);
    for (i = 0; i < N_ALL; i++)
        if (g_count[i]) fprintf(f, "%s %s %ld\n", i < N_DEVICE ? "device" : "context", i < N_DEVICE ? DEVICE_NAMES[i] : CONTEXT_NAMES[i - N_DEVICE], g_count[i]);
    fclose(f);
    path_in(full, sizeof(full), "engine.txt");
    oa_engine_report(full);
    path_in(full, sizeof(full), "callers.txt");
    if (!(f = fopen(full, "w"))) return;
    {
        uintptr_t self = (uintptr_t)GetModuleHandleA(NULL);
        int j;
        fprintf(f, "base %08lx\n", (unsigned long)self);
        for (i = 0; i < N_ALL; i++) {
            const char *n = i < N_DEVICE ? DEVICE_NAMES[i] : CONTEXT_NAMES[i - N_DEVICE];
            for (j = 0; j < MAX_CALLERS && g_caller[i][j]; j++) fprintf(f, "%s %s %08lx %ld\n", i < N_DEVICE ? "device" : "context", n, (unsigned long)((uintptr_t)g_caller[i][j] - self + 0x400000), g_caller_n[i][j]);
            if (g_caller_over[i]) fprintf(f, "%s %s overflow 0 %ld\n", i < N_DEVICE ? "device" : "context", n, g_caller_over[i]);
        }
    }
    fclose(f);
}

static void write_trace(const char *prefix, long frame, const uint16_t *buf, LONG n) {
    char name[64], full[MAX_PATH];
    FILE *f;
    LONG i;
    if ((ULONG)n > TRACE_MAX) n = TRACE_MAX;
    snprintf(name, sizeof(name), "%s_%ld.txt", prefix, frame);
    path_in(full, sizeof(full), name);
    if (!(f = fopen(full, "w"))) return;
    for (i = 0; i < n; i++) fprintf(f, "%s\n", buf[i] < N_DEVICE ? DEVICE_NAMES[buf[i]] : CONTEXT_NAMES[buf[i] - N_DEVICE]);
    fclose(f);
}

/* Context method numbers logged for every frame in frames.csv. */
static const int FRAME_COLUMNS[] = {12, 13, 14, 18, 9, 35, 36, 8, 30, 27, 33, 17, 11};
#define N_COLUMNS (sizeof(FRAME_COLUMNS) / sizeof(FRAME_COLUMNS[0]))
#define MAX_ODD_DUMPS 16

static HRESULT COM h_present(void *chain, UINT sync, UINT flags) {
    HRESULT hr = g_present(chain, sync, flags);
    long frame = InterlockedIncrement(&g_frame);
    static LONG last_indexed;
    static int odd_dumps;
    LONG values[N_ALL], calls = g_trace_len, indexed;
    uint16_t *swap;
    int i;
    for (i = 0; i < N_ALL; i++) {
        values[i] = InterlockedExchange(&g_frame_count[i], 0);
        g_count[i] += values[i];
    }
    indexed = values[N_DEVICE + 12];
    if (g_frames) {
        fprintf(g_frames, "%ld,%ld", frame, calls);
        for (i = 0; i < (int)N_COLUMNS; i++) fprintf(g_frames, ",%ld", values[N_DEVICE + FRAME_COLUMNS[i]]);
        fputc('\n', g_frames);
    }
    /* A steady frame whose draw count changed: keep its calls and the frame before it. */
    if (last_indexed > 1000 && indexed > 1000 && indexed != last_indexed && odd_dumps < MAX_ODD_DUMPS) {
        odd_dumps++;
        write_trace("odd", frame, g_trace, calls);
        write_trace("prev", frame, g_trace_prev, g_trace_prev_len);
    }
    last_indexed = indexed;
    if (frame % TRACE_EVERY == 0) write_trace("trace", frame, g_trace, calls);
    swap = g_trace;
    g_trace = g_trace_prev;
    g_trace_prev = swap;
    g_trace_prev_len = calls;
    g_trace_len = 0;
    if (frame % TRACE_EVERY == 0) {
        write_stats();
        EnterCriticalSection(&g_lock);
        if (g_res) fflush(g_res);
        if (g_frames) fflush(g_frames);
        LeaveCriticalSection(&g_lock);
    }
    return hr;
}

static void hook_chain(void *chain) {
    void **vt = *(void ***)chain;
    EnterCriticalSection(&g_lock);
    if (!g_chain_done) {
        g_chain_done = 1;
        g_present = vt[8];
        patch(&vt[8], (void *)h_present);
        res_log("present hooked");
    }
    LeaveCriticalSection(&g_lock);
}

static HRESULT COM h_create_chain(void *factory, void *device, void *desc, void **out) {
    HRESULT hr = g_create_chain(factory, device, desc, out);
    if (SUCCEEDED(hr) && out && *out) {
        const uint32_t *x = desc;
        res_log("swapchain %ux%u fmt=%u samples=%u usage=%x buffers=%u windowed=%u effect=%u flags=%x", x[0], x[1], x[4], x[7], x[9], x[10], x[12], x[13], x[14]);
        hook_chain(*out);
    }
    return hr;
}

static void hook_factory(void *device) {
    static const GUID IID_IDXGIDevice_ = {0x54ec77fa, 0x1377, 0x44e6, {0x8c, 0x32, 0x88, 0xfd, 0x5f, 0x44, 0xc8, 0x4c}};
    static const GUID IID_IDXGIFactory_ = {0x7b7166ec, 0x21c7, 0x44ae, {0xb2, 0x1a, 0xc9, 0xae, 0x32, 0x1a, 0xe3, 0x69}};
    typedef HRESULT(COM * qi_fn)(void *, const GUID *, void **);
    typedef ULONG(COM * rel_fn)(void *);
    void *dxgi = NULL, *adapter = NULL, *factory = NULL;
    if (g_factory_done) return;
    if (FAILED(((qi_fn)(*(void ***)device)[0])(device, &IID_IDXGIDevice_, &dxgi)) || !dxgi) return;
    if (SUCCEEDED(((HRESULT(COM *)(void *, void **))(*(void ***)dxgi)[7])(dxgi, &adapter)) && adapter) {
        if (SUCCEEDED(((HRESULT(COM *)(void *, const GUID *, void **))(*(void ***)adapter)[6])(adapter, &IID_IDXGIFactory_, &factory)) && factory) {
            void **vt = *(void ***)factory;
            g_factory_done = 1;
            g_create_chain = vt[10];
            patch(&vt[10], (void *)h_create_chain);
            res_log("factory hooked");
            ((rel_fn)vt[2])(factory);
        }
        ((rel_fn)(*(void ***)adapter)[2])(adapter);
    }
    ((rel_fn)(*(void ***)dxgi)[2])(dxgi);
}

static void hook_device(void *device) {
    void **vt = *(void ***)device;
    int i;
    EnterCriticalSection(&g_lock);
    if (!g_device_done) {
        g_device_done = 1;
        for (i = 0; i < N_DEVICE; i++) {
            void *hook = make_thunk(i);
            g_orig[i] = vt[i];
            switch (i) {
            case 3: hook = (void *)h_buffer; break;
            case 5: hook = (void *)h_tex2d; break;
            case 6: hook = (void *)h_tex3d; break;
            case 11: hook = (void *)h_layout; break;
            case 12: hook = (void *)h_vs; break;
            case 13: hook = (void *)h_gs; break;
            case 15: hook = (void *)h_ps; break;
            case 16: hook = (void *)h_hs; break;
            case 17: hook = (void *)h_ds; break;
            case 18: hook = (void *)h_cs; break;
            case 24: hook = (void *)h_query; break;
            case 25: hook = (void *)h_predicate; break;
            }
            patch(&vt[i], hook);
        }
    }
    LeaveCriticalSection(&g_lock);
    hook_factory(device);
}

static HMODULE real_module(void) {
    static HMODULE m;
    if (!m) {
        char path[MAX_PATH] = "";
        if (!GetEnvironmentVariableA("OA_REAL_D3D11", path, MAX_PATH) || !path[0]) {
            GetSystemDirectoryA(path, MAX_PATH);
            lstrcatA(path, "\\d3d11.dll");
        }
        m = LoadLibraryA(path);
        res_log("real d3d11 %s module=%p", path, (void *)m);
    }
    return m;
}

__declspec(dllexport) HRESULT WINAPI D3D11CreateDevice(void *adapter, int type, HMODULE sw, UINT flags, const void *levels, UINT n, UINT sdk, void **device, UINT *level, void **ctx) {
    create_device_fn real = (create_device_fn)GetProcAddress(real_module(), "D3D11CreateDevice");
    void *d = NULL, *c = NULL;
    HRESULT hr;
    UINT got = 0;
    if (!real) return E_FAIL;
    hr = real(adapter, type, sw, flags, levels, n, sdk, &d, &got, &c);
    res_log("D3D11CreateDevice hr=%lx flags=%x level=%x type=%d", (unsigned long)hr, flags, got, type);
    if (SUCCEEDED(hr) && d) {
        oa_engine_install(res_log);
        hook_device(d);
        if (c) hook_context(c);
        if (device) *device = d; else ((ULONG(COM *)(void *))(*(void ***)d)[2])(d);
        if (ctx) *ctx = c; else if (c) ((ULONG(COM *)(void *))(*(void ***)c)[2])(c);
    }
    if (level) *level = got;
    return hr;
}

__declspec(dllexport) HRESULT WINAPI D3D11CreateDeviceAndSwapChain(void *adapter, int type, HMODULE sw, UINT flags, const void *levels, UINT n, UINT sdk, const void *desc, void **chain, void **device, UINT *level, void **ctx) {
    create_chain_fn real = (create_chain_fn)GetProcAddress(real_module(), "D3D11CreateDeviceAndSwapChain");
    if (!real) return E_FAIL;
    return real(adapter, type, sw, flags, levels, n, sdk, desc, chain, device, level, ctx);
}

BOOL WINAPI DllMain(HINSTANCE self, DWORD why, LPVOID r) {
    (void)r;
    if (why == DLL_PROCESS_ATTACH) {
        char mod[MAX_PATH], full[MAX_PATH], *slash;
        DisableThreadLibraryCalls(self);
        InitializeCriticalSection(&g_lock);
        g_thunks = VirtualAlloc(NULL, N_ALL * THUNK_SIZE, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
        g_trace = VirtualAlloc(NULL, TRACE_MAX * sizeof(uint16_t), MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
        g_trace_prev = VirtualAlloc(NULL, TRACE_MAX * sizeof(uint16_t), MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
        GetModuleFileNameA(self, mod, MAX_PATH);
        if ((slash = strrchr(mod, '\\'))) *slash = 0;
        snprintf(g_dir, sizeof(g_dir), "%s\\oa_rec", mod);
        CreateDirectoryA(g_dir, NULL);
        path_in(full, sizeof(full), "shaders");
        CreateDirectoryA(full, NULL);
        path_in(full, sizeof(full), "resources.txt");
        g_res = fopen(full, "w");
        path_in(full, sizeof(full), "frames.csv");
        g_frames = fopen(full, "w");
        if (g_frames) fprintf(g_frames, "frame,calls,DrawIndexed,Draw,Map,IASetVertexBuffers,PSSetShader,OMSetBlendState,OMSetDepthStencilState,PSSetShaderResources,SetPredication,Begin,OMSetRenderTargets,IASetInputLayout,VSSetShader\n");
    } else if (why == DLL_PROCESS_DETACH && !r) {
        write_stats();
        if (g_res) fclose(g_res);
        if (g_frames) fclose(g_frames);
    }
    return TRUE;
}
