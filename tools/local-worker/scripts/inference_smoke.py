"""Prove inference and native tool-call output before assigning an investigation."""
from pathlib import Path
import json
import time
import urllib.request
from resource_monitor import Monitor

BASE=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:18180'


def call(path,payload=None):
    req=urllib.request.Request(URL+path,None if payload is None else json.dumps(payload).encode(),{'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as f:return json.load(f)


def main():
    models=call('/v1/models')
    model=models['data'][0]['id']
    monitor=Monitor(BASE/'results/inference-smoke-resources.jsonl').start()
    start=time.monotonic()
    plain=call('/v1/chat/completions',{'model':model,'messages':[{'role':'user','content':'Reply with exactly: LOCAL_READY'}],
              'max_tokens':32,'temperature':0,'chat_template_kwargs':{'enable_thinking':False}})
    first=time.monotonic()-start
    tool=call('/v1/chat/completions',{'model':model,'messages':[{'role':'system','content':'Call the record_probe tool with label local-ready. Do not answer in prose.'},
                 {'role':'user','content':'Run the local tool-call probe now.'}],
                 'tools':[{'type':'function','function':{'name':'record_probe','description':'Record that the local tool-call interface is working.',
                  'parameters':{'type':'object','properties':{'label':{'type':'string'}},'required':['label'],'additionalProperties':False}}}],
                 'tool_choice':'required','max_tokens':192,'temperature':0,
                 'chat_template_kwargs':{'enable_thinking':False}})
    tc=tool['choices'][0]['message'].get('tool_calls',[])
    valid=bool(tc) and tc[0]['function']['name']=='record_probe' and json.loads(tc[0]['function']['arguments'])['label']=='local-ready'
    result={'model_id':model,'models_response':models,'plain_seconds':first,'total_seconds':time.monotonic()-start,
            'plain_response':plain,'tool_response':tool,'native_tool_call_valid':valid,'resources':monitor.stop()}
    (BASE/'results/inference-smoke.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'model_id':model,'plain_seconds':first,'tool_call_valid':valid,'resources':result['resources']}))
    if not valid:raise SystemExit(1)


if __name__=='__main__':main()
