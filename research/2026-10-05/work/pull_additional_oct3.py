from pathlib import Path
import subprocess,concurrent.futures,hashlib,json
ROOT=Path(__file__).resolve().parent.parent; out=ROOT/'outputs/drive_analysis_20261003';dest=ROOT/'work/drive_logs_20261003'
s=(out/'additional_source_hashes.txt').read_text()
rows=[]
for line in s.splitlines():
 h,p=line.split(None,1);rel=p.split('/realdata/')[1];rows.append((h,p,rel))
def get(row):
 h,p,rel=row;local=dest/rel;local.parent.mkdir(parents=True,exist_ok=True)
 old=ROOT/'work/drive_logs_20261001'/rel
 if old.exists() and hashlib.sha256(old.read_bytes()).hexdigest()==h:
  import shutil;shutil.copy2(old,local)
 else:
  for attempt in range(3):
   r=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=10','comma@192.168.35.12:'+p,str(local)])
   if r.returncode==0 and hashlib.sha256(local.read_bytes()).hexdigest()==h:break
 return {'path':rel,'bytes':local.stat().st_size if local.exists() else 0,'match':local.exists() and hashlib.sha256(local.read_bytes()).hexdigest()==h}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
 for r in ex.map(get,rows):
  results.append(r)
  if len(results)%10==0:print('verified',len(results),'of',len(rows),flush=True)
(out/'additional_integrity.json').write_text(json.dumps(results,indent=2));print('DONE',len(results),'matched',sum(x['match'] for x in results),flush=True)
