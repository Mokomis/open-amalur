from pathlib import Path
import platform,json,subprocess
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';macros=json.loads((out/'asset-macros.json').read_text());import argparse
p=argparse.ArgumentParser();p.add_argument('--label',default='scene-latest-test');p.add_argument('--kind',default='1');a=p.parse_args()
cmd=[str(r/'work/v08-portable/build-windows/amalur-scene-v08-inspect.exe'),'--runtime-dir',str(r/'work/v08-portable/runtime'),'--modules-dir',str(out/'modules'),'--bootstrap-module','ParentUtils','--module','SpaceCommon','--event','on_object_creation_complete','--memory-mib','256','--instruction-budget','30000000','--input-actions',str(r/'work/scene-inputs-v07/initial_0.pak/inputdeviceaction_init.bin'),'--native-profile','16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314','--no-optional-content','--android-platform','--fresh-profile','--no-quick-save','--no-language-packs','--preview-renderer']
cmd+=['--android-standard-layout'] if a.kind=='android' else ['--controller-kind',a.kind]
cmd+=['--enums',str(out/'assets/compiled_enums.bin')]
for m in macros:cmd+=['--asset-macro',m['name'],str(m['category']),str(out/'assets'/m['file'])]
p=subprocess.run(cmd,capture_output=True,timeout=90);s=p.stdout.decode('utf8');(out/(a.label+'.json')).write_text(s);print(s);print(p.stderr.decode('utf8'));j=json.loads(s)
if j.get('error'):
 import re
 match=re.search(r'\[string "([^"]+)"\]:(\d+)',j['error'])
 if match:
  files=dict(line.split('\t') for line in (out/'modules/modules.tsv').read_text().splitlines() if line and not line.startswith('#'))
  lines=(out/'modules'/files[match[1]]).read_text().splitlines();n=int(match[2]);print('\n'.join(lines[max(0,n-25):n+5]))
