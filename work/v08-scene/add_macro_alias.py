from pathlib import Path
import json,re,sys,platform
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';p=r/'outputs/scene-v08/asset-macros.json';m=json.loads(p.read_text());name,source=sys.argv[1:];assert not any(x['name']==name for x in m)
s=json.loads((r/'outputs/scene-v08/rea-session/all_macro_registration.json').read_text())['structuredContent']['normalized_result']
# Registration callback immediately precedes each ID/KEY registration.
rx=r'FUN_010a7430\(\*in_ECX,&LAB_([0-9a-f]+),0,[^;]+;(?:(?!FUN_010a7430).)*?FUN_00aa(?:3340|36c0)\([^;]*?"([A-Z_]+)"'
pairs={n:cb for cb,n in re.findall(rx,s,re.S)}
assert name in pairs and pairs[name]==pairs[source],(name,source,pairs)
x=next(x for x in m if x['name']==source);m.append({**x,'name':name,'native_alias_of':source,'registration':'aa9b50 -> '+pairs[name]});assert len(m)<=32;p.write_text(json.dumps(m,indent=2));print(m[-1])
