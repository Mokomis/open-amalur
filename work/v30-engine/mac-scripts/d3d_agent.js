// Read-only D3D11 observer for koa.exe. Nothing is written to game files.
// Records shader bytecode, constant buffer contents and pass order for armed frames.
'use strict';
const CTX = {VSSetCB:7, PSSetSRV:8, PSSetShader:9, VSSetShader:11, DrawIndexed:12, Draw:13, Map:14, Unmap:15, PSSetCB:16,
  DrawIndexedInstanced:20, DrawInstanced:21, OMSetRT:33, CopyResource:47, UpdateSubresource:48, Resolve:57};
const DEV = {CreateBuffer:3, CreateTex2D:5, CreateTex3D:6, CreateSRV:7, CreateRTV:9, CreateVS:12, CreatePS:15, CreateDeferred:27};
const CB_BIND = 4;

let device = null, context = null, swapHooked = false;
const buffers = new Map(), textures = new Map(), srvs = new Map(), rtvs = new Map(), shaders = new Map();
let frameNo = 0, shotPending = false, armed = 0, capturing = false, frame = null, heavy = [], busy = false;
let dumpPs = new Set(), mapPending = new Map(), currentPs = '', currentVs = '', currentRt = [];

const vfn = (obj, i) => obj.readPointer().add(i * Process.pointerSize).readPointer();
const call = (obj, i, ret, args) => new NativeFunction(vfn(obj, i), ret, ['pointer'].concat(args), 'stdcall');
const release = o => { if (!o.isNull()) call(o, 2, 'uint', [])(o); };
const key = p => p.toString();

function hookDevice(d) {
  if (device) return;
  device = d;
  send({t:'log', m:'device ' + d});
  Interceptor.attach(vfn(d, DEV.CreateBuffer), {
    onEnter(a) { this.desc = a[1]; this.init = a[2]; this.out = a[3]; },
    onLeave(r) {
      if (r.toInt32() < 0 || this.out.isNull() || this.desc.isNull()) return;
      buffers.set(key(this.out.readPointer()), {size:this.desc.readU32(), usage:this.desc.add(4).readU32(), bind:this.desc.add(8).readU32()});
    }});
  const tex = dim => ({
    onEnter(a) { this.desc = a[1]; this.out = a[3]; },
    onLeave(r) {
      if (r.toInt32() < 0 || this.out.isNull()) return;
      const d = this.desc;
      const info = dim === 2
        ? {dim, w:d.readU32(), h:d.add(4).readU32(), mips:d.add(8).readU32(), arr:d.add(12).readU32(), fmt:d.add(16).readU32(), samples:d.add(20).readU32(), bind:d.add(32).readU32()}
        : {dim, w:d.readU32(), h:d.add(4).readU32(), depth:d.add(8).readU32(), mips:d.add(12).readU32(), fmt:d.add(16).readU32(), bind:d.add(24).readU32()};
      textures.set(key(this.out.readPointer()), info);
    }});
  Interceptor.attach(vfn(d, DEV.CreateTex2D), tex(2));
  Interceptor.attach(vfn(d, DEV.CreateTex3D), tex(3));
  const view = table => ({
    onEnter(a) { this.res = a[1]; this.out = a[3]; },
    onLeave(r) { if (r.toInt32() >= 0 && !this.out.isNull()) table.set(key(this.out.readPointer()), key(this.res)); }});
  Interceptor.attach(vfn(d, DEV.CreateSRV), view(srvs));
  Interceptor.attach(vfn(d, DEV.CreateRTV), view(rtvs));
  const shader = kind => ({
    onEnter(a) { this.code = a[1]; this.len = a[2].toUInt32(); this.out = a[4]; },
    onLeave(r) {
      if (r.toInt32() < 0 || this.out.isNull()) return;
      const sum = Array.from(new Uint8Array(this.code.add(4).readByteArray(16))).map(b => b.toString(16).padStart(2, '0')).join('');
      shaders.set(key(this.out.readPointer()), sum);
      send({t:'shader', kind, sum}, this.code.readByteArray(this.len));
    }});
  Interceptor.attach(vfn(d, DEV.CreateVS), shader('vs'));
  Interceptor.attach(vfn(d, DEV.CreatePS), shader('ps'));
  Interceptor.attach(vfn(d, DEV.CreateDeferred), {onLeave() { send({t:'log', m:'CreateDeferredContext called'}); }});
}

