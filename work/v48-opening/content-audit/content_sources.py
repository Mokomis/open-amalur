from pathlib import Path
import json,hashlib,subprocess,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur');OUT=ROOT/'work/v48-opening/content-audit';OUT.mkdir(parents=True,exist_ok=True)
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
SYMS=json.loads((ROOT/'work/v20-inputs/symbols.json').read_text())
LISTS={}
for a,n in [('DATA_0.pak','DATA'),('initial_0.pak','initial'),('patch_0.pak','patch')]:
 b=(ROOT/f'outputs/{n}-archive-list.txt').read_bytes();LISTS[a]=set(x.strip() for x in b.decode('utf-16' if b[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines())
def extract(names):
 rows=[];selected={}
 for a,ls in LISTS.items():
  wanted=sorted(set(names)&ls);d=OUT/'inputs'/a;d.mkdir(parents=True,exist_ok=True)
  missing=[n for n in wanted if not(d/n).exists()]
  for start in range(0,len(missing),30):
   batch=missing[start:start+30];r=subprocess.run([str(GAME/'modding/pakfileunpacker.exe'),str(GAME/'data'/a),'unpack',str(d),*batch],cwd=GAME/'modding',capture_output=True,timeout=240)
   (OUT/f'extract-{a}-{hashlib.sha256("|".join(batch).encode()).hexdigest()[:10]}.log').write_bytes(r.stdout+r.stderr)
   assert r.returncode==0,(a,r.returncode)
  for n in wanted:
   p=d/n;assert p.exists(),p;raw=p.read_bytes();rows.append(dict(archive=a,name=n,path=str(p.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()));selected[n]=p
 manifest=OUT/'extraction-receipt.json';prior=json.loads(manifest.read_text()) if manifest.exists() else []
 joined={(x['archive'],x['name']):x for x in prior+rows};manifest.write_text(json.dumps(list(joined.values()),indent=2)+'\n')
 return selected
def graph(path):
 d=Path(path).read_bytes();return d,d[8:8+struct.unpack_from('<I',d)[0]]
def arr(raw,b,slot,stride):
 p,n=struct.unpack_from('<II',b,slot);assert n<1000000 and (not n or p>=8 and p+n*stride<=len(b)+8),(slot,p,n,len(b));return [raw[p+i*stride:p+(i+1)*stride] for i in range(n)]
if __name__=='__main__':
 ids=[549780,1417252,1417255,1417257,1417259,1417261,1417263,1417265,1417267,1751255,1751258]
 names=[f'{i}.space_bxml' for i in ids]+[f'{i}.region_bxml' for i in [549773,1262814]]+[f'{i}.collision_set_bin' for i in [549771,549778,1262813,1417251,1417254,1417256,1417258,1417260,1417262,1417264,1417266,1751254,1751257]]+['1365769.lua_bxml']
 fs=extract(names);print([(n,p.stat().st_size) for n,p in fs.items()])
 summary=[]
 for sid in ids:
  raw,b=graph(fs[f'{sid}.space_bxml']);row={'space':sid,'name':SYMS['simspace'][str(sid)],'bytes':len(raw),'region':struct.unpack_from('<I',b,0x34)[0],'header_hex':b[:0x200].hex(),'arrays':{}}
  for slot,stride in [(0x98,80),(0x138,16),(0x140,16),(0x148,80),(0x150,84),(0x160,84),(0x170,84),(0x180,84),(0x1a8,12),(0x1b0,4)]:
   try:r=arr(raw,b,slot,stride);row['arrays'][hex(slot)]={'count':len(r),'stride':stride}
   except Exception as e:row['arrays'][hex(slot)]={'error':str(e)}
  summary.append(row)
 (OUT/'room-inventory.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
