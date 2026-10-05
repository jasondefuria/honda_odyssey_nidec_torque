from pathlib import Path
import numpy as np,json,os
os.environ['MPLCONFIGDIR']='/tmp/tor-matplotlib'
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path('outputs/friction_error_review');O.mkdir(exist_ok=True)
a=np.load('outputs/feedforward_replay/replay.npz');raw=np.load('outputs/drive_analysis_today/00000028--c139047a03.npz');q=raw['torque'];t=a['t'];m=a['window'];e=raw['est'];idx=np.clip(np.searchsorted(e[:,0],q[:,0],side='right')-1,0,len(e)-1);fr=e[idx,8];factor=e[idx,6];err=a['desired']-a['actual'];j=a['lookahead_jerk'];grid=np.arange(t[m][0],t[m][-1],.02)
def rms(y):
 x=np.interp(grid,t[m],y[m]);x-=np.polyval(np.polyfit(grid-grid[0],x,1),grid-grid[0]);f=np.fft.rfftfreq(len(x),.02);z=np.fft.rfft(x);return float(np.std(np.fft.irfft(z*((f>=.3)&(f<=2)),n=len(x))))
base=np.clip((err+.4*j)/.2,-1,1)*fr;rows=[];series={}
for gain in [1.,.85,.7,.5,0.]:
 comp=np.clip((gain*err+.4*j)/.2,-1,1)*fr;delta=comp-base
 # Preserve original logged command; alter only its friction compensation contribution.
 hypothetical=q[:,4]-delta;series[gain]=hypothetical
 rows.append({'error_multiplier':gain,'compensation_band_rms':rms(comp),'hypothetical_command_band_rms':rms(hypothetical),'max_abs_command_change':float(abs(delta[m]).max()),'mean_abs_command_change':float(abs(delta[m]).mean()),'command_change_rms':float(np.sqrt(np.mean(delta[m]**2))),'saturation_fraction':float(np.mean(abs(comp[m])>=fr[m]-1e-6))})
sel=m&(abs(q[:,3])>.005);kp=q[sel,8]/q[sel,3];slope=fr[m]/.2;kpacc=kp/factor[sel]
r={'scope':'429.65–439.65 seconds in route 28. Frozen-trajectory sensitivity, not closed-loop simulation; preserves logged command residual and all non-friction terms. No firmware, configuration or repository changes.','window_samples':int(m.sum()),'learned_friction_range':np.percentile(fr[m],[0,100]).tolist(),'friction_local_slope_per_mps2':np.percentile(slope,[0,50,100]).tolist(),'P_gain_torque_error_p5_median_p95':np.percentile(kp,[5,50,95]).tolist(),'P_effective_slope_per_mps2_p5_median_p95':np.percentile(kpacc,[5,50,95]).tolist(),'error_range_mps2':np.percentile(err[m],[0,100]).tolist(),'jerk_zero_samples':int((m&(j==0)).sum()),'variants':rows}
(O/'sensitivity.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
fig,axs=plt.subplots(2,1,figsize=(12,7),sharex=True)
for g in [1.,.7,.5]:axs[0].plot(t[m],series[g][m],label=f'Error multiplier {g:g}')
axs[0].set_ylabel('Normalized steering command');axs[0].set_title('Fixed recorded trajectory: command sensitivity only')
axs[1].plot(t[m],err[m],label='Recorded acceleration error');axs[1].plot(t[m],base[m],label='Original friction compensation');axs[1].set_ylabel('m/s² or normalized compensation');axs[1].set_xlabel('Seconds from first carState')
for ax in axs:ax.legend();ax.grid(alpha=.3)
fig.tight_layout();fig.savefig(O/'friction_sensitivity.png',dpi=140)
