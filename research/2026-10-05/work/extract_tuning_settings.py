import capnp,zstandard,json
from pathlib import Path
S=Path('work/drive_schema');schema=capnp.load(str(S/'log.capnp'),imports=[str(S)])
rows=[]
for route in ['00000023--b5e1d64a14','00000024--7d54f74e8e','00000028--c139047a03']:
 params={};delay=[];versions=set()
 for f in sorted(Path('work/drive_logs_20261004').glob(route+'--*/rlog.zst')):
  with f.open('rb') as h:data=zstandard.ZstdDecompressor().stream_reader(h).read()
  for e in schema.Event.read_multiple_bytes(data):
   k=e.which()
   if k=='initData':
    for ent in e.initData.params.entries:
     if any(s in ent.key for s in ['Torque','Lateral','Neural','Jerk','Steer','Delay']):
      try:params[ent.key]=bytes(ent.value).decode('utf-8')
      except UnicodeDecodeError:pass
   elif k=='lateralDelay':
    d=e.lateralDelay;delay.append([d.lateralDelay,d.lateralDelayEstimate,d.lateralDelayEstimateStd,str(d.status),d.validBlocks])
   elif k=='controlsState' and e.controlsState.lateralControlState.which()=='torqueState':versions.add(e.controlsState.lateralControlState.torqueState.version)
 rows.append(dict(route=route,parameters=params,torque_versions=list(versions),delay_count=len(delay),delay_first=delay[:1],delay_last=delay[-1:]))
Path('outputs/tuning_oscillation_review/settings.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
