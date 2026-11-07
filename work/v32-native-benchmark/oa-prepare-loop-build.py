from pathlib import Path
import zipfile,json
root=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark')
def extract(archive,target):
 target.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(archive) as z:
  for name in z.namelist():
   rel=Path(*name.split('/')[1:])
   if not str(rel) or str(rel)=='.':continue
   if '..' in rel.parts:raise RuntimeError('Unsafe archive path')
   dest=target/rel
   if name.endswith('/'):dest.mkdir(parents=True,exist_ok=True)
   else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
extract(root/'downloads/oa-gfx-loop-source.zip',root/'src')
for name,target in [('Vulkan-Headers',root/'src/external/Vulkan-Headers'),('SPIRV-Headers',root/'src/external/SPIRV-Headers'),('lz4',root/'deps/lz4'),('zlib',root/'deps/zlib'),('zstd',root/'deps/zstd')]:
 extract(root/'downloads'/(name+'.zip'),target)
print('Pinned source/dependencies extracted into isolated v32 folder.')
