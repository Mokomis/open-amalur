"""Bounded, read-only REA session, executed on the Windows analysis host."""
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

root = Path.home() / 'Documents' / 'Opem Amalur'
out = root / 'outputs' / 'initial-analysis'
out.mkdir(parents=True, exist_ok=False)
target = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
env = os.environ.copy()
env.update(GHIDRA_INSTALL_DIR=str(root / 'tools' / 'ghidra_12.1.4_PUBLIC'),
           JAVA_HOME=str(root / 'tools' / 'jdk-21.0.13+9'), REA_ANALYSIS_PROVIDER='ghidra')
rea = root / 'tools' / 'rea' / 'node_modules' / 'rea-agents' / 'scripts' / 'rea.mjs'
stderr = (out / 'server-stderr.log').open('w', encoding='utf-8')
proc = subprocess.Popen(['node', str(rea), 'mcp'], stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=stderr, text=True,
                        encoding='utf-8', env=env, bufsize=1)
responses = queue.Queue()
def reader():
    for line in proc.stdout:
        responses.put(json.loads(line))
    responses.put(None)
threading.Thread(target=reader, daemon=True).start()
serial = 0
def rpc(method, params, notify=False):
    global serial
    serial += 1
    message = {'jsonrpc': '2.0', 'method': method, 'params': params}
    if not notify:
        message['id'] = serial
    proc.stdin.write(json.dumps(message) + '\n')
    proc.stdin.flush()
    if notify:
        return
    deadline = time.monotonic() + 480
    while True:
        msg = responses.get(timeout=max(1, deadline-time.monotonic()))
        if msg is None:
            raise RuntimeError('REA exited unexpectedly')
        if msg.get('id') == serial:
            if 'error' in msg:
                raise RuntimeError(msg['error'])
            return msg['result']
        with (out / 'notifications.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(msg)+'\n')

def payload(result):
    if 'structuredContent' in result:
        return result['structuredContent']
    for item in result.get('content', []):
        if item.get('type') == 'text':
            try:
                return json.loads(item['text'])
            except ValueError:
                pass
    return result

def call(name, arguments, label=None):
    label = label or name
    print('START ' + label, flush=True)
    result = rpc('tools/call', {'name': name, 'arguments': arguments})
    (out / (label+'.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
    if result.get('isError'):
        raise RuntimeError(json.dumps(payload(result)))
    data = payload(result)
    print('DONE ' + label, flush=True)
    return data

before = hashlib.sha256(target.read_bytes()).hexdigest()
opened = False
try:
    init = rpc('initialize', {'protocolVersion':'2025-06-18',
        'capabilities':{}, 'clientInfo':{'name':'opem-amalur-analysis','version':'0.1'}})
    (out / 'server-identity.json').write_text(json.dumps(init, indent=2), encoding='utf-8')
    rpc('notifications/initialized', {}, notify=True)
    tool_list = rpc('tools/list', {})
    (out / 'tool-schemas.json').write_text(json.dumps(tool_list, indent=2), encoding='utf-8')
    call('open_binary', {'path':str(target), 'provider_id':'ghidra'})
    opened = True
    overview = call('binary_overview', {})
    print(json.dumps(overview.get('normalized_result', overview)), flush=True)
    patterns = {
        'candidate_luaL_loadfile':'8B 44 24 08 50 8B 44 24 08 8B 48 08 81 C1 A8 02',
        'candidate_lua_call':'8B 44 24 0C 8B 4C 24 08 8B 54 24 04 6A 00 50 51 52 E8 ?? ?? ?? ?? 83 C4 10 C3 CC CC CC CC CC 55 8B EC 83 EC 6C'
    }
    for name, pattern in patterns.items():
        found = call('search_bytes', {'pattern':pattern, 'limit':10}, name+'_matches')
        matches = found.get('normalized_result', {}).get('matches', [])
        print(json.dumps({'candidate':name,'matches':matches}), flush=True)
        if len(matches)==1 and matches[0].get('procedure'):
            call('procedure_pseudo_code', {'procedure':matches[0]['procedure']['address']}, name+'_pseudocode')
    call('search_strings', {'pattern':'Havok|Kore|cs:15032','mode':'regex','detail':'summary'}, 'script_engine_strings')
finally:
    if opened:
        try:
            call('export_evidence_bundle', {'path':str(out/'evidence.json')})
        finally:
            call('close_binary', {'snapshot_path':str(out/'analysis.snapshot.json')})
    proc.stdin.close()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait(timeout=10)
    stderr.close()
    after = hashlib.sha256(target.read_bytes()).hexdigest()
    (out/'input-integrity.json').write_text(json.dumps({'path':str(target),
        'sha256_before':before,'sha256_after':after,'unchanged':before==after},indent=2),encoding='utf-8')
    print('Input unchanged: '+str(before==after), flush=True)
