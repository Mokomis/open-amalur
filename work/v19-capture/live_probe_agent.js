// Late-attach D3D11 observer. Reads object descriptions live, so it needs no creation-time tables.
// Records two frames across immediate and deferred contexts, and copies the backbuffer through staging.
'use strict';
const CTX = {VSSetCB:7, PSSetSRV:8, PSSetShader:9, VSSetShader:11, DrawIndexed:12, Draw:13, Map:14, Unmap:15, PSSetCB:16,
  DrawIndexedInstanced:20, DrawInstanced:21, OMSetRT:33, CopyResource:47, UpdateSubresource:48, ExecuteCommandList:58, FinishCommandList:114};
const device = ptr(DEVICE_PTR), context = ptr(CONTEXT_PTR), FRAMES = 2;
const vfn = (o, i) => o.readPointer().add(i * 4).readPointer();
const call = (o, i, ret, args) => new NativeFunction(vfn(o, i), ret, ['pointer'].concat(args), 'stdcall');
const release = o => { if (!o.isNull()) call(o, 2, 'uint', [])(o); };
const key = p => p.toString();
const stdcall = (m, n, ret, args) => new NativeFunction(Process.getModuleByName(m).getExportByName(n), ret, args, 'stdcall');

function presentAddress() {
  const title = Memory.allocUtf16String('STATIC');
  const hwnd = stdcall('user32.dll', 'CreateWindowExW', 'pointer', ['uint', 'pointer', 'pointer', 'uint', 'int', 'int', 'int', 'int', 'pointer', 'pointer', 'pointer', 'pointer'])(0, title, title, 0x80000000, 0, 0, 16, 16, ptr(0), ptr(0), ptr(0), ptr(0));
  const d = Memory.alloc(60);
  d.writeU32(16); d.add(4).writeU32(16); d.add(16).writeU32(28); d.add(28).writeU32(1); d.add(36).writeU32(0x20); d.add(40).writeU32(1); d.add(44).writePointer(hwnd); d.add(48).writeU32(1);
  const ps = Memory.alloc(4), pd = Memory.alloc(4), pc = Memory.alloc(4);
  const create = stdcall('d3d11.dll', 'D3D11CreateDeviceAndSwapChain', 'int', ['pointer', 'uint', 'pointer', 'uint', 'pointer', 'uint', 'uint', 'pointer', 'pointer', 'pointer', 'pointer', 'pointer']);
  const hr = create(ptr(0), 5, ptr(0), 0, ptr(0), 0, 7, d, ps, pd, ptr(0), pc);
  if (hr < 0) throw new Error('dummy swapchain ' + hr);
  const addr = vfn(ps.readPointer(), 8);
  release(pc.readPointer()); release(ps.readPointer()); release(pd.readPointer());
  stdcall('user32.dll', 'DestroyWindow', 'int', ['pointer'])(hwnd);
  return addr;
}

const bufferInfo = new Map(), texInfo = new Map(), viewRes = new Map();
function describeBuffer(p) {
  const k = key(p);
  if (bufferInfo.has(k)) return bufferInfo.get(k);
  const type = Memory.alloc(4);
  call(p, 7, 'void', ['pointer'])(p, type);
  let info = {dim:type.readU32()};
  if (info.dim === 1) {
    const d = Memory.alloc(24);
    call(p, 10, 'void', ['pointer'])(p, d);
    info = {dim:1, size:d.readU32(), usage:d.add(4).readU32(), bind:d.add(8).readU32()};
  }
  bufferInfo.set(k, info);
  return info;
}
function describeView(v) {
  const k = key(v);
  if (viewRes.has(k)) return viewRes.get(k);
  const out = Memory.alloc(4);
  call(v, 7, 'void', ['pointer'])(v, out);
  const res = out.readPointer();
  const rk = key(res);
  if (!texInfo.has(rk)) {
    const type = Memory.alloc(4);
    call(res, 7, 'void', ['pointer'])(res, type);
    const dim = type.readU32();
    if (dim === 3) {
      const d = Memory.alloc(44);
      call(res, 10, 'void', ['pointer'])(res, d);
      texInfo.set(rk, {dim, w:d.readU32(), h:d.add(4).readU32(), fmt:d.add(16).readU32(), samples:d.add(20).readU32(), bind:d.add(32).readU32()});
    } else texInfo.set(rk, {dim});
  }
  release(res);
  viewRes.set(k, rk);
  return rk;
}
const views = (n, list) => { const o = []; for (let i = 0; i < n; i++) { const v = list.add(i * 4).readPointer(); o.push(v.isNull() ? null : describeView(v)); } return o; };

