from pathlib import Path
import capnp,zstandard,json,collections
P=Path('work/drive_schema').resolve();s=capnp.load(str(P/'log.capnp'),imports=[str(P)])
counts=collections.Counter();status=collections.Counter();alerts=collections.Counter();samples=[];errors=[];eps=[];start=None;fault_start=None;first_active=None;lastflags=None;changes=[]
for f in sorted(Path('work/eps_fault_logs').glob('*/rlog.zst')):
 try:
  with f.open('rb') as fh:data=zstandard.ZstdDecompressor().stream_reader(fh).read()
  for e in s.Event.read_multiple_bytes(data):
   t=e.logMonoTime/1e9
   if start is None:start=t
   k=e.which();counts[k]+=1
   if k=='carParams':
    for x in e.carParams.carFw:
     if str(x.ecu)=='eps':eps.append(bytes(x.fwVersion).decode('ascii','replace').rstrip('\0'))
   elif k=='can':
    for x in e.can:
     if x.address==399 and x.src==0 and len(x.dat)==7:status[x.dat[4]>>4]+=1
   elif k=='carState':
    c=e.carState;flags=(bool(c.steerFaultTemporary),bool(c.steerFaultPermanent),bool(c.canValid))
    if flags!=lastflags:changes.append({'seconds':t-start,'temporary':flags[0],'permanent':flags[1],'canValid':flags[2],'speed_mph':c.vEgo*2.236936});lastflags=flags
    samples.append([t,float(c.vEgo),int(c.steerFaultTemporary),int(c.steerFaultPermanent),int(c.canValid),int(c.steeringPressed)])
   elif k=='carControl':
    if e.carControl.latActive and first_active is None:first_active=t-start
   elif k in ('selfdriveState','controlsState'):
    z=getattr(e,k).to_dict()
    for key in ['alertText1','alertText2','alertType']:
     if z.get(key):alerts[key+': '+str(z[key])]+=1
 except Exception as ex:errors.append({'file':str(f),'error':str(ex)})
import numpy as np
a=np.array(samples);dt=np.diff(a[:,0],append=a[-1,0]+.01);dt=np.where((dt>0)&(dt<.1),dt,0)
r={'eps_identities':sorted(set(eps)),'counts':dict(counts),'raw_eps_status_counts':dict(status),'alerts':dict(alerts),'first_active_seconds':first_active,'carState_seconds':float(dt.sum()),'max_mph':float(a[:,1].max()*2.236936),'temporary_fault_seconds':float(dt[a[:,2]>0].sum()),'permanent_fault_seconds':float(dt[a[:,3]>0].sum()),'transitions':changes,'parse_errors':errors};Path('outputs/eps_fault_review/summary.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
