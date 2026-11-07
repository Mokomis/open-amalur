from pathlib import Path
root=Path.home()/'Documents'/'Opem Amalur'
for n in ['initial','DATA','patch']:
 d=(root/f'outputs/{n}-archive-list.txt').read_bytes();t=d.decode('utf-16' if d.startswith(b'\xff\xfe') else 'utf-8-sig')
 rows=[l.strip() for l in t.splitlines() if '.visualbundle' in l or 'space_visual' in l or 'world' in l.lower() and l.endswith('.bin')];print(n,rows)