function hookSwap(s) {
  if (swapHooked) return;
  swapHooked = true;
  send({t:'log', m:'swapchain ' + s});
  Interceptor.attach(vfn(s, 8), {onEnter(a) { onPresent(a[0]); }});
}

function readTexture(res, label, extra) {
  // Copies through a private staging texture; the game's resource is only read.
  busy = true;
  try {
    const desc = Memory.alloc(44), out = Memory.alloc(4), map = Memory.alloc(12);
    call(res, 10, 'void', ['pointer'])(res, desc);
    const w = desc.readU32(), h = desc.add(4).readU32(), fmt = desc.add(16).readU32(), samples = desc.add(20).readU32();
    desc.add(8).writeU32(1);
    desc.add(20).writeU32(1); desc.add(24).writeU32(0);
    desc.add(28).writeU32(3); desc.add(32).writeU32(0); desc.add(36).writeU32(0x20000); desc.add(40).writeU32(0);
    let hr = call(device, DEV.CreateTex2D, 'int', ['pointer', 'pointer', 'pointer'])(device, desc, ptr(0), out);
    if (hr < 0) { send({t:'log', m:'staging failed ' + hr + ' ' + label}); return; }
    const staging = out.readPointer();
    if (samples > 1) {
      desc.add(28).writeU32(0); desc.add(36).writeU32(0);
      call(device, DEV.CreateTex2D, 'int', ['pointer', 'pointer', 'pointer'])(device, desc, ptr(0), out);
      const resolved = out.readPointer();
      call(context, CTX.Resolve, 'void', ['pointer', 'uint', 'pointer', 'uint', 'uint'])(context, resolved, 0, res, 0, fmt);
      call(context, CTX.CopyResource, 'void', ['pointer', 'pointer'])(context, staging, resolved);
      release(resolved);
    } else if (w && h) {
      const full = (textures.get(key(res)) || {mips:1}).mips;
      if (full === 1) call(context, CTX.CopyResource, 'void', ['pointer', 'pointer'])(context, staging, res);
      else call(context, 46, 'void', ['pointer', 'uint', 'uint', 'uint', 'uint', 'pointer', 'uint', 'pointer'])(context, staging, 0, 0, 0, 0, res, 0, ptr(0));
    }
    hr = call(context, CTX.Map, 'int', ['pointer', 'uint', 'uint', 'uint', 'pointer'])(context, staging, 0, 1, 0, map);
    if (hr >= 0) {
      const pitch = map.add(4).readU32();
      send(Object.assign({t:'tex', label, w, h, fmt, pitch, frame:frameNo}, extra || {}), map.readPointer().readByteArray(pitch * h));
      call(context, CTX.Unmap, 'void', ['pointer', 'uint'])(context, staging, 0);
    } else send({t:'log', m:'staging map failed ' + hr});
    release(staging);
  } finally { busy = false; }
}

function readBuffer(res, size) {
  busy = true;
  try {
    const desc = Memory.alloc(24), out = Memory.alloc(4), map = Memory.alloc(12);
    desc.writeU32(size); desc.add(4).writeU32(3); desc.add(8).writeU32(0); desc.add(12).writeU32(0x20000); desc.add(16).writeU32(0); desc.add(20).writeU32(0);
    if (call(device, DEV.CreateBuffer, 'int', ['pointer', 'pointer', 'pointer'])(device, desc, ptr(0), out) < 0) return null;
    const staging = out.readPointer();
    call(context, CTX.CopyResource, 'void', ['pointer', 'pointer'])(context, staging, res);
    let data = null;
    if (call(context, CTX.Map, 'int', ['pointer', 'uint', 'uint', 'uint', 'pointer'])(context, staging, 0, 1, 0, map) >= 0) {
      data = map.readPointer().readByteArray(size);
      call(context, CTX.Unmap, 'void', ['pointer', 'uint'])(context, staging, 0);
    }
    release(staging);
    return data;
  } finally { busy = false; }
}

function addBlob(buffer, size, source) {
  const at = frame.blobBytes;
  frame.blobs.push(source);
  frame.blobBytes += source.byteLength;
  frame.seen.add(buffer);
  return {buf:buffer, size, at, len:source.byteLength};
}

function viewList(table, count, listPtr) {
  const out = [];
  for (let i = 0; i < count; i++) { const v = listPtr.add(i * 4).readPointer(); out.push(v.isNull() ? null : (table.get(key(v)) || 'unknown')); }
  return out;
}

