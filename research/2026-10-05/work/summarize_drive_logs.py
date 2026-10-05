import pathlib,json,csv
import numpy as np
P=pathlib.Path(__file__).resolve().parent.parent/'outputs/drive_analysis_20260930'
def align(a,t):
 ix=np.searchsorted(a[:,0],t,side='right')-1; ix=np.clip(ix,0,len(a)-1)
 return a[ix],(t>=a[ix,0])&(t-a[ix,0]<.1)
def stats(p,cs,dt,m):
 if not m.any():return {'seconds':0}
 err=p[m,5];out=p[m,6];w=dt[m]
 return dict(seconds=float(w.sum()),samples=int(m.sum()),rms_angle_error_deg=float(np.sqrt(np.average(err**2,weights=w))),mean_abs_angle_error_deg=float(np.average(abs(err),weights=w)),p95_abs_angle_error_deg=float(np.percentile(abs(err),95)),mean_signed_error_deg=float(np.average(err,weights=w)),near_limit_percent=float(np.average(abs(out)>=.95,weights=w)*100),pid_saturated_percent=float(np.average(p[m,7],weights=w)*100),speed_mph_median=float(np.median(cs[m,2])*2.236936),output_abs_p95=float(np.percentile(abs(out),95)))
allrows=[]; collected=[]
for f in sorted(P.glob('*.npz')):
 a=np.load(f)
 if not all(k in a for k in ['pid','cs','cc']):continue
 p=a['pid']; t=p[:,0]; cs,fresh=align(a['cs'],t); cc,fr=align(a['cc'],t)
 dt=np.diff(t,append=t[-1]+.01);dt=np.where((dt>0)&(dt<=.05),dt,0)
 active=(p[:,2]>0)&(cc[:,2]>0)&fresh&fr
 # Exclude first two seconds after lateral activation, even if speed filter changes later.
 starts=np.where(active&~np.r_[False,active[:-1]],t,-np.inf);since=t-np.maximum.accumulate(starts)
 eligible=active&(since>=2)&(p[:,1]>0)&(cs[:,1]>0)&(cc[:,1]>0)&(cs[:,8]>0)&(cs[:,2]>=10)&(cs[:,4]==0)&(cs[:,6]==0)&(cs[:,7]==0)&(dt>0)
 moving=(cs[:,2]>=10)&(dt>0)&fresh
 row={'route':f.stem,'recorded_seconds':float(dt.sum()),'lateral_active_seconds':float(dt[active].sum()),'driver_override_active_seconds':float(dt[active&(cs[:,4]>0)].sum()),'temporary_fault_moving_seconds':float(dt[moving&(cs[:,6]>0)].sum()),'permanent_fault_moving_seconds':float(dt[moving&(cs[:,7]>0)].sum()),'qualified':stats(p,cs,dt,eligible)}
 
 if 'co' in a and eligible.any():
  co,fc=align(a['co'],t);sel=eligible&fc
  row['controller_output']={'near_limit_percent':float(np.average(abs(co[sel,2])>=.95,weights=dt[sel])*100),'request_difference_gt_005_percent':float(np.average(abs(co[sel,2]-cc[sel,3])>.05,weights=dt[sel])*100)}
 if 'lp' in a and eligible.any():
  lp,fl=align(a['lp'],t);sel=eligible&fl&(lp[:,2]>0)
  row['learned_parameters']={name:np.percentile(lp[sel,col],[5,50,95]).tolist() for name,col in [('steer_ratio',3),('stiffness_factor',4),('angle_offset_deg',5)]} if sel.any() else {}
 allrows.append(row);collected.append((p,cs,dt,eligible))
p=np.concatenate([v[0] for v in collected]);cs=np.concatenate([v[1] for v in collected]);dt=np.concatenate([v[2] for v in collected]);m=np.concatenate([v[3] for v in collected])
speed=[]
for lo,hi in [(22,35),(35,45),(45,55),(55,65),(65,100)]:
 sel=m&(cs[:,2]*2.236936>=lo)&(cs[:,2]*2.236936<hi);speed.append({'mph':f'{lo}-{hi}',**stats(p,cs,dt,sel)})
result={'routes':allrows,'aggregate':stats(p,cs,dt,m),'speed_bins':speed,'unsaturated':stats(p,cs,dt,m&(abs(p[:,6])<.95)),'near_limit':stats(p,cs,dt,m&(abs(p[:,6])>=.95))}
(P/'metrics.json').write_text(json.dumps(result,indent=2))
with open(P/'route_metrics.csv','w') as fh:
 rows=[{k:v for k,v in r.items() if k!='qualified'}|r['qualified'] for r in allrows];w=csv.DictWriter(fh,fieldnames=sorted(set().union(*(r.keys() for r in rows))));w.writeheader();w.writerows(rows)
print(json.dumps(result,indent=2))