let frame = null, frameNo = 0, remaining = 0, heavy = [], busy = false, finished = false, swapSeen = null, pending = new Map();
const started = Date.now();

function blob(data) {
  const at = frame.bytes;
  frame.blobs.push(data);
  frame.bytes += data.byteLength;
  return {at, len:data.byteLength};
}
const push = (a, e) => { e.ctx = key(a); e.tid = Process.getCurrentThreadId(); frame.ev.push(e); };

function startHeavy() {
  const seen = new Set();
  const H = (i, cb, deferred) => [context].concat(deferred || []).forEach(c => {
    const f = key(vfn(c, i));
    if (seen.has(i + f)) return;
    seen.add(i + f);
    heavy.push(Interceptor.attach(ptr(f), cb));
  });
  const out = Memory.alloc(4);
  call(device, 27, 'int', ['uint', 'pointer'])(device, 0, out);
  const def = [out.readPointer()];
  const bindCb = stage => ({onEnter(a) {
    if (busy) return;
    const n = a[2].toUInt32(), bufs = [];
    for (let i = 0; i < n; i++) {
      const b = a[3].add(i * 4).readPointer();
      if (b.isNull()) { bufs.push(null); continue; }
      const k = key(b), info = describeBuffer(b);
      bufs.push({buf:k, size:info.size});
      frame.bound.add(k);
    }
    push(a[0], {e:stage + 'cb', start:a[1].toUInt32(), bufs});
  }});
  H(CTX.VSSetCB, bindCb('vs'), def);
  H(CTX.PSSetCB, bindCb('ps'), def);
  H(CTX.PSSetShader, {onEnter(a) { if (!busy) push(a[0], {e:'ps', id:key(a[1])}); }}, def);
  H(CTX.VSSetShader, {onEnter(a) { if (!busy) push(a[0], {e:'vs', id:key(a[1])}); }}, def);
  H(CTX.PSSetSRV, {onEnter(a) { if (!busy) push(a[0], {e:'srv', start:a[1].toUInt32(), res:views(a[2].toUInt32(), a[3])}); }}, def);
  H(CTX.OMSetRT, {onEnter(a) { if (!busy) push(a[0], {e:'rt', res:views(a[1].toUInt32(), a[2])}); }}, def);
  H(CTX.Map, {
    onEnter(a) { this.skip = busy; this.ctx = a[0]; this.res = a[1]; this.type = a[3].toUInt32(); this.out = a[5]; },
    onLeave(r) {
      if (this.skip || r.toInt32() < 0 || this.type === 1) return;
      const info = describeBuffer(this.res);
      if (info.dim === 1 && (info.bind & 4)) pending.set(key(this.ctx) + key(this.res), this.out.readPointer());
    }}, def);
  H(CTX.Unmap, {onEnter(a) {
    if (busy) return;
    const k = key(a[0]) + key(a[1]), p = pending.get(k);
    if (!p) return;
    pending.delete(k);
    const info = describeBuffer(a[1]);
    frame.seen.add(key(a[1]));
    push(a[0], Object.assign({e:'cbdata', via:'map', buf:key(a[1]), size:info.size}, blob(p.readByteArray(info.size))));
  }}, def);
  H(CTX.UpdateSubresource, {onEnter(a) {
    if (busy) return;
    const info = describeBuffer(a[1]);
    if (info.dim === 1 && (info.bind & 4) && a[3].isNull()) {
      frame.seen.add(key(a[1]));
      push(a[0], Object.assign({e:'cbdata', via:'update', buf:key(a[1]), size:info.size}, blob(a[4].readByteArray(info.size))));
    }
  }}, def);
  const draw = kind => ({onEnter(a) { if (!busy) { frame.draws++; push(a[0], {e:kind}); } }});
  H(CTX.Draw, draw('draw'), def);
  H(CTX.DrawIndexed, draw('drawi'), def);
  H(CTX.DrawInstanced, draw('drawinst'), def);
  H(CTX.DrawIndexedInstanced, draw('drawiinst'), def);
  H(CTX.ExecuteCommandList, {onEnter(a) { if (!busy) push(a[0], {e:'exec', list:key(a[1])}); }}, def);
  H(CTX.FinishCommandList, {
    onEnter(a) { this.ctx = a[0]; this.out = a[2]; },
    onLeave(r) { if (!busy && r.toInt32() >= 0) push(this.ctx, {e:'finish', list:key(this.out.readPointer())}); }}, def);
  release(def[0]);
}

