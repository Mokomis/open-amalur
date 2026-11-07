import sys,glob,os,json,collections
sys.path.insert(0,'work/v19-lighting')
import decode_scene_lighting as D
Z='0'*16
rk=collections.Counter()
for f in glob.glob('work/v19-inputs/*/*.region_bxml'):
    try:rk[D.decode_region(open(f,'rb').read())['region_key']['value']]+=1
    except D.DecodeError:pass
c=collections.Counter()
for f in glob.glob('work/v19-inputs/*/*.space_bxml'):
    try:k=D.decode_space_lights(open(f,'rb').read())['region_key']['value']
    except Exception:c['undecodable']+=1;continue
    c['zero' if k==Z else ('nonzero_match' if k in rk else 'nonzero_nomatch')]+=1
print('region files zero key',rk[Z],'of',sum(rk.values()),'distinct nonzero',len(rk)-1);print(dict(c))
p=json.load(open('outputs/scene-v19/lighting-provenance.json'))
for r in p['binding']:
    if r['claim'].startswith('Space links'):
        r['status']='hypothesis';r['evidence']='Spaces with a non-zero key: %d match a region key, %d do not. %d spaces and %d region files have an all-zero key, so this link cannot be the general binding; the native binding path is not traced'%(c['nonzero_match'],c['nonzero_nomatch'],c['zero'],rk[Z])
json.dump(p,open('outputs/scene-v19/lighting-provenance.json','w'),indent=1)
t=open('outputs/scene-v19/PROGRESS.txt').read()
old='799 of 950 decodable spaces match a region key; 151 do not and are unexplained.'
assert old in t
t=t.replace(old,'Space-to-region key match: %d non-zero matches, %d non-zero misses, %d all-zero keys. The key is not a general binding; the native space-to-region path is not traced.'%(c['nonzero_match'],c['nonzero_nomatch'],c['zero']))
open('outputs/scene-v19/PROGRESS.txt','w').write(t)
