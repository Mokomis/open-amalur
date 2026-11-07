from pathlib import Path
import hashlib,json,os,shutil,time
import worker
root=worker.BASE
source=Path(r'C:\OpenRune\work\rune-classic\System\Engine.dll')
expected='41458bac7e717a57effbe45d9351664ab79d72d7b821c3103018d057b7c585d0'
with worker.task_lock():
    pending=[p.stem for p in sorted((root/'jobs').glob('*.json')) if not (root/'results'/p.stem/'status.json').exists()]
    if pending: raise RuntimeError('Unstarted jobs exist; preserve queue: '+repr(pending))
    sha=worker.sha(source)
    if sha!=expected:raise RuntimeError('Windows source differs from Mac original')
    snapshot=root/'targets'/('rune-classic-engine-'+sha[:16]+'.dll')
    if not snapshot.exists():
        shutil.copyfile(source,snapshot)
        if worker.sha(snapshot)!=sha:raise RuntimeError('Copy hash mismatch')
        snapshot.chmod(0o444)
    if worker.sha(snapshot)!=sha:raise RuntimeError('Snapshot changed')
    configfile=root/'config.json'
    before=configfile.read_bytes()
    config=json.loads(before)
    target={'source':str(source),'snapshot':str(snapshot),'sha256':sha}
    old=config['targets'].get('rune-classic-engine')
    if old is not None and old!=target:raise RuntimeError('Existing target differs; refusing repoint')
    backup=None
    if old is None:
        backup=root/('config.pre-rune-'+time.strftime('%Y%m%d-%H%M%S')+'.json')
        backup.write_bytes(before)
        config['targets']['rune-classic-engine']=target
        tmp=root/'config.rune-new.tmp'
        tmp.write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
        os.replace(tmp,configfile)
    report={'target_id':'rune-classic-engine','target':target,'read_only':not bool(snapshot.stat().st_mode&0o200),'config_backup':str(backup) if backup else None,'preserved_target_ids':[k for k in config['targets'] if k!='rune-classic-engine'],'pending_jobs':pending}
    (root/'results/rune-registration-20261102.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
