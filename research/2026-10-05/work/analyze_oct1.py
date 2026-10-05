import pathlib,json,capnp,zstandard,sys,collections,time,hashlib
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent
SC=ROOT/'drive_schema'; schema=capnp.load(str(SC/'log.capnp'),imports=[str(SC)])
LOG=ROOT/'drive_logs_20261001'; OUT=ROOT.parent/'outputs/drive_analysis_20261001'
def events(f):
 with open(f,'rb') as fh:
  data=zstandard.ZstdDecompressor().stream_reader(fh).read()
 yield from schema.Event.read_multiple_bytes(data)
def clean(x):
 if isinstance(x,bytes):return x.decode('ascii','replace').rstrip('\0')
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 if isinstance(x,list):return [clean(v) for v in x]
 return x
if '--inventory' in sys.argv:
 inv=[]
 for f in sorted(LOG.glob('*--0/rlog.zst')):
  d={'route':f.parent.name.rsplit('--',1)[0]}
  for e in events(f):
   k=e.which()
   if k=='initData':
    z=e.initData.to_dict();d['software']={k:z.get(k) for k in ['gitCommit','gitBranch','version','wallTimeNanos']}
   if k=='carParams':
    z=clean(e.carParams.to_dict());d['params']={k:z.get(k) for k in ['carFingerprint','lateralTuning','lateralParams','steerActuatorDelay','steerLimitTimer','flags']};d['eps']=[v['fwVersion'] for v in z['carFw'] if v['ecu']=='eps'];break
  inv.append(d)
 (OUT/'inventory.json').write_text(json.dumps(inv,indent=2));print(json.dumps(inv,indent=2));sys.exit()
# Keep event streams separately and align causally with a freshness limit.
for directory in sorted(LOG.glob('*--0')):
 route=directory.name.rsplit('--',1)[0]; dest=OUT/(route+'.npz')
 if dest.exists() and '--force' not in sys.argv:continue
 streams=collections.defaultdict(list); errors=[]; metadata=[]; files=sorted(LOG.glob(route+'--*/rlog.zst'),key=lambda f:int(f.parent.name.rsplit('--',1)[1]))
 for f in files:
  try:
   for e in events(f):
    k=e.which();t=e.logMonoTime/1e9
    if k=='can':
     for frame in e.can:
      if frame.address==399 and frame.src==0 and len(frame.dat)==7:
       streams['eps_status'].append([t,frame.dat[4]>>4])
    elif k=='carState':
     s=e.carState;streams['cs'].append([t,e.valid,s.vEgo,s.steeringAngleDeg,s.steeringPressed,s.steeringTorque,s.steerFaultTemporary,s.steerFaultPermanent,s.canValid,s.steeringRateDeg])
    elif k=='carControl':
     s=e.carControl;streams['cc'].append([t,e.valid,s.latActive,s.actuators.torque])
    elif k=='carOutput':
     s=e.carOutput.actuatorsOutput;streams['co'].append([t,e.valid,s.torque,s.torqueOutputCan])
    elif k in ['carParams','carParamsSP']:
     z=clean(getattr(e,k).to_dict())
     if k=='carParams':z={x:z.get(x) for x in ['carFingerprint','carFw','lateralTuning','lateralParams','steerActuatorDelay']}
     if not any(x['kind']==k and x['value']==z for x in metadata):metadata.append({'kind':k,'value':z})
    elif k=='controlsState':
     s=e.controlsState
     if s.lateralControlState.which()=='pidState':
      p=s.lateralControlState.pidState;streams['pid'].append([t,e.valid,p.active,p.steeringAngleDeg,p.steeringAngleDesiredDeg,p.angleError,p.output,p.saturated,p.p,p.i,p.f,s.curvature,s.desiredCurvature])
    elif k=='vehicleParameters':
     s=e.vehicleParameters; streams['lp'].append([t,e.valid,s.valid,s.steerRatio,s.stiffnessFactor,s.angleOffsetDeg,s.roll])
  except Exception as ex:errors.append({'file':str(f),'error':str(ex)})
 np.savez_compressed(dest,**{k:np.array(v) for k,v in streams.items()})
 (OUT/(route+'.parse.json')).write_text(json.dumps({'files':len(files),'counts':{k:len(v) for k,v in streams.items()},'errors':errors,'metadata':metadata},indent=2))
 print(route,len(files),{k:len(v) for k,v in streams.items()},errors,flush=True)
