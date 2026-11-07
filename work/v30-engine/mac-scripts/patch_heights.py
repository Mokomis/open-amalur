import re
from pathlib import Path
f=Path.home()/"Documents/Opem Amalur/work/v20-char/build_town.py";s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n")
n,c=re.subn(r"( *)if max\(q\) > 60000:.*\n\s*continue\n",lambda m:f"{m.group(1)}if 65535 in q:  # Marks a hole.\n{m.group(1)}    continue\n{m.group(1)}q = tuple(x - 65536 if x >= 32768 else x for x in q)  # Heights are signed: ground below the zero level has the top bit set.\n",s)
assert c==1,c
s=n
if crlf:s=s.replace("\n","\r\n")
f.write_bytes(s.encode());print("patched")
