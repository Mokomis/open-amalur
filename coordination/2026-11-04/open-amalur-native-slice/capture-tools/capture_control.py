"""One-game, one-frame capture configuration with checked restoration.

Runs on the Mac. Uses existing ADB/root, and never changes Steam saves or drivers.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

HERE = Path(__file__).resolve().parent
ADB = ['/opt/homebrew/bin/adb', '-s', '99cc517a']
ROOT = '/data/user/0/com.droiddeck.launcher/files/linuxfs'
CONFIG = ROOT + '/root/.config/droiddeck/game-environment.json'
TOOLS = ROOT + '/root/oa-native-tools'
BACKUP = HERE / 'game-environment.before.json'
ARMED = HERE / 'game-environment.armed.json'
OPTIONS = {
    'VK_ADD_LAYER_PATH': '/root/oa-native-tools',
    'VK_INSTANCE_LAYERS': 'VK_LAYER_LUNARG_gfxreconstruct:VK_LAYER_VALVE_rpo:VK_LAYER_VALVE_fdm_injection',
    'GFXRECON_CAPTURE_FILE': '/root/oa-native-tools/captures/amalur.gfxr',
    'GFXRECON_CAPTURE_TRIGGER': 'F10',
    'GFXRECON_CAPTURE_TRIGGER_FRAMES': '1',
    'GFXRECON_CAPTURE_FILE_TIMESTAMP': 'true',
    'GFXRECON_MEMORY_TRACKING_MODE': 'unassisted',
    'GFXRECON_LOG_FILE': '/root/oa-native-tools/capture.log',
    'GFXRECON_LOG_FILE_FLUSH_AFTER_WRITE': 'true',
}

def root(command):
    return subprocess.run(ADB + ['exec-out', 'su -c ' + shlex.quote(command)],
                          check=True, stdout=subprocess.PIPE).stdout

def read_config():
    return root('cat ' + shlex.quote(CONFIG))

def write_config(data):
    stage = HERE / 'game-environment.upload.json'
    stage.write_bytes(data)
    subprocess.run(ADB + ['push', str(stage), '/data/local/tmp/oa-game-environment.json'], check=True)
    root('set -e; cp /data/local/tmp/oa-game-environment.json ' + shlex.quote(CONFIG + '.oa-tmp') +
         '; chown 10307:10307 ' + shlex.quote(CONFIG + '.oa-tmp') +
         '; chmod 600 ' + shlex.quote(CONFIG + '.oa-tmp') +
         '; mv ' + shlex.quote(CONFIG + '.oa-tmp') + ' ' + shlex.quote(CONFIG))
    assert read_config() == data, 'Configuration readback differs'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'arm', 'restore'])
    action = parser.parse_args().action
    original = read_config()
    current = json.loads(original)
    assert current['version'] == 1 and isinstance(current['games'], dict)
    if action == 'status':
        game = current['games'].get('1041720', {})
        print(json.dumps({'armed': all(game.get(k) == v for k,v in OPTIONS.items()),
                          'capture_settings': {k:game[k] for k in OPTIONS if k in game}}, indent=2))
    elif action == 'arm':
        if ARMED.exists() and original == ARMED.read_bytes():
            print('Already armed; backup preserved.'); return
        if BACKUP.exists() and original != BACKUP.read_bytes():
            raise SystemExit('Configuration changed since backup; review before re-arming.')
        BACKUP.write_bytes(original)
        root('set -e; mkdir -p ' + shlex.quote(TOOLS + '/captures') + '; chown 10307:10307 ' +
             shlex.quote(TOOLS) + ' ' + shlex.quote(TOOLS + '/captures') +
             '; cp -n ' + shlex.quote(CONFIG) + ' ' + shlex.quote(TOOLS + '/game-environment.before.json'))
        current['games'].setdefault('1041720', {}).update(OPTIONS)
        data = (json.dumps(current, indent=2) + '\n').encode()
        write_config(data)
        ARMED.write_bytes(data)
        print('Armed one F10-triggered frame for Amalur only. Original SHA256=' + hashlib.sha256(original).hexdigest())
    else:
        if not BACKUP.exists() or not ARMED.exists():
            raise SystemExit('No owned configuration backup; refusing to restore.')
        if original == BACKUP.read_bytes():
            print('Already restored.'); return
        if original != ARMED.read_bytes():
            raise SystemExit('Configuration changed externally; refusing to overwrite it. Merge owned fields manually.')
        write_config(BACKUP.read_bytes())
        print('Original configuration restored and byte-matched.')

if __name__ == '__main__':
    main()
