import os,re,sys,json,collections
root=os.getcwd()
dirs=['work/v19-host','work/v19-capture','work/v19-lighting','work/v20-char','work/v20-town','work/v21-ui','work/v22-stress','work/v23-actors','work/v23-audio','work/v24-zones','work/v25-fx','work/v30-engine/proxy','work/v30-engine/vk']
top_v30=['PLAN.md','ApplyAndExport.java','CountFuncs.java','callers_map.py','closewin.ps1','d3d_needs.py','desk.ps1','frame_compare.py','game_ctl.ps1','job_size.py','load_save.ps1','pe32_size.py','rec_report.py','rec_run.ps1','render_map.py','rtti_names.py','scene_compare.py','scene_run.ps1','show_fn.py','trace_counts.py','trace_diff.py','trace_runs.py','wins.ps1','winshot.ps1','run_export.cmd','run_ghidra.cmd','run-dxvk.cmd','run-rec.cmd','run-vk.cmd','functions-summary.txt']
ext={'.c','.h','.cpp','.hpp','.inc','.py','.cmd','.ps1','.bat','.java','.md','.txt','.js','.xml','.def','.cmake','.sh','.gradle'}
skipdir=re.compile(r'(^|/)(build|build-android-arm64|build-windows|__pycache__|spv|include|shaders|pack|live-pack|zone-pack|live|fonts)(/|$)')
out=[];rej=collections.Counter();big=[]
for d in dirs:
    for a,ds,fs in os.walk(d):
        ra=a.replace('\\','/')
        if skipdir.search(ra): rej['skipdir']+=len(fs); continue
        for f in fs:
            p=ra+'/'+f; e=os.path.splitext(f)[1].lower(); n=os.path.getsize(p)
            if f=='CMakeLists.txt' or e in ext:
                if n>1500000: big.append((n,p)); rej['big']+=1; continue
                out.append(p)
            else: rej[e]+=1
for f in top_v30: out.append('work/v30-engine/'+f)
out.append('work/CURRENT_STATE.txt')
out=[p for p in out if os.path.exists(p) and not p.endswith('.dll')]
open('work/v30-engine/publish-list.txt','w',newline='\n').write('\n'.join(sorted(set(out)))+'\n')
print('files',len(set(out)),'MB',round(sum(os.path.getsize(p) for p in set(out))/1e6,1))
print('by dir',collections.Counter('/'.join(p.split('/')[:2]) for p in out).most_common(20))
print('largest',[(round(os.path.getsize(p)/1e6,2),p) for p in sorted(set(out),key=os.path.getsize)[-8:]])
print('rejected',rej.most_common(25))
print('big',big[:12])
pat=re.compile(rb'(?i)(storepass|keypass|password\s*[=:]|api[_-]?key|secret|BEGIN [A-Z ]*PRIVATE KEY|ghp_|gho_|sk-[A-Za-z0-9]{20}|AKIA[0-9A-Z]{10})')
hits=[]
for p in set(out):
    d=open(p,'rb').read()
    for m in pat.finditer(d):
        s=d.rfind(b'\n',0,m.start())+1;e=d.find(b'\n',m.end())
        hits.append((p,d[s:min(e,s+110)].decode('latin1').strip()))
print('secret-like',len(hits))
seen=set()
for p,l in hits:
    k=(p.split('/')[1],re.sub(r'\s+',' ',l)[:60])
    if k in seen: continue
    seen.add(k); print('  ',p[:50],'|',re.sub(r'(?i)((storepass|keypass|pass:|password)\S*\s*\S{0,2})\S+',r'\1***',l)[:100])
    if len(seen)>25: break
