from pathlib import Path
import numpy as np,json,collections
P=Path('outputs/drive_analysis_today')
def dt(t):
 x=np.diff(t,append=t[-1]+.01);return np.where((x>0)&(x<=.05),x,0)
def align(a,t):
 i=np.clip(np.searchsorted(a[:,0],t,side='right')-1,0,len(a)-1);return a[i],(t>=a[i,0])&(t-a[i,0]<.1)
def stats(q,w,m):
 if not m.any():return {'seconds':0}
 q=q.copy();q[:,3]=q[:,7]-q[:,6]
 return dict(seconds=float(w[m].sum()),mae=float(np.average(abs(q[m,3]),weights=w[m])),rms=float(np.sqrt(np.average(q[m,3]**2,weights=w[m]))),p95=float(np.percentile(abs(q[m,3]),95)),near_limit_pct=float(np.average(abs(q[m,4])>=.95,weights=w[m])*100),saturated_pct=float(np.average(q[m,5],weights=w[m])*100))
rows=[];pool=[]
for f in sorted(P.glob('000*.npz')):
 
 if '.qualified.' in f.name:continue
 a=np.load(f);c=a['cs'];cc=a['cc'];w=dt(c[:,0]);cw=dt(cc[:,0]);r={'route':f.stem,'recorded_seconds':float(w.sum()),'active_seconds':float(cw[cc[:,2]>0].sum()),'max_mph':float(c[:,2].max()*2.236936),'temporary_moving_seconds':float(w[(c[:,2]>=10)&(c[:,6]>0)].sum()),'permanent_moving_seconds':float(w[(c[:,2]>=10)&(c[:,7]>0)].sum())}
 e=a['eps_status'];r['eps_status_counts']={str(int(k)):int(v) for k,v in zip(*np.unique(e[:,1],return_counts=True))}
 if 'torque' in a:
  q=a['torque'];t=q[:,0];cs,fc=align(c,t);ctrl,ff=align(cc,t);w=dt(t);active=(q[:,2]>0)&(ctrl[:,2]>0)&fc&ff;starts=np.where(active&~np.r_[False,active[:-1]],t,-np.inf)
  m=active&(t-np.maximum.accumulate(starts)>=2)&(cs[:,2]>=10)&(cs[:,4]==0)&(cs[:,6]==0)&(cs[:,7]==0)&(cs[:,8]>0)&(cs[:,1]>0)&(q[:,1]>0)&(ctrl[:,1]>0)&(w>0)
  r['qualified']=stats(q,w,m);r['speed_bins']={str(lo)+'-'+str(hi):stats(q,w,m&(cs[:,2]*2.236936>=lo)&(cs[:,2]*2.236936<hi)) for lo,hi in [(22,35),(35,45),(45,55),(55,65),(65,100)]};r['driver_override_active_seconds']=float(w[active&(cs[:,4]>0)].sum());pool.append((q,w,m))
  np.savez_compressed(P/(f.stem+'.qualified.npz'),t=t,torque=q,mask=m,speed=cs[:,2])
 else:r['qualified']={'seconds':0}
 if 'est' in a:
  z=a['est'];r['estimator']={'messages':len(z),'valid_messages':int((z[:,2]>0).sum()),'calibration_percent_min_max':np.percentile(z[:,4],[0,100]).tolist(),'last':dict(zip(['event_valid','valid','useParams','calPerc','points','factor','offset','friction'],z[-1,1:].tolist())),'filtered_min_max':{name:np.percentile(z[:,i],[0,100]).tolist() for name,i in [('factor',6),('offset',7),('friction',8)]}}
 rows.append(r)
q=np.concatenate([x[0] for x in pool]);w=np.concatenate([x[1] for x in pool]);m=np.concatenate([x[2] for x in pool]);res={'routes':rows,'aggregate':stats(q,w,m),'below_limit':stats(q,w,m&(abs(q[:,4])<.95)),'near_limit':stats(q,w,m&(abs(q[:,4])>=.95))};(P/'torque_metrics.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
