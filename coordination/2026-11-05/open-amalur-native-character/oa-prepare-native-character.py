from pathlib import Path
import shutil
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v37-native-character');src=r/'src';assert not src.exists();shutil.copytree(r.parent/'v36-native-ranges/src',src)
for n in ['oa_native_geometry.h','oa_native_geometry.cpp','oa_character_fixture.inc','oa_character_palette.inc']:shutil.copyfile(r/n,src/'framework/decode'/n)
print('Prepared isolatedv37character branch;v36preserved')
