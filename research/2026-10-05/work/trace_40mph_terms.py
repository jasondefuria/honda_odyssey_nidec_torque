from pathlib import Path
import json,numpy as np,os
os.environ['MPLCONFIGDIR']='/tmp/tor-matplotlib'
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path('outputs/tuning_oscillation_review');a=np.load('outputs/drive_analysis_today/00000028--c139047a03.npz');q=a['torque'];t=q[:,0]-a['cs'][0,0];start=429.65;end=439.65;m=(t>=start)&(t<end);grid=np.arange(start+.02,end-.02,.02)
series={name:np.interp(grid,t,q[:,col]) for name,col in [('command',4),('P',8),('I',9),('feedforward',10),('desired',7),('actual',6)]}
def filtered(x):
 z=x-np.polyval(np.polyfit(grid-grid[0],x,1),grid-grid[0]);f=np.fft.rfftfreq(len(z),.02);spec=np.fft.rfft(z);mask=(f>=.3)&(f<=2);return np.fft.irfft(spec*mask,n=len(z))
band={k:filtered(v) for k,v in series.items()};r={'window_seconds':[start,end],'effective_delay_s':0.29064884781837463,'live_delay_toggle':True,'smoothing_delay_s':0,'command_equation':'output = -(P + I + feedforward), D=0 in this controller','max_equation_residual':float(abs(q[m,4]+q[m,8]+q[m,9]+q[m,10]).max()),'band_rms_0p3_to_2Hz':{k:float(np.std(v)) for k,v in band.items()},'raw_ranges':{k:[float(v.min()),float(v.max())] for k,v in series.items()},'correlation_with_command':{k:float(np.corrcoef(-band[k],band['command'])[0,1]) for k in ['P','I','feedforward']}}
(O/'40mph_terms.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
fig,axs=plt.subplots(3,1,figsize=(12,9),sharex=True)
for k in ['desired','actual']:axs[0].plot(grid,series[k],label=k)
axs[0].set_ylabel('Lateral acceleration m/s²')
for k in ['P','I','feedforward']:axs[1].plot(grid,-series[k],label='−'+k)
axs[1].plot(grid,series['command'],'k',label='Final command',alpha=.7);axs[1].set_ylabel('Normalized command contributions')
for k in ['P','I','feedforward']:axs[2].plot(grid,-band[k],label='−'+k)
axs[2].set_ylabel('0.3–2 Hz filtered contributions');axs[2].set_xlabel('Seconds from first carState')
for ax in axs:ax.legend();ax.grid(alpha=.3)
fig.suptitle('40 mph correction window — logged terms, not causal proof');fig.tight_layout();fig.savefig(O/'40mph_decomposition.png',dpi=140)
