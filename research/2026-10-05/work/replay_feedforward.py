from pathlib import Path
import json,capnp,zstandard,numpy as np
R=Path.cwd();O=R/'outputs/feedforward_replay';O.mkdir(exist_ok=True);S=R/'work/drive_schema';schema=capnp.load(str(S/'log.capnp'),imports=[str(S)])
route='00000028--c139047a03';a=np.load(R/'outputs/drive_analysis_today'/f'{route}.npz');q=a['torque'];cs=a['cs'];lp=a['lp'];est=a['est'];models=[]
for f in sorted((R/'work/drive_logs_20261004').glob(route+'--*/rlog.zst'),key=lambda p:int(p.parent.name.rsplit('--',1)[1])):
 with f.open('rb') as h:data=zstandard.ZstdDecompressor().stream_reader(h).read()
 for e in schema.Event.read_multiple_bytes(data):
  if e.which()=='modelV2' and len(e.modelV2.acceleration.y)==33:
   models.append([e.logMonoTime/1e9,int(len(e.modelV2.orientation.x)>=17),*e.modelV2.acceleration.y])
models=np.array(models);t=q[:,0]
def align(x):
 i=np.clip(np.searchsorted(x[:,0],t,side='right')-1,0,len(x)-1);return x[i],t-x[i,0]
c,ca=align(cs);l,la=align(lp);e,ea=align(est);mo,ma=align(models)
T=10*(np.arange(33)/32)**2;delta=.29064884781837463;factor=.7;jerks=[];factors=[]
for i in range(len(t)):
 j=0
 if q[i,2] and mo[i,1]:
  pred=np.diff(mo[i,2:])/np.diff(T);upper=next((n for n,v in enumerate(T) if v>np.interp(c[i,2],[9,30],[1.4,2])),16)
  current=(np.interp(delta,T,mo[i,2:])-q[i,7])/delta;vals=pred[5:upper]
  if len(vals) and np.all(np.sign(vals)==np.sign(current)):j=np.sign(current)*min(abs(current),min(abs(vals)))
  if j==0:factor=1.
 jerks.append(j);factors.append(factor)
jerks=np.array(jerks);factors=np.array(factors);err=q[:,7]-q[:,6]
nom=(q[:,7]-l[:,6]*9.81)/e[:,6]
# The saturation is nonlinear: jerk contribution is the marginal change with jerk on.
friction_without_jerk=np.clip(factors*err/0.2,-1,1)*e[:,8]
combined_friction=np.clip((factors*err+.4*jerks)/.2,-1,1)*e[:,8]
jerk_increment=combined_friction-friction_without_jerk
replayed=nom+combined_friction
valid=(q[:,1]>0)&(q[:,2]>0)&(ca>=0)&(ca<.1)&(la>=0)&(la<.1)&(ea>=0)&(ea<.5)&(ma>=0)&(ma<.15)
local=t-cs[0,0];window=valid&(local>=429.65)&(local<439.65)
def summary(mask):
 residual=replayed[mask]-q[mask,10]
 return {'samples':int(mask.sum()),'residual_mae':float(np.mean(abs(residual))),'residual_p95':float(np.percentile(abs(residual),95)),'residual_max':float(max(abs(residual))),'jerk_nonzero_pct':float(np.mean(jerks[mask]!=0)*100),'friction_saturated_pct':float(np.mean(abs(combined_friction[mask])>=e[mask,8]-.000001)*100),'accel_friction_factor_unique':np.unique(factors[mask]).tolist()}
r={'method':'Formula replay using causal latest published modelV2, vehicleParameters, carState and torque estimator messages; exact source revision 580e0fe and opendbc 1fe4521. Not bit-exact process scheduling replay.','all_active':summary(valid),'target_window':summary(window)}
np.savez_compressed(O/'replay.npz',t=local,window=window,valid=valid,nominal=nom,friction_without_jerk=friction_without_jerk,jerk_increment=jerk_increment,replayed=replayed,logged=q[:,10],lookahead_jerk=jerks,friction_factor=factors,desired=q[:,7],actual=q[:,6],model_age=ma)
(O/'summary.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
