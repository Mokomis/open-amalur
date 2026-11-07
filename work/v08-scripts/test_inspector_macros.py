"""Windows CLI integration tests for explicit bounded macro snapshot lists."""
import argparse,json,platform,struct,subprocess
from pathlib import Path
assert platform.system()=='Windows'
ap=argparse.ArgumentParser();ap.add_argument('--inspector',type=Path,required=True);ap.add_argument('--runtime-dir',type=Path,required=True)
ap.add_argument('--output-dir',type=Path,default=Path.home()/'Documents/Opem Amalur/outputs/scene-v08/inspector-macro-tests')
args=ap.parse_args();out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
(out/'probe.lua').write_text('return true\n',encoding='utf-8');(out/'modules.tsv').write_text('Probe\tprobe.lua\n',encoding='utf-8')
small=out/'small.bin';small.write_bytes(struct.pack('<4I',1,1,42,90168))
maximum=out/'maximum.bin';maximum.write_bytes(bytes(524296))
oversize=out/'oversize.bin';oversize.write_bytes(bytes(524297))
base=[str(args.inspector),'--runtime-dir',str(args.runtime_dir),'--modules-dir',str(out),'--module','Probe']
checks=[]
def run(label,extra,code,fragment=None,phase=None):
    result=subprocess.run(base+extra,text=True,capture_output=True,timeout=30)
    assert result.returncode==code,(label,result.returncode,result.stdout,result.stderr)
    report=json.loads(result.stdout) if code!=2 else None
    if fragment:assert fragment in (report['error'] if report else result.stderr),(label,result.stdout,result.stderr)
    if phase:assert report['phase']==phase,(label,report)
    if not code:assert report['root_loaded'] and report['ok'],(label,report)
    checks.append({'name':label,'exit_code':result.returncode,'report':report})
for category in ['1','255','0x37','0Xff']:
    run('valid category '+category,['--asset-macro','TEST_A',category,str(small)],0)
for category in ['0','256','0x100','-1','+1','1.5','0x',' 1','1e2']:
    run('invalid category '+repr(category),['--asset-macro','TEST_A',category,str(small)],2,'category')
run('invalid lowercase name',['--asset-macro','bad_name','1',str(small)],1,'uppercase','host_setup')
run('overlong name',['--asset-macro','A'*128,'1',str(small)],1,'uppercase','host_setup')
run('duplicate name',['--asset-macro','TEST_A','1',str(small),'--asset-macro','TEST_A','2',str(small)],1,'already exists','host_setup')
many=sum((['--asset-macro','TEST_'+str(i),'1',str(small)] for i in range(32)),[])
run('32 macros',many,0)
run('33 macros',many+['--asset-macro','TEST_32','1',str(small)],2,'32')
run('legacy loot plus31',['--loot-tables',str(small)]+many[:-4],0)
run('legacy loot plus32',['--loot-tables',str(small)]+many,2,'32')
run('per-source cap',['--asset-macro','TEST_A','1',str(oversize)],1,'524296','asset_macros')
run('total16MiB cap',sum((['--asset-macro','TEST_'+str(i),'1',str(maximum)] for i in range(32)),[]),1,'16MiB','asset_macros')
run('missing later source',['--asset-macro','TEST_A','1',str(small),'--asset-macro','TEST_B','1',str(out/'missing.bin')],1,'Cannot open','asset_macros')
report={'ok':True,'checks':len(checks),'scope':'Inspector argument/list/I/O limits with synthetic snapshots; no native asset behavior proof.','cases':checks}
(out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'ok':True,'checks':len(checks),'directory':str(out)}))
