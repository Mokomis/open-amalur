import re,struct,os
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
R=[m.start() for m in re.finditer(b'RDEF',c)]
print(R[:5],R[-3:])
o=R[0];print(c[o-0x60:o+0x40].hex());print(c[o-0x60:o+0x60])
# gap stats
print([R[i+1]-R[i] for i in range(12)])
p=[m.start() for m in re.finditer(rb'\d{3,8}\.[vf]so',c)][:3];print(p)
print(os.path.exists(r'C:\Windows\System32\D3DCompiler_47.dll'),os.path.exists(r'C:\Windows\System32\d3dcompiler_43.dll'))
