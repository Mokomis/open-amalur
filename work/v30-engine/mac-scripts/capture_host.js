// Spawns koa.exe through Frida with no file or config patch; commands arrive as lines in cmd.txt.
'use strict';
const fs = require('fs'), path = require('path');
const root = path.join(process.env.USERPROFILE, 'Documents', 'Opem Amalur');
const frida = require(path.join(root, 'tools', 'rea-frida', 'node_modules', 'frida'));
const dir = path.join(root, 'work', 'v19-capture');
const run = path.join(dir, 'run');
fs.mkdirSync(path.join(run, 'shaders'), {recursive: true});
const logFile = path.join(run, 'host.log');
const log = m => fs.appendFileSync(logFile, new Date().toISOString() + ' ' + m + '\n');
const game = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Kingdoms of Amalur Re-Reckoning';
let counter = 0;

(async () => {
  const device = await frida.getLocalDevice();
  const pid = await device.spawn(path.join(game, 'koa.exe'), {cwd: game, env: {SteamAppId: '1041720', SteamGameId: '1041720', GameId: '1041720'}});
  log('spawned ' + pid);
  fs.writeFileSync(path.join(run, 'pid.txt'), String(pid));
  const session = await device.attach(pid);
  session.detached.connect(reason => { log('detached ' + reason); fs.writeFileSync(path.join(run, 'exited.txt'), String(reason)); process.exit(0); });
  const script = await session.createScript(fs.readFileSync(path.join(dir, 'd3d_agent.js'), 'utf8'));
  script.message.connect((message, data) => {
    if (message.type !== 'send') { log('script ' + JSON.stringify(message).slice(0, 1500)); return; }
    const p = message.payload;
    if (p.t === 'log') log(p.m);
    else if (p.t === 'status') { log(JSON.stringify(p)); fs.writeFileSync(path.join(run, 'status.json'), JSON.stringify(p)); }
    else if (p.t === 'shader') { const f = path.join(run, 'shaders', p.kind + '_' + p.sum + '.dxbc'); if (!fs.existsSync(f)) fs.writeFileSync(f, data); }
    else if (p.t === 'tex') {
      const base = 'tex_' + String(++counter).padStart(4, '0') + '_' + p.label;
      fs.writeFileSync(path.join(run, base + '.raw'), data);
      fs.writeFileSync(path.join(run, base + '.json'), JSON.stringify(p));
      log('texture ' + base + ' ' + p.w + 'x' + p.h + ' fmt ' + p.fmt);
    } else if (p.t === 'frame') {
      const base = 'frame_' + String(++counter).padStart(4, '0');
      fs.writeFileSync(path.join(run, base + '.bin'), data);
      fs.writeFileSync(path.join(run, base + '.json'), JSON.stringify(p));
      log('frame ' + base + ' draws ' + p.draws + ' events ' + p.events.length + ' bytes ' + data.length);
    }
  });
  await script.load();
  await device.resume(pid);
  log('resumed');
  const cmdFile = path.join(run, 'cmd.txt');
  setInterval(() => {
    if (!fs.existsSync(cmdFile)) return;
    const text = fs.readFileSync(cmdFile, 'utf8');
    fs.unlinkSync(cmdFile);
    for (const line of text.split(/\r?\n/)) {
      if (!line.trim()) continue;
      const m = JSON.parse(line.replace(/^\uFEFF/, ''));
      log('cmd ' + line);
      if (m.op === 'detach') { session.detach(); return; }
      script.post({type: 'cmd', ...m});
    }
  }, 500);
})().catch(e => { log('fatal ' + e.stack); process.exit(1); });
