// Copies the inputs and output of named passes during one frame. Pointers come from the frame capture.
'use strict';
const device = ptr(DEVICE_PTR), context = ptr(CONTEXT_PTR);
const PASSES = {
  '0x53c11538': {name:'combine', before:{lit0:'0x46ccfca4', lit1:'0x46ccf524', lit2:'0x46ccfe64', lit3:'0x46ccfaa4', ramp:'0x46cd6ce4'}, after:{out:'0x46ccf8e4'}},
  '0x5318c078': {name:'lut', before:{}, after:{out:'0x53069fe4'}},
  '0x5318beb8': {name:'merge', before:{lut:'0x53069fe4', scene:'0x46ccf8e4', second:'0x46ccf6e4', bloom:'0x46cd79e4'}, after:{out:'0x46cd7424'}},
  '0x5318c378': {name:'final', before:{in:'0x46cd7424'}, after:{}},
};
const vfn = (o, i) => o.readPointer().add(i * 4).readPointer();
const call = (o, i, ret, args) => new NativeFunction(vfn(o, i), ret, ['pointer'].concat(args), 'stdcall');
const stdcall = (m, n, ret, args) => new NativeFunction(Process.getModuleByName(m).getExportByName(n), ret, args, 'stdcall');
const release = o => { if (!o.isNull()) call(o, 2, 'uint', [])(o); };
let busy = false, armed = false, currentPs = null, frameNo = 0, done = false, handled = new Set(), hooks = [];

function dump(res, label) {
  busy = true;
  try {
    const d = Memory.alloc(44), out = Memory.alloc(4), m = Memory.alloc(12);
    call(res, 10, 'void', ['pointer'])(res, d);
    const w = d.readU32(), h = d.add(4).readU32(), fmt = d.add(16).readU32();
    d.add(28).writeU32(3); d.add(32).writeU32(0); d.add(36).writeU32(0x20000); d.add(40).writeU32(0);
    if (call(device, 5, 'int', ['pointer', 'pointer', 'pointer'])(device, d, ptr(0), out) < 0) { send({t:'log', m:'staging failed ' + label}); return; }
    const s = out.readPointer();
    call(context, 47, 'void', ['pointer', 'pointer'])(context, s, res);
    if (call(context, 14, 'int', ['pointer', 'uint', 'uint', 'uint', 'pointer'])(context, s, 0, 1, 0, m) >= 0) {
      const pitch = m.add(4).readU32();
      send({t:'tex', label, w, h, fmt, pitch}, m.readPointer().readByteArray(pitch * h));
      call(context, 15, 'void', ['pointer', 'uint'])(context, s, 0);
    }
    release(s);
  } finally { busy = false; }
}

const draw = {
  onEnter() {
    this.pass = null;
    if (busy || !armed || !currentPs) return;
    const p = PASSES[currentPs];
    if (!p || handled.has(currentPs)) return;
    handled.add(currentPs);
    this.pass = p;
    for (const k in p.before) dump(ptr(p.before[k]), p.name + '_in_' + k);
  },
  onLeave() {
    if (!this.pass) return;
    for (const k in this.pass.after) dump(ptr(this.pass.after[k]), this.pass.name + '_' + k);
  }};

function presentAddress() {
  const title = Memory.allocUtf16String('STATIC');
  const hwnd = stdcall('user32.dll', 'CreateWindowExW', 'pointer', ['uint', 'pointer', 'pointer', 'uint', 'int', 'int', 'int', 'int', 'pointer', 'pointer', 'pointer', 'pointer'])(0, title, title, 0x80000000, 0, 0, 16, 16, ptr(0), ptr(0), ptr(0), ptr(0));
  const d = Memory.alloc(60);
  d.writeU32(16); d.add(4).writeU32(16); d.add(16).writeU32(28); d.add(28).writeU32(1); d.add(36).writeU32(0x20); d.add(40).writeU32(1); d.add(44).writePointer(hwnd); d.add(48).writeU32(1);
  const ps = Memory.alloc(4), pd = Memory.alloc(4), pc = Memory.alloc(4);
  const hr = stdcall('d3d11.dll', 'D3D11CreateDeviceAndSwapChain', 'int', ['pointer', 'uint', 'pointer', 'uint', 'pointer', 'uint', 'uint', 'pointer', 'pointer', 'pointer', 'pointer', 'pointer'])(ptr(0), 5, ptr(0), 0, ptr(0), 0, 7, d, ps, pd, ptr(0), pc);
  if (hr < 0) throw new Error('dummy swapchain ' + hr);
  const addr = vfn(ps.readPointer(), 8);
  release(pc.readPointer()); release(ps.readPointer()); release(pd.readPointer());
  stdcall('user32.dll', 'DestroyWindow', 'int', ['pointer'])(hwnd);
  return addr;
}

Interceptor.attach(presentAddress(), {onEnter() {
  if (done) return;
  frameNo++;
  try {
    if (frameNo === 10) {
      armed = true;
      hooks.push(Interceptor.attach(vfn(context, 9), {onEnter(a) { if (!busy) currentPs = a[1].toString(); }}));
      hooks.push(Interceptor.attach(vfn(context, 13), draw));
      hooks.push(Interceptor.attach(vfn(context, 12), draw));
    } else if (frameNo === 11) {
      armed = false; done = true;
      hooks.forEach(h => h.detach());
      send({t:'log', m:'passes handled ' + handled.size});
      send({t:'done'});
    }
  } catch (e) { done = true; send({t:'log', m:'error ' + e.stack}); send({t:'done'}); }
}});
send({t:'log', m:'stage agent ready'});