function afterDraw(kind) {
  const ev = {e:kind, ps:currentPs, vs:currentVs};
  frame.ev.push(ev);
  frame.draws++;
  if (dumpPs.has(currentPs) && currentRt.length && currentRt[0]) {
    const res = ptr(currentRt[0]);
    readTexture(res, 'after_' + currentPs + '_' + frame.draws, {draw:frame.draws});
  }
}

function startHeavy() {
  const c = context, H = (i, cb) => heavy.push(Interceptor.attach(vfn(c, i), cb));
  const bindCb = stage => ({onEnter(a) {
    if (busy || !a[0].equals(context)) return;
    const n = a[2].toUInt32(), list = [];
    for (let i = 0; i < n; i++) { const b = a[3].add(i * 4).readPointer(); const k = b.isNull() ? null : key(b); list.push(k); if (k) frame.bound.add(k); }
    frame.ev.push({e:stage + 'cb', start:a[1].toUInt32(), bufs:list});
  }});
  H(CTX.VSSetCB, bindCb('vs'));
  H(CTX.PSSetCB, bindCb('ps'));
  H(CTX.PSSetShader, {onEnter(a) { if (busy) return; currentPs = a[1].isNull() ? '' : (shaders.get(key(a[1])) || 'unknown'); frame.ev.push({e:'ps', id:currentPs}); }});
  H(CTX.VSSetShader, {onEnter(a) { if (busy) return; currentVs = a[1].isNull() ? '' : (shaders.get(key(a[1])) || 'unknown'); frame.ev.push({e:'vs', id:currentVs}); }});
  H(CTX.PSSetSRV, {onEnter(a) { if (busy) return; frame.ev.push({e:'srv', start:a[1].toUInt32(), res:viewList(srvs, a[2].toUInt32(), a[3])}); }});
  H(CTX.OMSetRT, {onEnter(a) { if (busy) return; currentRt = viewList(rtvs, a[1].toUInt32(), a[2]); frame.ev.push({e:'rt', res:currentRt}); }});
  H(CTX.Map, {
    onEnter(a) { this.skip = busy; this.res = a[1]; this.type = a[3].toUInt32(); this.out = a[5]; },
    onLeave(r) {
      if (this.skip || r.toInt32() < 0 || this.type === 1) return;
      const b = buffers.get(key(this.res));
      if (b && (b.bind & CB_BIND)) mapPending.set(key(this.res), this.out.readPointer());
    }});
  H(CTX.Unmap, {onEnter(a) {
    if (busy) return;
    const k = key(a[1]), p = mapPending.get(k);
    if (!p) return;
    mapPending.delete(k);
    const b = buffers.get(k);
    frame.ev.push(Object.assign({e:'cbdata', via:'map'}, addBlob(k, b.size, p.readByteArray(b.size))));
  }});
  H(CTX.UpdateSubresource, {onEnter(a) {
    if (busy) return;
    const k = key(a[1]), b = buffers.get(k);
    if (b && (b.bind & CB_BIND) && a[3].isNull()) frame.ev.push(Object.assign({e:'cbdata', via:'update'}, addBlob(k, b.size, a[4].readByteArray(b.size))));
  }});
  H(CTX.Draw, {onLeave() { if (!busy) afterDraw('draw'); }});
  H(CTX.DrawIndexed, {onLeave() { if (!busy) afterDraw('drawi'); }});
  H(CTX.DrawInstanced, {onLeave() { if (!busy) afterDraw('drawinst'); }});
  H(CTX.DrawIndexedInstanced, {onLeave() { if (!busy) afterDraw('drawiinst'); }});
}

function stopHeavy() {
  heavy.forEach(l => l.detach());
  heavy = [];
  Interceptor.flush();
}

function backbuffer(swap, label) {
  const iid = Memory.alloc(16), out = Memory.alloc(4);
  iid.writeByteArray([0xf2, 0xaa, 0x15, 0x6f, 0x08, 0xd2, 0x89, 0x4e, 0x9a, 0xb4, 0x48, 0x95, 0x35, 0xd3, 0x4f, 0x9c]);
  const hr = call(swap, 9, 'int', ['uint', 'pointer', 'pointer'])(swap, 0, iid, out);
  if (hr < 0) { send({t:'log', m:'GetBuffer failed ' + hr}); return; }
  const tex = out.readPointer();
  readTexture(tex, label);
  release(tex);
}