function readTexture(res, label) {
  busy = true;
  try {
    const d = Memory.alloc(44), out = Memory.alloc(4), m = Memory.alloc(12);
    call(res, 10, 'void', ['pointer'])(res, d);
    const w = d.readU32(), h = d.add(4).readU32(), fmt = d.add(16).readU32(), samples = d.add(20).readU32();
    if (samples > 1) { send({t:'log', m:'multisampled ' + label + ' skipped'}); return; }
    d.add(28).writeU32(3); d.add(32).writeU32(0); d.add(36).writeU32(0x20000); d.add(40).writeU32(0);
    if (call(device, 5, 'int', ['pointer', 'pointer', 'pointer'])(device, d, ptr(0), out) < 0) { send({t:'log', m:'staging failed'}); return; }
    const s = out.readPointer();
    call(context, CTX.CopyResource, 'void', ['pointer', 'pointer'])(context, s, res);
    if (call(context, CTX.Map, 'int', ['pointer', 'uint', 'uint', 'uint', 'pointer'])(context, s, 0, 1, 0, m) >= 0) {
      const pitch = m.add(4).readU32();
      send({t:'tex', label, w, h, fmt, pitch}, m.readPointer().readByteArray(pitch * h));
      call(context, CTX.Unmap, 'void', ['pointer', 'uint'])(context, s, 0);
    }
    release(s);
  } finally { busy = false; }
}

function readBuffer(res, size) {
  busy = true;
  try {
    const d = Memory.alloc(24), out = Memory.alloc(4), m = Memory.alloc(12);
    d.writeU32(size); d.add(4).writeU32(3); d.add(12).writeU32(0x20000);
    if (call(device, 3, 'int', ['pointer', 'pointer', 'pointer'])(device, d, ptr(0), out) < 0) return null;
    const s = out.readPointer();
    call(context, CTX.CopyResource, 'void', ['pointer', 'pointer'])(context, s, res);
    let data = null;
    if (call(context, CTX.Map, 'int', ['pointer', 'uint', 'uint', 'uint', 'pointer'])(context, s, 0, 1, 0, m) >= 0) {
      data = m.readPointer().readByteArray(size);
      call(context, CTX.Unmap, 'void', ['pointer', 'uint'])(context, s, 0);
    }
    release(s);
    return data;
  } finally { busy = false; }
}

function backbuffer(swap, label) {
  const iid = Memory.alloc(16), out = Memory.alloc(4);
  iid.writeByteArray([0xf2, 0xaa, 0x15, 0x6f, 0x08, 0xd2, 0x89, 0x4e, 0x9a, 0xb4, 0x48, 0x95, 0x35, 0xd3, 0x4f, 0x9c]);
  if (call(swap, 9, 'int', ['uint', 'pointer', 'pointer'])(swap, 0, iid, out) < 0) { send({t:'log', m:'GetBuffer failed'}); return; }
  const t = out.readPointer();
  readTexture(t, label);
  release(t);
}

function finish(swap) {
  heavy.forEach(l => l.detach());
  heavy = [];
  frame.bound.forEach(k => {
    if (frame.seen.has(k)) return;
    const info = bufferInfo.get(k);
    if (!info) return;
    const data = readBuffer(ptr(k), info.size);
    if (data) frame.ev.push(Object.assign({e:'cbdata', via:'readback', buf:k, size:info.size}, blob(data)));
  });
  backbuffer(swap, 'final');
  const total = new Uint8Array(frame.bytes);
  let at = 0;
  frame.blobs.forEach(s => { total.set(new Uint8Array(s), at); at += s.byteLength; });
  const tex = {}; texInfo.forEach((v, k) => { tex[k] = v; });
  send({t:'frame', draws:frame.draws, events:frame.ev, textures:tex}, total.buffer);
  frame = null;
  finished = true;
  send({t:'done'});
}

function onPresent(a) {
  frameNo++;
  try {
    if (finished) return;
    if (frameNo === 30) { send({t:'log', m:'fps ' + (30000 / (Date.now() - started)).toFixed(1) + ' swap ' + a}); backbuffer(a, 'before'); }
    if (frameNo === 32) {
      frame = {ev:[], blobs:[], bytes:0, seen:new Set(), bound:new Set(), draws:0};
      remaining = FRAMES;
      startHeavy();
      return;
    }
    if (frame && --remaining === 0) finish(a);
  } catch (e) { send({t:'log', m:'present error ' + e.stack}); finished = true; heavy.forEach(l => l.detach()); heavy = []; send({t:'done'}); }
}

const addr = presentAddress();
send({t:'log', m:'present at ' + addr + ' in ' + Process.findModuleByAddress(addr).name});
Interceptor.attach(addr, {onEnter(a) { onPresent(a[0]); }});
