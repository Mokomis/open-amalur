"""Validate decode_scene_lighting.py across all region_bxml files against shipped koalighting XML."""
import sys,glob,os,json,collections,struct,re
sys.path.insert(0,'work/v19-lighting')
import decode_scene_lighting as D
import xml.etree.ElementTree as ET
XML={}
for f in glob.glob('work/v19-inputs/initial_0.pak/*.koalighting'):
    b=open(f,'rb').read()
    if not b.startswith(b'<?xml'):continue
    o=ET.fromstring(b).find('DataObject');s=o.find("value[@name='settings']")
    if s is None:continue
    d={}
    for k in s:
        kn=k.attrib['name']
        for v in k:
            t=v.attrib['type'];n=v.attrib['name']
            if t=='float':d[(kn,n)]=float(v.text)
            elif t.endswith('HdrColorRgb'):d[(kn,n)]=[float(c.text) for c in v]
            elif t=='float4':d[(kn,n)]=[float(x) for x in v.text.split()]
            else:d[(kn,n)]=v.text
    dd=o.find("value[@name='directional_light_direction']")
    d['dir']=[float(x) for x in dd.text.split()] if dd is not None and dd.text else None
    fl=o.find("value[@name='flags']");d['flags']=int(fl.text) if fl is not None else None
    XML[os.path.basename(f)]=d
print('xml presets',len(XML))
def eq(a,b):return a is not None and abs(a-b)<=1e-5*(abs(b)+1e-3)
def flat(dec):
    out={}
    for name,rows in dec['environment']['time_keyed'].items():
        for k,r in rows.items():
            v=r['value']
            if name=='post_contrast':
                for i,c in enumerate('xyz'):out[(k,'post_contrast_'+c)]=v[i]
            elif isinstance(v,dict):out[(k,name)]=v['rgb']+[v['intensity']]
            elif name.endswith('_id') or name.endswith('_index'):continue
            else:out[(k,name)]=v
    return out
def score(F,X):
    ok=t=0;mis=[]
    for key,x in X.items():
        if not isinstance(key,tuple) or isinstance(x,str):continue
        y=F.get(key)
        if y is None:continue
        t+=1
        good=all(eq(a,b) for a,b in zip(y,x)) if isinstance(x,list) else eq(y,x)
        ok+=good
        if not good:mis.append(key)
    return ok,t,mis
files=glob.glob('work/v19-inputs/DATA_0.pak/*.region_bxml')+glob.glob('work/v19-inputs/patch_0.pak/*.region_bxml')
res=[];errs=[];pf=collections.Counter();pt=collections.Counter();groups=collections.defaultdict(set);cc=collections.Counter()
dirok=0;dirt=0;cubes=collections.Counter()
for f in files:
    try:dec=D.decode_region(open(f,'rb').read())
    except D.DecodeError as e:errs.append((os.path.basename(f),str(e)));continue
    F=flat(dec);best=None
    for n,X in XML.items():
        ok,t,mis=score(F,X)
        d=dec['environment']['directional_light_direction']['value']
        dok=X['dir'] is not None and all(eq(a,b) for a,b in zip(d,X['dir']))
        s=(ok/t if t else 0,dok,ok,n,mis)
        if best is None or s[:3]>best[:3]:best=s
    res.append((os.path.basename(os.path.dirname(f)),os.path.basename(f),best[0],best[1],best[2],best[3],best[4][:6]))
    groups[best[3]].add(os.path.basename(f))
    X=XML[best[3]]
    if best[0]==1:
        for key in X:
            if isinstance(key,tuple) and not isinstance(X[key],str) and key in F:pt[key[1]]+=1;pf[key[1]]+=1
    for r in dec['environment']['time_keyed']['ambient_cube_index'].values():cubes[r['value']<len(dec['ambient_cubes'])]+=1
    for r in dec['environment']['time_keyed']['character_ambient_cube_index'].values():cubes[r['value']<len(dec['ambient_cubes'])]+=1
    cc.update(r['value'] for r in dec['environment']['time_keyed']['color_correction_texture_id'].values())
full=[r for r in res if r[2]==1 and r[3]];near=[r for r in res if not(r[2]==1 and r[3])]
print('decoded',len(res),'errors',errs)
print('exact all-fields+direction',len(full),'presets used',len({r[5] for r in full}))
print('not exact',len(near))
for r in sorted(near,key=lambda r:r[2])[:20]:print(' ',r[0][:5],r[1],round(r[2],3),r[3],r[5],r[6][:3])
print('cube index in range',cubes)
L=open('outputs/initial-archive-list.txt','rb').read();L=L.decode('utf-16' if L[:2]==b'\xff\xfe' else 'utf-8-sig')
D2=open('outputs/DATA-archive-list.txt','rb').read();D2=D2.decode('utf-16' if D2[:2]==b'\xff\xfe' else 'utf-8-sig');N=set(re.findall(r'(?m)^(\d+)',L+'\n'+D2))
print('cc ids',len(cc),'found as asset ids',sum(str(i) in N for i in cc),'top',cc.most_common(5))
json.dump(dict(decoded=len(res),exact=len(full),presets=len({r[5] for r in full}),not_exact=[dict(archive=r[0],file=r[1],score=r[2],direction=r[3],preset=r[5],mismatches=[list(m) for m in r[6]]) for r in near],region_to_preset={r[0][:-6]+'/'+r[1]:r[5] for r in full}),open('outputs/scene-v19/decoder-validation.json','w'),indent=1)
sh=[r for r in res if r[1]=='524912.region_bxml'];print('shop',[r[:6] for r in sh])
for name,sp in [('shop space','work/scene-inputs-v07/DATA_0.pak/524859.space_bxml')]:
    d=D.decode_space_lights(open(sp,'rb').read());print(name,d['region_key']['value'],len(d['lights']),d['lights'][0]['time_keyed']['Noon'])
    r=D.decode_region(open('work/v19-inputs/DATA_0.pak/524912.region_bxml','rb').read());print('region key',r['region_key']['value'],'sky',r['sky_asset_id']['value'],'hours',r['day_division_hours']['value'])
    e=r['environment'];print({k:e['time_keyed'][k]['Noon']['value'] for k in('directional_light_color','directional_light_intensity','environment_tint','shadow_color','shadow_opacity','fog_start','fog_density','ambient_cube_index','character_ambient_cube_index','color_correction_texture_id')},e['directional_light_direction']['value'])
