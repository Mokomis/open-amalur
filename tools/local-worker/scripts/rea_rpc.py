"""Private, owned REA stdio connection; reuses the project's installed REA."""
import base64
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time


class Rea:
    def __init__(self, base, output):
        self.base = Path(base)
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        project = Path.home() / 'Documents/Opem Amalur'
        env = os.environ.copy()
        temp = self.base / 'analysis'
        temp.mkdir(exist_ok=True)
        env.update(GHIDRA_INSTALL_DIR=str(project/'tools/ghidra_12.1.4_PUBLIC'),
                   JAVA_HOME=str(project/'tools/jdk-21.0.13+9'),
                   REA_ANALYSIS_PROVIDER='ghidra',
                   REA_GHIDRA_STARTUP_TIMEOUT_MS='600000',
                   GHIDRA_HEADLESS_MAXMEM='2G', TEMP=str(temp), TMP=str(temp))
        env['PATH'] = str(project/'tools/jdk-21.0.13+9/bin') + os.pathsep + env['PATH']
        self.err = (self.output/'rea-stderr.log').open('w', encoding='utf-8')
        self.p = subprocess.Popen(
            [r'C:\Program Files\nodejs\node.exe', str(project/'tools/rea/node_modules/rea-agents/scripts/rea.mjs'), 'mcp'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err,
            text=True, encoding='utf-8', errors='replace', env=env, bufsize=1)
        self.messages = queue.Queue()
        self.serial = 0
        self.opened = False
        def read():
            try:
                for line in self.p.stdout:
                    try: self.messages.put(json.loads(line))
                    except ValueError: self.messages.put({'unparsed_stdout': line[:1000]})
            finally:
                self.messages.put(None)
        threading.Thread(target=read, daemon=True).start()
        self.rpc('initialize', {'protocolVersion':'2025-06-18', 'capabilities':{},
                               'clientInfo':{'name':'open-amalur-local-worker','version':'1.0'}})
        self.p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized','params':{}})+'\n')
        self.p.stdin.flush()
        self.catalog = {x['name']:x for x in self.rpc('tools/list', {})['tools']}
        (self.output/'tool-catalog.json').write_text(json.dumps(self.catalog, indent=2), encoding='utf-8')

    def rpc(self, method, params, timeout=660):
        self.serial += 1
        request = {'jsonrpc':'2.0','id':self.serial,'method':method,'params':params}
        self.p.stdin.write(json.dumps(request)+'\n')
        self.p.stdin.flush()
        deadline = time.monotonic()+timeout
        while True:
            msg = self.messages.get(timeout=max(0.1, deadline-time.monotonic()))
            if msg is None: raise RuntimeError('REA closed its stdout; inspect rea-stderr.log')
            if msg.get('id') != self.serial: continue
            if 'error' in msg: raise RuntimeError(json.dumps(msg['error']))
            return msg['result']

    def call(self, name, arguments, label=None):
        if name not in self.catalog: raise ValueError('Unadvertised REA tool: '+name)
        result = self.rpc('tools/call', {'name':name,'arguments':arguments})
        if label:
            (self.output/(label+'.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
        if name == 'open_binary' and not result.get('isError'): self.opened = True
        if name == 'close_binary' and not result.get('isError'): self.opened = False
        return result

    def close(self):
        try:
            if self.opened: self.call('close_binary', {}, 'close-binary')
        finally:
            try: self.p.stdin.close()
            except OSError: pass
            try: self.p.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.p.terminate()
                self.p.wait(timeout=15)
            self.err.close()


if __name__ == '__main__':
    base = Path(__file__).resolve().parents[1]
    r = Rea(base, base/'results/rea-discovery')
    try:
        names = ['open_binary','inspect_native_exports','inspect_pe_imports','search_procedures',
                 'analyze_function','procedure_pseudo_code','procedure_assembly','procedure_callees',
                 'inspect_analysis_view','close_binary']
        selected = {n:r.catalog[n] for n in names if n in r.catalog}
        (base/'rea-selected-tools.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
        print(json.dumps({'advertised_tools':len(r.catalog),'selected':list(selected)}))
    finally:
        r.close()