function onPresent(swap) {
  frameNo++;
  if (!context) return;
  try {
    if (capturing) {
      capturing = false;
      stopHeavy();
      // Constant buffers bound this frame but not rewritten in it: read the current contents.
      frame.bound.forEach(k => {
        if (frame.seen.has(k)) return;
        const b = buffers.get(k);
        if (!b) return;
        const data = readBuffer(ptr(k), b.size);
        if (data) frame.ev.push(Object.assign({e:'cbdata', via:'readback', carried:true}, addBlob(k, b.size, data)));
      });
      backbuffer(swap, 'final');
      const total = new Uint8Array(frame.blobBytes);
      let at = 0;
      frame.blobs.forEach(s => { total.set(new Uint8Array(s), at); at += s.byteLength; });
      const tex = {};
      textures.forEach((v, k) => { tex[k] = v; });
      const bufs = {};
      buffers.forEach((v, k) => { if (v.bind & CB_BIND) bufs[k] = v; });
      send({t:'frame', frame:frameNo, draws:frame.draws, events:frame.ev, buffers:bufs, textures:tex}, total.buffer);
      frame = null;
      send({t:'log', m:'frame capture sent'});
    }
    if (shotPending) { shotPending = false; backbuffer(swap, 'shot'); }
    if (armed > 0) {
      armed--;
      frame = {ev:[], blobs:[], blobBytes:0, seen:new Set(), bound:new Set(), draws:0};
      mapPending = new Map();
      capturing = true;
      startHeavy();
    }
  } catch (e) { send({t:'log', m:'present error ' + e.stack}); }
}

function hookFactory(mod) {
  const onFactory = {
    onEnter(a) { this.out = a[1]; },
    onLeave(r) {
      if (r.toInt32() < 0) return;
      const f = this.out.readPointer();
      Interceptor.attach(vfn(f, 10), {
        onEnter(b) { this.sc = b[3]; },
        onLeave(q) { if (q.toInt32() >= 0) hookSwap(this.sc.readPointer()); }});
    }};
  ['CreateDXGIFactory', 'CreateDXGIFactory1'].forEach(n => { const e = mod.findExportByName(n); if (e) Interceptor.attach(e, onFactory); });
}

function hookD3D(mod) {
  const adopt = (ppDev, ppCtx, ppSwap) => {
    if (ppDev && !ppDev.isNull()) hookDevice(ppDev.readPointer());
    if (ppCtx && !ppCtx.isNull() && !context) { context = ppCtx.readPointer(); send({t:'log', m:'context ' + context}); }
    if (ppSwap && !ppSwap.isNull()) hookSwap(ppSwap.readPointer());
  };
  const a = mod.findExportByName('D3D11CreateDeviceAndSwapChain');
  if (a) Interceptor.attach(a, {
    onEnter(x) { this.sw = x[8]; this.d = x[9]; this.c = x[11]; },
    onLeave(r) { if (r.toInt32() >= 0) adopt(this.d, this.c, this.sw); }});
  const b = mod.findExportByName('D3D11CreateDevice');
  if (b) Interceptor.attach(b, {
    onEnter(x) { this.d = x[7]; this.c = x[9]; },
    onLeave(r) { if (r.toInt32() >= 0) adopt(this.d, this.c, null); }});
}

const done = {};
function onModule(m) {
  const n = m.name.toLowerCase();
  if (n === 'd3d11.dll' && !done.d) { done.d = 1; hookD3D(m); send({t:'log', m:'d3d11 hooked'}); }
  if (n === 'dxgi.dll' && !done.g) { done.g = 1; hookFactory(m); send({t:'log', m:'dxgi hooked'}); }
}
Process.enumerateModules().forEach(onModule);
Process.attachModuleObserver({onAdded: onModule});

function listen() {
  recv('cmd', m => {
    if (m.op === 'shot') shotPending = true;
    if (m.op === 'arm') { armed = m.frames || 1; dumpPs = new Set(m.dumpPs || []); }
    if (m.op === 'status') send({t:'status', frameNo, device:String(device), context:String(context), swap:swapHooked, shaders:shaders.size, buffers:buffers.size, textures:textures.size});
    listen();
  });
}
listen();
send({t:'log', m:'agent ready'});
