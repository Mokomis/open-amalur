from pathlib import Path
f=Path.home()/"Documents/Opem Amalur/work/v20-char/build_town.py";s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n")
a="        if 65535 in q:  # Marks a hole.\n            continue\n"
assert a in s
s=s.replace(a,a+"        # Each tile carries a mask beside its heights. A cell with all four corners at 0 is cut out: canyons and riverbeds are built from models there.\n        m = masks[n]\n        if m is not None and not (m[iy * 19 + ix] or m[iy * 19 + ix + 1] or m[(iy + 1) * 19 + ix] or m[(iy + 1) * 19 + ix + 1]):\n            return None\n",1)
i=s.index('pickle.load(open(');j=s.rfind("\n",0,i)+1
line=s[j:s.index("\n",i)]
print(line[:150])
ind=line[:len(line)-len(line.lstrip())]
s=s[:j]+ind+'masks = pickle.load(open(root / "work/v20-char/terrain-masks.pkl", "rb"))\n'+s[j:]
if crlf:s=s.replace("\n","\r\n")
f.write_bytes(s.encode());print("ok")
