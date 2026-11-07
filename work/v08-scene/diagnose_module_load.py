from pathlib import Path
import os,subprocess,json,platform
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';src=out/'modules';dst=out/'diagnostic-modules';dst.mkdir(exist_ok=True)
manifest=(src/'modules.tsv').read_text()
for line in manifest.splitlines():
 if not line or line.startswith('#'):continue
 _,name=line.split('\t');p=dst/name
 if not p.exists():os.link(src/name,p)
(dst/'diagnostic.lua').write_text('''local ok,err=pcall(require,'SpaceCommon')
print('LOAD',ok,err)
for _,name in ipairs({'Constants','main_menu','menu_tools','SpaceCommon'}) do
 local t=_G[name];print('GLOBAL',name,type(t),t,package.loaded[name],type(t)=='table' and __amalur_module_table_allowed(t))
 if type(t)=='table' then local mt=getmetatable(t);print('META',mt,mt and mt.__index, _G);print('FIELDS',t._NAME,t._M, t.general_audio) end
end
error(err or 'diagnostic completed')
''')
(dst/'modules.tsv').write_text(manifest+'\nDiagnostic\tdiagnostic.lua\n')
s=(r/'work/run_bootstrap.py').read_text().replace("str(out/'modules')","str(dst)").replace("'--module','SpaceCommon','--event','on_object_creation_complete'","'--module','Diagnostic'")
s=s.replace("import platform,json,subprocess","import platform,json,subprocess").replace("if j.get('error'):","if False:")
# Inspector stdout mixes intentionally printed diagnostics with its final JSON.
s=s.replace("j=json.loads(s)","j={}")
exec(compile(s,'run-diagnostic','exec'),{'dst':dst,'__name__':'__main__'})
