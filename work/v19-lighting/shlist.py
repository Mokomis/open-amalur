import re,glob,struct
def lst(n):
    b=open(f'outputs/{n}-archive-list.txt','rb').read();return [x.strip() for x in b.decode('utf-16' if b[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines() if x.strip()]
for n in('initial','patch','DATA'):
    L=lst(n);h=[x for x in L if re.search(r'(\.vso|\.fso|\.cso|\.fxo|\.hlsl|\.fx$|platform_shader|shader_init|compiled_shader|shaders?\.)',x,re.I)]
    print(n,len(h),h[:40])
b=open('work/v19-inputs/initial_0.pak/symbol_table_platform_shader.bin','rb').read()
s=sorted({m.group().decode() for m in re.finditer(rb'[A-Za-z_][A-Za-z0-9_\.:\[\]]{3,70}',b)});print('symtab strings',len(s),s[:20]);
n=struct.unpack_from('<I',b)[0];print('n',n,'hex',b[:80].hex());print(b[-400:])
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
print('d3d',sorted({m.group().decode() for m in re.finditer(rb'(?i)(d3d[0-9a-z_]{1,16}\.dll|dxgi\.dll|opengl32\.dll|vulkan[-0-9a-z]*\.dll)',c)}))
v=sorted({m.group().decode() for m in re.finditer(rb'[A-Za-z0-9_]{2,60}\.(?:vso|fso|gso|cso)',c)});print('shader names',len(v));print(' '.join(x for x in v if x.endswith('.fso')))
names=sorted({m.group().decode() for m in re.finditer(rb'[A-Za-z_][A-Za-z0-9_]{3,50}',c) if re.search(rb'(?i)(^g_|^c_|^u_|^cb|ConstantBuffer|Lighting|LightCount|FogParam|FogColor|ExposureL|Tonemap|ToneMap|Luminance|EnvMap|AmbientCube|Attenuation|ShadowMap|DirLight|SunDir|DirectionalLight)',m.group())});print('const names',len(names));print(' '.join(names)[:3500])
