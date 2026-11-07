import sys,os,re,zipfile,hashlib,subprocess,collections,json
repo,rel,out=sys.argv[1:4]
os.chdir(repo)
idx={}
zips=[z for z in os.listdir(rel) if z.endswith('.zip')]
handles={z:zipfile.ZipFile(os.path.join(rel,z)) for z in zips}
for z,h in handles.items():
    n=h.namelist();print(z,'entries',len(n))
    for x in n: idx.setdefault(x.replace('\\','/'),[]).append((z,x))
files=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')[:-1]
REF3=('references/DevCortez--KoaModFramework/','references/ZucchiniZap--AmalurBxmlConverter/','references/mburbea--ModelSwapper/')
def cat(p):
    e=os.path.splitext(p)[1].lower();b=os.path.basename(p)
    if p.startswith('outputs/'):
        return None if e=='.md' or b in('PROGRESS.txt','continuation.json','README.txt') else 'outputs'
    if p.startswith('mac-coordination/'):return 'mac'
    if re.match(r'src/scene-v\d+/',p):return 'src-scene'
    if p.startswith('work/') and e in('.log','.png'):return 'work-logs'
    if p.startswith(REF3):return 'ref3'
    return None
st=collections.defaultdict(collections.Counter);bad=[];rem=[]
def dig(h,n):
    d=hashlib.sha256()
    with h.open(n) as f:
        for c in iter(lambda:f.read(1<<20),b''):d.update(c)
    return d.hexdigest()
for p in files:
    c=cat(p)
    if not c:continue
    rem.append(p)
    want=hashlib.sha256(open(p,'rb').read()).hexdigest()
    cands=[p]
    if p.startswith('mac-coordination/'):cands.append(p[len('mac-coordination/'):])
    found=None
    for k in cands:
        for z,n in idx.get(k,[]):
            if dig(handles[z],n)==want:found=z;break
        if found:break
    if found:st[c]['ok']+=1;st[c][found]+=1
    else:st[c]['MISSING']+=1;bad.append((c,p))
for c,v in st.items():print(c,dict(v))
print('total remove',len(rem),'bad',len(bad))
for x in bad[:40]:print(' BAD',x)
open(out,'w').write('\n'.join(rem)+'\n')
