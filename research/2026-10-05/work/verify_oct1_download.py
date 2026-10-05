from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent.parent
out=root/'outputs/drive_analysis_20261001'
rows=[]
for line in (out/'source_hashes_latest.txt').read_text().splitlines():
 expected,remote=line.split(None,1);rel=remote.split('/realdata/',1)[1];p=root/'work/drive_logs_20261001'/rel
 actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
 rows.append({'path':rel,'bytes':p.stat().st_size if p.exists() else None,'source_sha256':expected,'local_sha256':actual,'match':actual==expected})
(out/'download_integrity_latest.json').write_text(json.dumps(rows,indent=2))
print(json.dumps({'expected':len(rows),'matched':sum(r['match'] for r in rows),'bytes':sum(r['bytes'] or 0 for r in rows),'unmatched':[r['path'] for r in rows if not r['match']]},indent=2))
