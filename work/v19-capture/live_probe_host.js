// One shot: attach to the running game, capture, detach. Exits by itself after 90 seconds at most.
'use strict';
const fs = require('fs'), path = require('path');
const root = path.join(process.env.USERPROFILE, 'Documents', 'Opem Amalur');
const frida = require(path.join(root, 'tools', 'rea-frida', 'node_modules', 'frida'));
const dir = path.join(root, 'work', 'v19-capture'), run = path.join(dir, process.argv[2]);
fs.mkdirSync(run, {recursive: true});
const log = m => { console.log(m); fs.appendFileSync(path.join(run, 'host.log'), new Date().toISOString() + ' ' + m + '\n'); };
const text = fs.readFileSync(path.join(dir, 'run', 'host.log'), 'utf8');
const pid = Number(fs.readFileSync(path.join(dir, 'run', 'pid.txt'), 'utf8'));
const devicePtr = /device (0x[0-9a-f]+)/.exec(text)[1], contextPtr = /context (0x[0-9a-f]+)/.exec(text)[1];
let n = 0;

(async () => {
  const device = await frida.getLocalDevice();
  const session = await device.attach(pid);
  const source = fs.readFileSync(path.join(dir, 'live_probe_agent.js'), 'utf8').replace('DEVICE_PTR', "'" + devicePtr + "'").replace('CONTEXT_PTR', "'" + contextPtr + "'");
  const script = await session.createScript(source);
  const end = async why => { log('ending: ' + why); try { await script.unload(); await session.detach(); } catch (e) { log('detach ' + e.message); } process.exit(0); };
  const timer = setTimeout(() => end('timeout'), 90000);
  script.message.connect((message, data) => {
    if (message.type !== 'send') { log('script ' + JSON.stringify(message).slice(0, 1500)); return; }
    const p = message.payload;
    if (p.t === 'log') log(p.m);
    else if (p.t === 'tex') {
      const base = 'tex_' + (++n) + '_' + p.label;
      fs.writeFileSync(path.join(run, base + '.raw'), data);
      fs.writeFileSync(path.join(run, base + '.json'), JSON.stringify(p));
      log('texture ' + base + ' ' + p.w + 'x' + p.h + ' fmt ' + p.fmt);
    } else if (p.t === 'frame') {
      fs.writeFileSync(path.join(run, 'frame.bin'), data);
      fs.writeFileSync(path.join(run, 'frame.json'), JSON.stringify(p));
      log('frame draws ' + p.draws + ' events ' + p.events.length + ' bytes ' + data.length);
    } else if (p.t === 'done') { clearTimeout(timer); end('done'); }
  });
  await script.load();
  log('attached ' + pid);
})().catch(e => { log('fatal ' + e.stack); process.exit(1); });
