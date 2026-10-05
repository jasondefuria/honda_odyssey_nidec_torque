from pathlib import Path
import subprocess,concurrent.futures,hashlib,json
ROOT=Path(__file__).resolve().parent.parent; out=ROOT/'outputs/drive_analysis_20261003';dest=ROOT/'work/drive_logs_20261003'
cmd="find /data/media/0/realdata -name rlog.zst -path '/data/media/0/realdata/0000000*' -exec sha256sum {} +"
s=subprocess.check_output(['ssh','-o','BatchMode=yes','comma@192.168.35.12',cmd],text=True)
rows=[]
for line in s.splitlines():
 h,p=line.split(None,1);rel=p.split('/realdata/')[1];route=rel.split('/')[0].rsplit('--',1)[0]
 if route>='00000005':rows.append((h,p,rel))
(out/'earlier_source_hashes.txt').write_text('\n'.join(h+'  '+p for h,p,r in rows)+'\n')
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
(out/'earlier_integrity.json').write_text(json.dumps(results,indent=2));print('DONE',len(results),'matched',sum(x['match'] for x in results),flush=True)
