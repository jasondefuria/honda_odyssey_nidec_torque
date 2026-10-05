from pathlib import Path
import numpy as np,json,os
os.environ['MPLCONFIGDIR']='/tmp/tor-matplotlib'
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path('outputs/drive_analysis_today');O=Path('outputs/tuning_oscillation_review');rows=[]
for route in ['00000023--b5e1d64a14','00000024--7d54f74e8e','00000028--c139047a03']:
 a=np.load(P/(route+'.npz'));q=a['torque'];c=a['cs'];qual=np.load(P/(route+'.qualified.npz'));t=q[:,0];valid=qual['mask'];origin=c[0,0]
 for start in np.arange(t[0],t[-1]-10,5):
  ix=np.where((t>=start)&(t<start+10))[0]
  if len(ix)<900 or not valid[ix].all() or np.max(np.diff(t[ix]))>.05:continue
  grid=np.arange(start+.02,start+9.98,.02);actual=np.interp(grid,t,q[:,6]);desired=np.interp(grid,t,q[:,7]);err=desired-actual;out=np.interp(grid,t,q[:,4]);angle=np.interp(grid,c[:,0],c[:,3]);speed=np.interp(grid,c[:,0],c[:,2])*2.236936
  def band(x):
   y=x-np.polyval(np.polyfit(grid-grid[0],x,1),grid-grid[0]);f=np.fft.rfftfreq(len(y),.02);z=np.fft.rfft(y);mask=(f>=.3)&(f<=2);filtered=np.fft.irfft(z*mask,n=len(y));power=abs(z)**2;k=np.where(mask)[0][np.argmax(power[mask])];return float(np.std(filtered)),float(f[k])
  er,f=band(err);ac,_=band(actual);de,_=band(desired);ou,_=band(out)
  rows.append(dict(route=route,start_seconds=float(start-origin),mean_mph=float(speed.mean()),error_band_rms=er,actual_band_rms=ac,desired_band_rms=de,command_band_rms=ou,peak_error_frequency_hz=f,angle_peak_to_peak=float(np.ptp(angle)),error_peak_to_peak=float(np.ptp(err)),max_abs_command=float(abs(out).max())))
rows.sort(key=lambda r:r['error_band_rms'],reverse=True)
(O/'windows.json').write_text(json.dumps(rows,indent=2));print('windows',len(rows));print(json.dumps(rows[:8],indent=2))
latest=[r for r in rows if r['route'].startswith('00000028')];top=latest[:3]
fig,axes=plt.subplots(len(top),2,figsize=(12,3*len(top)),squeeze=False)
for ax,r in zip(axes,top):
 a=np.load(P/(r['route']+'.npz'));q=a['torque'];c=a['cs'];t=q[:,0]-c[0,0];m=(t>=r['start_seconds'])&(t<r['start_seconds']+10)
 ax[0].plot(t[m],q[m,7],label='Desired');ax[0].plot(t[m],q[m,6],label='Actual');ax[0].set_ylabel('Lateral acceleration m/s²');ax[0].legend();ax[0].set_title(f'{r["mean_mph"]:.1f} mph, error-band RMS {r["error_band_rms"]:.3f}')
 ax[1].plot(t[m],q[m,4],label='Normalized torque command');ax[1].plot(t[m],q[m,8],label='P term');ax[1].plot(t[m],q[m,9],label='I term');ax[1].legend();ax[1].set_title('Terms use different units; shape comparison only')
 for x in ax:x.grid(alpha=.3);x.set_xlabel('Seconds from first carState')
fig.tight_layout();fig.savefig(O/'largest_latest_windows.png',dpi=140)
