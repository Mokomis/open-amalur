import re,struct,json,collections
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
H=[m.start() for m in re.finditer(b'D\x00XBC',c)]
print(len(H),H[:4],H[-2:])
cnt=collections.Counter()
for i in H[:400]:
    cnt[struct.unpack_from('<I',c,i-8)[0]]+=1
print(cnt.most_common(8))
for i in H[3:9]:
    print(hex(i),c[i-32:i+8].hex())
rows=json.load(open('outputs/scene-v19/shader-blobs.json'))
print(rows[:3]);
oks={r['file_offset'] for r in rows}
bad=[i for i in H if i not in oks][:6]
for i in bad:print('BAD',hex(i),c[i-32:i+12].hex())
