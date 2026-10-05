from pathlib import Path
import json,zstandard,collections
P=Path('outputs/drive_analysis_20261003');D=Path('work/drive_logs_20261003');a=json.loads((P/'latest_integrity.json').read_text())+json.loads((P/'earlier_integrity.json').read_text())+json.loads((P/'additional_integrity.json').read_text());routes=collections.defaultdict(lambda:{'segments':[],'bytes':0});errors=[]
for r in a:
 f=D/r['path'];route=f.parent.name.rsplit('--',1)[0];routes[route]['segments'].append(int(f.parent.name.rsplit('--',1)[1]));routes[route]['bytes']+=f.stat().st_size
 try:
  with f.open('rb') as fh,zstandard.ZstdDecompressor().stream_reader(fh) as z:
   while z.read(1024*1024):pass
 except Exception as ex:errors.append({'path':r['path'],'error':str(ex)})
for v in routes.values():
 v['segments'].sort();v['contiguous_from_zero']=v['segments']==list(range(max(v['segments'])+1));v['count']=len(v['segments'])
s={'files':len(a),'hash_matches':sum(x['match'] for x in a),'bytes':sum(x['bytes'] for x in a),'compression_errors':errors,'routes':dict(sorted(routes.items()))};(P/'collection_manifest.json').write_text(json.dumps(s,indent=2));print(json.dumps({k:v for k,v in s.items() if k!='routes'},indent=2));print([(k,v['count'],v['contiguous_from_zero']) for k,v in s['routes'].items()])
