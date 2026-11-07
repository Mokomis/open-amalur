import re, struct, json
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
b=(root/"work/v21-ui/simtype/bins/batch_8130.simtype_bxml").read_bytes()
n=struct.unpack_from("<I",b,0)[0]
tab=[struct.unpack_from("<II",b,4+8*i) for i in range(n)]
print(n,tab[:4],'data start',4+8*n,'sum sizes',sum(s for _,s in tab),'len',len(b))
off={};o=4+8*n
for i,s in tab: off[i]=(o,s);o+=s
print('end',o)
S=json.loads((root/"work/v20-inputs/symbols.json").read_text())
ids={}
for cat,v in S.items():
    if isinstance(v,dict):
        for k,nm in v.items(): ids.setdefault(int(k),f"{cat}:{nm}")
sim=S["simtype"]; byname={str(v):int(k) for k,v in sim.items()}
def show(name):
    i=byname[name]; 
    if i not in off: print('##',name,'absent');return
    o,s=off[i];r=b[o:o+s]
    print('##',name,i,'size',s)
    print(r[:64].hex())
    res=[]
    for q in range(0,len(r)-3):
        v=struct.unpack_from('<I',r,q)[0]
        if v in ids and v>1000: res.append((q,ids[v]))
    print(' ids',res[:18])
    print(' str',re.findall(rb'[A-Za-z_][\w. \-]{3,}',r)[:10])
for nm in ['sword1h_common01a','sword1h_common01b','sword1h_common02a','warrior_common01a_torso','alchemypotion_healthrestoration_01','parent_sword_1h']:
    show(nm)
a=b[off[byname['sword1h_common01a']][0]:sum(off[byname['sword1h_common01a']])]
c=b[off[byname['sword1h_common02a']][0]:sum(off[byname['sword1h_common02a']])]
print('len',len(a),len(c))
print('diff',[(q,a[q],c[q]) for q in range(min(len(a),len(c))) if a[q]!=c[q]][:60])
print('all a',a.hex())
