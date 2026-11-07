import re,struct
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
ib=0x400000
o2v=lambda o:o-0xf61000+0x1362000
v=[(o2v(m.start()),m.group().decode()) for m in re.finditer(rb'[a-z][a-z0-9_]{2,50}\.(?:vso|fso)\x00',c[0xf61000:0xf61000+0x453800]) ]
v=[(a+0xf61000-0xf61000,b) for a,b in v]
print(len(v));print(' '.join(sorted({b[:-1] for a,b in v})))
for a,b in v:
    if re.search('light|sun|fog|deferred|bloom|shadow|sky',b):print(hex(a+0),b)
