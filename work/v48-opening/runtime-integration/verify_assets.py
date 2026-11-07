from pathlib import Path
import hashlib,json
Q=Path(__file__).resolve().parent
rows=json.loads((Q/'asset-integrity.json').read_text())
for r in rows:
 p=Q/'assets'/r['path'];data=p.read_bytes()
 assert len(data)==r['size'] and hashlib.sha256(data).hexdigest()==r['sha256'],r['path']
print(json.dumps({'passed':True,'verified_assets':len(rows),'bytes':sum(r['size'] for r in rows)}))
