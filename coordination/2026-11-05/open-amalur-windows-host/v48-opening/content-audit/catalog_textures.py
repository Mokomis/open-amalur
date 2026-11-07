from pathlib import Path
import sys,json,struct,hashlib,collections
sys.dont_write_bytecode=True
Q=Path(__file__).resolve().parent;sys.path.insert(0,str(Q));import content_sources as C
def main():
 mats=json.loads((Q/'first-room-material-catalog.json').read_text());assets=sorted({r['asset'] for m in mats for r in m['texture_references']})
 names=[name for tid in assets for name in [f'{tid}.dds']+[f'{tid}_{k}.dds' for k in range(6)]]
 fs=C.extract(names);rows=[];selected=[];total=0
 for tid in assets:
  carriers=[]
  for name in [f'{tid}.dds']+[f'{tid}_{k}.dds' for k in range(6)]:
   if name not in fs:continue
   f=fs[name];b=f.read_bytes()
   if len(b)<38 or b[16:20]!=b'KEEN':carriers.append(dict(name=name,path=str(f.relative_to(C.ROOT)),error='not38BKEEN'));continue
   w,h=struct.unpack_from('<2H',b,20);fmt=b[29];levels=struct.unpack_from('<H',b,35)[0];at=38;ww,hh=w,h;lev=[]
   block=8 if fmt in [1,2] else 16 if fmt==5 else None
   if block:
    for l in range(levels):
     n=((ww+3)//4)*((hh+3)//4)*block;lev.append(dict(level=l,width=ww,height=hh,source_offset=at,bytes=n));at+=n;ww,hh=max(1,ww//2),max(1,hh//2)
   carriers.append(dict(name=name,path=str(f.relative_to(C.ROOT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),width=w,height=h,format=fmt,mips=levels,levels=lev,expected_2d_bytes=at,complete_2d=at==len(b)))
  good=[r for r in carriers if r.get('complete_2d') and r['format'] in [1,5] and r['width']>0 and r['height']>0]
  best=max(good,key=lambda x:(x['width']*x['height'],x['mips'],x['bytes'])) if good else None
  if best:
   n=sum(l['width']*l['height']*4 for l in best['levels']);total+=n;selected.append(dict(asset=tid,name=C.SYMS['texture'][str(tid)],carrier=best,decoded_rgba_bytes=n))
  rows.append(dict(asset=tid,name=C.SYMS['texture'][str(tid)],carriers=carriers,selected_name=best['name'] if best else None))
 report=dict(status='Source authored carrier inventory, no capture-residency claim',assets=len(assets),selected_2d=len(selected),rgba_total_bytes=total,selection='Per-name PATCH>initial>DATA, then largest declared complete2D authored chain; no resizing/mipmap generation. Nativeopeningquality/residency unobserved.',textures=rows,selected=selected)
 (Q/'first-room-texture-catalog.json').write_text(json.dumps(report,indent=2)+'\n');print('ASSETS',len(assets),'SELECTED2D',len(selected),'RGBA_MB',total/1048576);print('UNSELECTED',[(r['asset'],r['name'],[(c.get('format'),c.get('width'),c.get('height'),c.get('complete_2d')) for c in r['carriers']]) for r in rows if not r['selected_name']])
if __name__=='__main__':main()
