from pathlib import Path
import sys,time,subprocess,configparser,json,re
sys.stdout.reconfigure(encoding='utf-8')
P=Path(__file__).resolve().parents[2];V=P/'work/v47-performance';D=V/'reference-data';L=D/'desktop.log';F=D/'properties.ini'
def setp(**kw):
 c=configparser.ConfigParser();c.read(F,encoding='utf-8')
 for k,val in kw.items():c['properties']['debug.opem.'+k]=str(val)
 tmp=F.with_suffix('.tmp');tmp.write_text(''.join(['[properties]\n']+[k+'='+val+'\n' for k,val in c['properties'].items()]),encoding='utf-8');tmp.replace(F)
def wait(needle,start,timeout=40):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  s=L.read_text(encoding='utf-8',errors='replace')[start:]
  if re.search(needle,s):return s
  time.sleep(.1)
 raise RuntimeError('No matching evidence: '+needle)
result=[]
for mode,tag in [(1,'cached-a'),(0,'legacy'),(1,'cached-b')]:
 start=len(L.read_text(encoding='utf-8',errors='replace'));setp(rendercache=mode,materialprobe=-1)
 wait('stage=final',start)
 start=len(L.read_text(encoding='utf-8',errors='replace'));setp(materialprobe=0)
 probes=wait('DepthProbe error=',start)
 lines=[x for x in probes.splitlines() if 'MaterialProbe' in x or 'DepthProbe' in x]
 (V/(tag+'-probes.log')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
 out=V/(tag+'.png')
 if out.exists():raise RuntimeError('Preserve existing evidence '+str(out))
 cap=subprocess.run([sys.executable,str(P/'work/v40-windows-host/control.py'),'capture','--user-data',str(D),'--out',str(out)],capture_output=True,text=True)
 if cap.returncode:raise RuntimeError(cap.stdout+cap.stderr)
 metrics=wait('RENDER_CACHE enabled='+str(mode),start)
 rcline=[x for x in metrics.splitlines() if 'RENDER_CACHE enabled='+str(mode) in x][-1]
 rc={k:int(val) for k,val in re.findall(r'([a-z_]+)=(\d+)',rcline)}
 depths={m[0]+','+m[1]:int(m[2]) for m in re.findall(r'DepthProbe pixel=(\d+),(\d+) raw24=(\d+)',probes)}
 colors={stage+' '+xy:rgba for stage,xy,rgba in re.findall(r'MaterialProbe mode=0 stage=(\S+) pixel=(\d+,\d+) rgba=([\d,]+)',probes)}
 result.append(dict(tag=tag,mode=mode,counters=rc,depths=depths,colors=colors,capture=str(out)))
 print(tag,json.dumps(rc),flush=True)
a,b,c=result
checks=dict(all_depth_samples_equal=a['depths']==b['depths']==c['depths'],all_opaque_samples_equal={k:x for k,x in a['colors'].items() if k.startswith('opaque ')}=={k:x for k,x in b['colors'].items() if k.startswith('opaque ')}=={k:x for k,x in c['colors'].items() if k.startswith('opaque ')},warm_uniform_queries_zero=a['counters']['uniform_gl_queries']==c['counters']['uniform_gl_queries']==0,legacy_queries_positive=b['counters']['uniform_gl_queries']>0,active_program_setup_reduced=a['counters']['world_program_setups']<b['counters']['world_program_setups'],texture_binds_reduced=a['counters']['texture_gl_binds']<b['counters']['texture_gl_binds'])
(V/'windows-ab-results.json').write_text(json.dumps(dict(results=result,checks=checks,benchmark_warning='Windows ANGLE offscreen host is for correctness/call-count comparison, not Android FPS.'),indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2));sys.exit(0 if all(checks.values()) else 1)
