from pathlib import Path
import capnp,zstandard,numpy as np,json,collections
R=Path(__file__).resolve().parent;O=R.parent/'outputs/drive_analysis_20261001_route05_partial';sc=capnp.load(str(R/'drive_schema/log.capnp'),imports=[str(R/'drive_schema')]);f=R/'drive_logs_20261001/00000005--446af71a85--0/rlog.zst'
with f.open('rb') as fh: data=zstandard.ZstdDecompressor().stream_reader(fh).read()
torque=[];kinds=collections.Counter(); estimates=[];times=[]
for e in sc.Event.read_multiple_bytes(data):
 k=e.which();t=e.logMonoTime/1e9;times.append(t)
 if k=='controlsState':
  s=e.controlsState.lateralControlState;kind=s.which();kinds[kind]+=1
  if kind=='torqueState':
   z=s.torqueState;torque.append([t,e.valid,z.active,z.error,z.output,z.saturated,z.actualLateralAccel,z.desiredLateralAccel])
 if k=='lateralTorqueParameters':
  d=e.lateralTorqueParameters.to_dict();d.pop('points',None);estimates.append(d)
a=np.load(O/'00000005--446af71a85.npz');c=a['cs'];cc=a['cc'];q=np.array(torque)
def dur(t):
 d=np.diff(t,append=t[-1]+.01);return np.where((d>0)&(d<=.05),d,0)
def align(z,t):
 i=np.clip(np.searchsorted(z[:,0],t,side='right')-1,0,len(z)-1);return z[i],(t>=z[i,0])&(t-z[i,0]<.1)
s={'event_span_seconds':max(times)-min(times),'controller_types':dict(kinds),'speed_mph_min_median_max':(np.percentile(c[:,2],[0,50,100])*2.236936).tolist(),'lat_active_seconds':float(dur(cc[:,0])[cc[:,2]>0].sum()),'temporary_fault_seconds':float(dur(c[:,0])[c[:,6]>0].sum()),'permanent_fault_seconds':float(dur(c[:,0])[c[:,7]>0].sum()),'estimator_first':estimates[0] if estimates else None,'estimator_last':estimates[-1] if estimates else None}
if len(q):
 cs,fc=align(c,q[:,0]);ctrl,ff=align(cc,q[:,0]);dt=dur(q[:,0]);active=(q[:,2]>0)&(ctrl[:,2]>0)&fc&ff;starts=np.where(active&~np.r_[False,active[:-1]],q[:,0],-np.inf);m=active&(q[:,0]-np.maximum.accumulate(starts)>=2)&(cs[:,2]>=10)&(cs[:,4]==0)&(cs[:,6]==0)&(cs[:,7]==0)&(cs[:,8]>0)&(cs[:,1]>0)&(q[:,1]>0)&(ctrl[:,1]>0)&(dt>0)
 s['torque_active_seconds']=float(dt[active].sum());s['qualified_seconds']=float(dt[m].sum())
 if m.any():s['qualified_metrics']={'mean_abs_lateral_accel_error':float(np.average(abs(q[m,3]),weights=dt[m])),'near_limit_percent':float(np.average(abs(q[m,4])>=.95,weights=dt[m])*100)}
np.savez_compressed(O/'torque_state.npz',torque=q)
(O/'segment_summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s,indent=2))
